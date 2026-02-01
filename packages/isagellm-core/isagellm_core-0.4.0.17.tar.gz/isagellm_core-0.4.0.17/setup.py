
from setuptools import setup

setup(
    include_package_data=True,
    package_data={
        "": ["*.pyc", "*.pyo", "__pycache__/*", "*.so", "*.pyd", "*.dylib"],
    },
)
