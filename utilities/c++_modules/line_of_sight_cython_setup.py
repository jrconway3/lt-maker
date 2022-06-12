try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from Cython.Build import cythonize
# Compile with `python line_of_sight_cython_setup.py build_ext --inplace`
# Can get cython from `pip install cython`
# Can get Windows compilation tools from Visual Studio 2019 build tools
# Follow: https://stackoverflow.com/a/50210015
setup(
    ext_modules=cythonize("line_of_sight_cython.pyx", language_level="3")
)