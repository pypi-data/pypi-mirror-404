import os
import sys

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.sdist import sdist

try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None

PYPY = hasattr(sys, "pypy_version_info")


class BuildExt(build_ext):
    def build_extension(self, ext):
        for source in ext.sources:
            pyx = os.path.splitext(source)[0] + ".pyx"
            if not os.path.exists(pyx):
                if not cythonize:
                    print("WARNING")
                    print("Cython is required for building extension.")
                    print("Cython can be installed from PyPI.")
                    print("Falling back to pure Python implementation.")
                    return
                cythonize(pyx)
            elif os.path.exists(pyx) and os.stat(source).st_mtime < os.stat(pyx).st_mtime and cythonize:
                cythonize(pyx)
        try:
            return build_ext.build_extension(self, ext)
        except Exception as e:
            print("WARNING: Failed to compile extension modules.")
            print("Falling back to pure Python implementation.")
            print(e)


class Sdist(sdist):
    def __init__(self, *args, **kwargs):
        cythonize("safe_radix32/_cython.pyx")
        sdist.__init__(self, *args, **kwargs)


ext_modules = []
if not PYPY:
    ext_modules.append(Extension("safe_radix32._cython", sources=["safe_radix32/_cython.c"]))

setup(
    packages=["safe_radix32"],
    cmdclass={"build_ext": BuildExt, "sdist": Sdist},
    ext_modules=ext_modules,
)
