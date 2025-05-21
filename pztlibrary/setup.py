"""
Setup script for pztlibrary package.
"""
from setuptools import setup, find_packages

setup(
    name="pztlibrary",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pyserial>=3.5",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="Library for controlling piezo actuators",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
) 