"""
OneX SDK Setup Configuration
Package neural signal monitoring as pip-installable module
"""

import os
from setuptools import setup, find_packages

# Read version from version.py
version = {}
with open(os.path.join("onex", "version.py")) as fp:
    exec(fp.read(), version)

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    # Package metadata
    name="onex-sdk",
    version=version["__version__"],
    author=version["__author__"],
    author_email=version["__email__"],
    description="Framework-agnostic neural signal monitoring for inside-the-brain observability",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/onex-ai/onex-sdk",
    project_urls={
        "Bug Tracker": "https://github.com/onex-ai/onex-sdk/issues",
        "Documentation": "https://docs.onex.io",
        "Source Code": "https://github.com/onex-ai/onex-sdk",
    },
    
    # Package discovery
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    
    # Package data
    include_package_data=True,
    package_data={
        "onex": ["py.typed"],  # For type hints
    },
    
    # Dependencies
    install_requires=requirements,
    
    # Optional dependencies
    extras_require={
        "pytorch": ["torch>=1.12.0"],
        "tensorflow": ["tensorflow>=2.8.0"],
        "jax": ["jax>=0.3.0", "jaxlib>=0.3.0"],
        "all": [
            "torch>=1.12.0",
            "tensorflow>=2.8.0",
            "jax>=0.3.0",
            "jaxlib>=0.3.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "twine>=4.0.0",
            "build>=0.7.0",
        ],
    },
    
    # Python version requirement
    python_requires=">=3.8",
    
    # PyPI classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    
    # Keywords for PyPI search
    keywords=[
        "machine-learning",
        "deep-learning",
        "neural-networks",
        "monitoring",
        "observability",
        "bert",
        "transformers",
        "pytorch",
        "tensorflow",
        "mlops",
    ],
    
    # Entry points (optional - for CLI tools)
    entry_points={
        "console_scripts": [
            "onex-cli=onex.cli:main",  # If you want CLI tools
        ],
    },
    
    # License
    license="MIT",
    
    # Zip safe
    zip_safe=False,
)
