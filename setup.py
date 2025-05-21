"""
Setup script for DAS Auto Experiment Application.
"""
import os
from setuptools import setup, find_packages

# Get the absolute path to the pztlibrary directory
pztlibrary_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pztlibrary")

setup(
    name="das-auto-experiment-app",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "pyserial>=3.5",
    ],
    dependency_links=[
        f"file://{pztlibrary_path}#egg=pztlibrary-1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "das-experiment=run:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Automated experiment application for controlling piezo actuators",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
) 