#!/usr/bin/env python
"""
Setup script for the PDF Vector Search Engine package.
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Get package version
version = "1.0.0"

# Read requirements from requirements.txt
req_file = Path(__file__).parent / "requirements.txt"
with open(req_file, "r") as f:
    requirements = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]

# Read long description from README.md
readme_file = Path(__file__).parent / "README.md"
with open(readme_file, "r") as f:
    long_description = f.read()

setup(
    name="pdf-vector-search",
    version=version,
    description="A production-ready PDF Vector Search Engine using AI technology",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Engiverse",
    author_email="info@engiverse.com",
    url="https://github.com/engiverse/pdf-vector-search",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "pdf-search=backend.vector_search_mistral.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Indexing",
    ],
    keywords="pdf, vector search, embeddings, semantic search, nlp, mistral",
    license="MIT",
) 