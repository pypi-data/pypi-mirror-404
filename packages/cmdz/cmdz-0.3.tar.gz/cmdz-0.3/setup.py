from setuptools import setup, find_packages

setup(
    name="cmdz",
    version="0.3",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "cmdz=cmdz.cli:main",
        ]
    },
)