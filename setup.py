from setuptools import setup, Extension
import sys
import pybind11

ext_modules = [
    Extension(
        "rsa_cpp",
        sources=["cpp/rsa_module.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++",
    ),
]

setup(
    name="rsa_cpp",
    version="0.0.1",
    ext_modules=ext_modules,
)
