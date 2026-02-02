#!/usr/bin/env python3
"""
ONTO Standard - Reference Implementation
pip install onto-standard
"""

from setuptools import setup, find_packages

setup(
    name="onto-standard",
    version="10.0.0",
    description="ONTO Epistemic Risk Standard v10.0 Reference Implementation",
    long_description=open("README_PACKAGE.md").read(),
    long_description_content_type="text/markdown",
    author="ONTO Standards Council",
    author_email="standards@onto-bench.org",
    url="https://onto-bench.org/standard",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],  # No dependencies - pure Python
    entry_points={
        "console_scripts": [
            "onto-standard=onto_standard:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Quality Assurance",
    ],
    keywords="ai ml llm calibration uncertainty epistemic compliance",
    project_urls={
        "Documentation": "https://onto-bench.org/standard",
        "Source": "https://github.com/onto-project/onto-standard",
        "Standard": "https://onto-bench.org/standard/v10.0",
    },
)
