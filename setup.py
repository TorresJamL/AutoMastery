from setuptools import setup, find_packages

setup(
    name="automastery",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28",
        "pandas>=2.0",
        "numpy>=1.24",
        "tqdm>=4.60",
        "openpyxl>=3.1",
        "gradescope-tool>=0.1.4",
        "beautifulsoup4>=4.12",
    ],
    python_requires=">=3.10",
)
