# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="georgian-hyphenation",
    version="2.2.6",
    author="Guram Zhgamadze",
    author_email="guramzhgamadze@gmail.com",
    description="Georgian Language Hyphenation Library v2.2.6 - Preserves compound word hyphens",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/guramzhgamadze/georgian-hyphenation",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "georgian_hyphenation": ["data/*.json"],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Text Processing :: Linguistic",
        "Natural Language :: Georgian",
    ],
    python_requires=">=3.7",
)