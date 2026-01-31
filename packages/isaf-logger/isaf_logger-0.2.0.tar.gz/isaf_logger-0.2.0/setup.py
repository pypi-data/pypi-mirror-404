"""ISAF Logger - Setup Configuration"""

from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

setup(
    name="isaf-logger",
    version="0.1.0",
    author="HAIEC Lab",
    author_email="contact@haiec.com",
    description="Instruction Stack Audit Framework - Automatic compliance logging for AI systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/haiec/isaf-logger",
    project_urls={
        "Documentation": "https://haiec.com/isaf/docs",
        "Bug Tracker": "https://github.com/haiec/isaf-logger/issues",
        "Homepage": "https://haiec.com/isaf"
    },
    packages=find_packages(exclude=["tests*", "examples*"]),
    package_data={
        "isaf": ["schemas/*.json"]
    },
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
        "click>=8.0.0"
    ],
    extras_require={
        "mlflow": ["mlflow>=2.0.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mlflow>=2.0.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "isaf=isaf.cli:main"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    keywords="ai ml compliance audit logging eu-ai-act nist isaf"
)
