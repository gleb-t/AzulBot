import os
import sys

# Couldn't find a better way of importing the .pyd module while storing it as a submodule.
# Trying to use relative imports would break the stubs.
# (I would need to create a stub for the outer 'azulbot' module to point out the submodule,
#  and then I'll have to recreate all the definitions, since PyCharm doesn't support partial stubs.)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# noinspection PyUnresolvedReferences
from .azul import Azul, AzulState, Move
# noinspection PyUnresolvedReferences
from azulcpp import PlayerState, MoveOutcome, Color
