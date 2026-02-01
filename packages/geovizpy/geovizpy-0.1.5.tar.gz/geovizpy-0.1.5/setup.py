"""Setup script for the geovizpy package."""

from setuptools import setup, find_packages

# Read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="geovizpy",
    version="0.1.5",
    description="A Python wrapper for the geoviz JavaScript library",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="fbxyz",
    packages=find_packages(),
    install_requires=[],
    extras_require={
        "export": ["playwright"]
    },
    project_urls={
        'Source': 'https://codeberg.org/fbxyz/geovizpy',
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
