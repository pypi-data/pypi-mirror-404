from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    description = f.read()

setup(
    name="y_not_finance",
    version="1.0.0",
    description="Financial data library for prices and index constituents",
    long_description=description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "numpy",
        "pandas",
        "requests",
    ],
    python_requires=">=3.8",
)