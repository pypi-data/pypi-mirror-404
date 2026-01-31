#!/usr/bin/env python3
"""
Enumageddon - Web Fuzzer & Cloud Enumeration Tool
Setup configuration for pip/pipx installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="enumageddon",
    version="1.0.4",
    author="Not-4O4",
    author_email="security@example.com",
    description="A powerful multi-threaded web fuzzer and OSINT tool for discovering endpoints and cloud services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/enumageddon",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/enumageddon/issues",
        "Documentation": "https://github.com/yourusername/enumageddon#readme",
        "Source Code": "https://github.com/yourusername/enumageddon",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.31.0",
        "dnspython>=2.4.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "enumageddon=enumageddon.main:main",
        ],
    },
    keywords="fuzzing enumeration osint security bug-bounty cloud aws gcp azure",
    include_package_data=True,
    zip_safe=False,
)
