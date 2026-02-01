from setuptools import setup, find_packages
import os
import sys

# Add the package directory to the path to import version
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from fishertools._version import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fishertools",
    version=__version__,
    author="f1sherFM",
    author_email="kirillka229top@gmail.com",
    description="Fishertools - инструменты, которые делают Python удобнее и безопаснее для новичков",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/f1sherFM/My_1st_library_python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests",
        "click",
    ],
)