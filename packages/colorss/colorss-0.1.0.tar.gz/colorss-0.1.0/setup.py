# setup.py
from setuptools import setup, find_packages

setup(
    name="colorss",
    version="0.1.0",
    author="Paradox",
    description="colors's",
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[],  # Add dependencies if needed
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)