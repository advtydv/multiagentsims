"""Setup configuration for SafetyChecker package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="safetychecker",
    version="0.1.0",
    author="SafetyChecker Contributors",
    description="A Multi-Agent System for AI Safety Research",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/safetychecker",
    packages=find_packages(exclude=["tests", "tests.*", "scripts", "docs", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv>=0.19.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.12.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
        ],
    },
    entry_points={
        "console_scripts": [
            "safetychecker=scripts.run_simulation:main",
        ],
    },
)