from setuptools import setup, find_packages

setup(
    name="QuickSearch-py",
    version="1.0.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "whoosh",
        "motor",       # Async MongoDB driver
        "pymongo",
    ],
    python_requires=">=3.8",
)