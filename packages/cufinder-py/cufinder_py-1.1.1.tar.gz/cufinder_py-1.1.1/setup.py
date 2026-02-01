#!/usr/bin/env python3
"""Setup configuration for Cufinder Python SDK."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = [
    "requests>=2.28.0",
    "pydantic>=2.0.0",
    "typing-extensions>=4.0.0",
]

setup(
    name="cufinder-py",
    version="1.1.1",
    author="Cufinder Team",
    author_email="support@cufinder.io",
    description="Type-safe Python SDK for easily integrating with the Cufinder API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CUFinder/cufinder-py",
    project_urls={
        "Bug Reports": "https://github.com/CUFinder/cufinder-py/issues",
        "Source": "https://github.com/CUFinder/cufinder-py",
        "Documentation": "https://docs.cufinder.io/python",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "types-requests>=2.28.0",
        ],
    },
    keywords="cufinder, api, sdk, python, b2b, data-enrichment",
    include_package_data=True,
    zip_safe=False,
)
