"""Setup script for Windows Package Manager."""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path("README.md")
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path("requirements.txt")
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="winget-package-manager",
    version="1.0.0",
    author="tboy1337",
    author_email="tboy1337@example.com",
    description="A GUI-based Windows Package Manager using winget",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tboy1337/Windows-Package-Manager",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["data/*.json"],
    },
    install_requires=[
        # Runtime dependencies only
    ],
    extras_require={
        "dev": requirements,  # Development dependencies
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "winget-pm=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: System :: Software Distribution",
        "Topic :: Utilities",
    ],
    keywords="winget, package manager, windows, gui",
)
