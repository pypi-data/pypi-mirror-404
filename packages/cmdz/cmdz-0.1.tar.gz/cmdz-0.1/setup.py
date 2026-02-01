from setuptools import setup, find_packages

setup(
    name="cmdz",
    version="0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "cmdz=cmdz.cli:main",
        ]
    },
)