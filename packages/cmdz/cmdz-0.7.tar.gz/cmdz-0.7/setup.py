from setuptools import setup, find_packages

setup(
    name="cmdz",
    version="0.7",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "cmdz=cmdz.cli:main",
        ]
    },
)

# python setup.py sdist bdist_wheel
# python -m twine upload dist/*