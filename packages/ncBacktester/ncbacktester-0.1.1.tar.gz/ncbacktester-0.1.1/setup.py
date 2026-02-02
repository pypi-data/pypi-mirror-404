from setuptools import setup, find_packages
from pathlib import Path

readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="ncBacktester",
    version="0.1.1",
    author="ncBacktester Team",
    author_email="sksharm4@ncsu.edu",  
    description="A simple backtesting engine for trading strategies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gjarment/FIM500AlgoTrading",  
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "matplotlib>=3.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    keywords="backtesting, trading, finance, strategy, quantitative",
    project_urls={
        "Bug Reports": "https://github.com/gjarment/FIM500AlgoTrading/issues",
        "Source": "https://github.com/gjarment/FIM500AlgoTrading/tree/main/ncBacktester",  
        "Documentation": "https://github.com/gjarment/FIM500AlgoTrading/tree/main/ncBacktester#readme",  
    },
)

