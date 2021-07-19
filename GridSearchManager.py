"""
Dropped in from TempFlow. Removed the yaml config support.
"""

import copy
import datetime
import warnings
import re
import pydoc
from abc import abstractmethod, ABCMeta
from typing import Dict, List, Union, Any, Callable, Tuple, NamedTuple, Generator


class SearchConfiguration(NamedTuple):
    searchPoint: Dict[str, Any]
    config: Dict[str, Any]
    id: int


class AbstractSearchManager(metaclass=ABCMeta):

    def __init__(self):
        self.name = ''  # type: str
        self.description = ''  # type: str

    @abstractmethod
    def generate_configuration(self) -> Generator[SearchConfiguration, None, None]:
        """
        Generate all configuration combinations. Each configuration corresponds to a point in the parameter space.
        Return both a full configuration dict, as well as a dict with only the parameter axes.
        (The latter being useful for naming/reporting.)
        :return:
        """
        pass

    def get_configuration(self):
        """
        Return a list of full configs and a list of search points.
        I.e. packs the results from generate_configuration into two separate lists.
        :return:
        """
        configs, paramAxisValues = [], []
        for config, axes in self.generate_configuration():
            configs.append(config)
            paramAxisValues.append(axes)

        return configs, paramAxisValues

    class RunResult:
        """
        Represents a single execution result for some search point.
        Same point can generate multiple RunResult instances, if repetitions are used.
        """

        def __init__(self, returnedValue=None, paramValues=None, instance=0):
            paramValues = paramValues or {}
            self.returnedValue = returnedValue
            runMetrics = returnedValue[0] if isinstance(returnedValue, tuple) else returnedValue
            self.metrics = runMetrics  # type: Dict[str, Any]
            self.paramValues = paramValues
            self.instance = instance  # The repetition index for this search point.

    def run_search(self, targetFunc: Callable[[Dict, Dict, str], Union[Dict, Tuple]],
                   nameGenerator: Callable[[Dict], str] = None,
                   repeatNumber: int = 1):

        import numpy as np

        # Run the experiments.
        runResults = []  # type: List[AbstractSearchManager.RunResult]
        searchConfiguration = list(self.generate_configuration())
        for config, paramValues in searchConfiguration:
            # Perform several runs for each search point, if requested.
            for instanceIndex in range(repeatNumber):
                # Generate run names inside the loop, to generate current timestamps.
                if nameGenerator is None:
                    runName = datetime.datetime.now().strftime('%y%m%d-%H%M%S_')
                    runName += '_'.join(['{}-{}'.format(k, paramValues[k]) for k in sorted(paramValues.keys())])
                else:
                    runName = nameGenerator(paramValues)
                if repeatNumber > 1:
                    runName += '_instance-{}'.format(instanceIndex)

                returnedValues = targetFunc(config, paramValues, runName)
                runResults.append(AbstractSearchManager.RunResult(returnedValues, paramValues, instanceIndex))

        # For convenience, generate two different result formats.
        resultsAvg = []  # type: List[Dict]
        resultsFull = []  # type: List[Dict]

        allSearchPoints = [v[1] for v in searchConfiguration]

        # Aggregate the returned metrics, computing mean and std for each search point.
        for searchPoint in allSearchPoints:
            # Fetch all run results for a given search point.
            allRunResults = [r for r in runResults if searchPoint == r.paramValues]
            if len(allRunResults) == 1:
                # If only a single execution is performed, there's nothing to aggregate.
                assert repeatNumber == 1
                runResult = allRunResults[0]
                resultsAvg.append({**searchPoint, **runResult.metrics})
            else:
                # Compute mean and std if several executions were performed.
                assert repeatNumber > 1
                metricsAvg, metricsStd = {}, {}
                for metricName in allRunResults[0].metrics.keys():
                    allMetricValues = np.asarray([r.metrics[metricName] for r in allRunResults])
                    metricsAvg[metricName] = np.mean(allMetricValues)
                    metricsStd[metricName + '-std'] = np.std(allMetricValues)

                resultsAvg.append({**searchPoint, **metricsAvg})
                resultsFull.append({**searchPoint, **metricsAvg, **metricsStd})

        if repeatNumber == 1:
            # We can't compute std from a single run, but at least return the averages.
            resultsFull = resultsAvg

        return runResults, resultsAvg, resultsFull

    @classmethod
    def _decode_python_types_recursive(cls, rawValue):
        """
        Given a JSON/YAML-object (output of json.load or yaml.load), traverses it and converts
        string values of form '__type(value)' to Python objects of type ' type'.
        """
        from collections import OrderedDict

        if isinstance(rawValue, str):
            if rawValue[:2] == '__':
                match = re.match(r'__(\w+)\((.*)\)\s*', rawValue)
                if match:
                    typeName = match.group(1)
                    valueString = match.group(2)  # type: str
                    if typeName in ['tuple', 'list']:
                        valueString = [int(s.strip()) for s in valueString.split(',')]  # We only support int tuples.
                    if typeName == 'slice':
                        return slice(*(int(s.strip()) for s in valueString.split(',')))
                    typeObject = pydoc.locate(typeName)

                    return typeObject(valueString)
            return rawValue
        elif isinstance(rawValue, list):
            return [cls._decode_python_types_recursive(v) for v in rawValue]
        elif isinstance(rawValue, dict) or isinstance(rawValue, OrderedDict):
            return {k: cls._decode_python_types_recursive(v) for k,v in rawValue.items()}
        else:
            return rawValue


class GridSearchManager(AbstractSearchManager):
    """
    Assist in parameter grid search by constructing all possible
    config combinations.
    Search space can be restricted by specifying which parameter values
    should occur together. (Other combinations are prohibited.)
    """

    def __init__(self, defaultConfig: Dict):
        super().__init__()

        self.defaultConfig = defaultConfig
        self.paramAxes = {}
        self.axisOrder = []
        self.isCompoundAxis = {}
        self.dependencies = []

    def add_param_axis(self, paramName: str, paramValues: Union[List, Dict], isCompound: bool = False,
                       insertBeforeIndex: int = -1):
        """
        Add a list of values that a parameter can take, turning it into a 'parameter axis'.
        The value can be an object, a list of object or a dictionary.
        Dictionaries are used for specifying parameter value aliases, which can be used
        to simplify calls to 'restrict'.

        Compound axes define corresponding values to multiple parameters, i.e. make a set
        of parameters change together.
        (This is similar to 'restriction', but is much more convenient for many parameters.)

        :param paramName:
        :param paramValues:
        :param isCompound:
        :param insertBeforeIndex: Allows axes to be added out-of-order.
        :return:
        """
        if not isinstance(paramValues, dict) and isCompound:
            raise RuntimeError("Compound axes must use parameter value aliasing.")

        if not isinstance(paramValues, list) and not isinstance(paramValues, dict):
            paramValues = [paramValues]

        self.paramAxes[paramName] = paramValues
        if insertBeforeIndex == -1:
            self.axisOrder.append(paramName)
        else:
            self.axisOrder.insert(insertBeforeIndex, paramName)
        self.isCompoundAxis[paramName] = isCompound

    def restrict(self,
                 dependencyName: str, dependencyValues: Union[Any, List],
                 dependentName: str, dependentValues: Union[Any, List]):
        """
        Restricts the search space by specifying that if the dependency has one of the provided values,
        the dependent parameter must have one the corresponding provided values as well.
        If the dependency is not satisfied, the parameter combination is skipped.
        :param dependencyName:
        :param dependencyValues:
        :param dependentName:
        :param dependentValues:
        :return:
        """

        if dependencyName not in self.paramAxes:
            raise RuntimeError("Unknown dependency name: '{}'".format(dependencyName))
        if dependentName not in self.paramAxes:
            raise RuntimeError("Unknown dependent name: '{}'".format(dependencyName))

        if not isinstance(dependencyValues, list):
            dependencyValues = [dependencyValues]
        if not isinstance(dependentValues, list):
            dependentValues = [dependentValues]

        for value in dependencyValues:
            if value not in self.paramAxes[dependencyName]:
                raise RuntimeError("Dependency value is missing from the configuration: '{}'".format(value))
        for value in dependentValues:
            if value not in self.paramAxes[dependentName]:
                raise RuntimeError("Dependent value is missing from the configuration: '{}'".format(value))

        self.dependencies.append({
            'dependency-name': dependencyName,
            'dependency-values': dependencyValues,
            'dependent-name': dependentName,
            'dependent-values': dependentValues,
        })

    def restrict_two_way(self, paramA: str, valuesA: Union[Any, List], paramB: str, valuesB: Union[Any, List]):
        """
        Restrict two parameters, such that their specified values only occur together.
        :param paramA:
        :param valuesA:
        :param paramB:
        :param valuesB:
        :return:
        """
        self.restrict(paramA, valuesA, paramB, valuesB)
        self.restrict(paramB, valuesB, paramA, valuesA)

    def generate_configuration(self) -> Generator[SearchConfiguration, None, None]:
        """
        Generate all configuration combinations. Each configuration corresponds to a point in the parameter space.
        Return both a full configuration dict, as well as a dict with only the parameter axes.
        (The latter being useful for naming/reporting.)
        :return:
        """

        paramIndices = [0] * len(self.paramAxes)

        def increment_parameter_indices():
            axis = len(paramIndices) - 1
            while paramIndices[axis] == len(self.paramAxes[self.axisOrder[axis]]) - 1 and axis >= 0:
                paramIndices[axis] = 0  # Loop around.
                axis -= 1

            if axis >= 0:
                paramIndices[axis] += 1
                return True
            else:
                return False

        pointCount = 0
        while True:
            paramAxisValues = {}

            for axis in range(len(paramIndices)):
                paramName = self.axisOrder[axis]
                paramValues = self.paramAxes[paramName]
                if isinstance(paramValues, dict):
                    paramValues = list(sorted(paramValues.keys()))  # Sort for consistent search order.

                paramAxisValues[paramName] = paramValues[paramIndices[axis]]

            # Make sure the current configuration satisfies all the search space restrictions.
            areDependenciesSatisfied = True
            for desc in self.dependencies:
                dependencyName = desc['dependency-name']
                if paramAxisValues[dependencyName] in desc['dependency-values']:
                    if paramAxisValues[desc['dependent-name']] not in desc['dependent-values']:
                        areDependenciesSatisfied = False
                        break

            if areDependenciesSatisfied:
                # Generate a configuration.
                currentConfig = copy.deepcopy(self.defaultConfig)
                # Iterate in the axis order to overwrite in proper order.
                for axis in range(len(paramIndices)):
                    paramName = self.axisOrder[axis]
                    paramValue = paramAxisValues[paramName]

                    # If the parameter values were specified as a dictionary, transform parameter value *alias*
                    # into an actual value.
                    if isinstance(self.paramAxes[paramName], dict):
                        paramValue = self.paramAxes[paramName][paramValue]
                    else:
                        paramValue = paramAxisValues[paramName]

                    # If this is a 'compound axis', it specifies multiple parameter values at once.
                    if not self.isCompoundAxis[paramName]:
                        currentConfig[paramName] = paramValue
                    else:
                        assert (isinstance(paramValue, dict))  # Compound axes must define multiple parameters.
                        subparamValues = paramValue

                        for subparamName, subparamValue in subparamValues.items():
                            currentConfig[subparamName] = subparamValue

                            # Check for accidental overwrites.
                            isOverwriting = subparamName in paramAxisValues
                            isOverwriting = isOverwriting and self.axisOrder.index(paramName) > \
                                                              self.axisOrder.index(subparamName)
                            if (isOverwriting):
                                warnings.warn("Compound axis '{}' is overwriting the value of another axis '{}'."
                                              .format(paramName, subparamName))

                pointCount += 1
                yield SearchConfiguration(searchPoint=paramAxisValues, config=currentConfig, id=pointCount - 1)

            if not increment_parameter_indices():
                break

    def get_axes_names_ordered(self):
        return self.axisOrder
