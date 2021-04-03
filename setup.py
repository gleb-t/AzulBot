from glob import glob
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
      Pybind11Extension(
            "azulcpp",
            sorted(glob("azulbot/azulsimcpp/*.cpp")),
      ),
]


setup(name='azulbot',
      version='0.2',
      description='Simulator and bot for the game of Azul.',
      license='MIT',
      author='gleb-t',
      url='https://github.com/gleb-t/AzulBot',

      packages=['azulbot'],
      cmdclass={"build_ext": build_ext},
      ext_modules=ext_modules,

      zip_safe=True,
      include_package_data=True,
      install_requires=['numpy', 'numba', 'pybind11'],
      classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Libraries',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
      ],
)
