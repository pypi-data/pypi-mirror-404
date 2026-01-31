"""
CliMaPan-Lab: Climate-Pandemic Economic Modeling Laboratory
Setup script for package installation
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="climapan-lab",
    version="0.1.0",
    author="CliMaPan-Lab Team",
    description="Climate-Pandemic Economic Modeling Laboratory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/a11to1n3/climapan-lab",
    packages=find_packages(exclude=["tests*", "docs*", "results*"]),
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "matplotlib>=3.5.0",
        "ambr>=0.1.5",
        "scikit-learn>=1.0.0",
        "scipy>=1.7.0",
        "joblib>=1.1.0",
        "salib>=1.4.0",
        "networkx>=2.6.0",
        "pathos>=0.2.8",
        "dill>=0.3.4",
        "h5py>=3.7.0",
        "statsmodels>=0.13.0",
        "plotly>=5.0",
        "pyarrow>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "climapan-run=climapan_lab.run_sim:main",
            "climapan-example=climapan_lab.examples.simple_example:run_simple_simulation",
        ],
    },
)
