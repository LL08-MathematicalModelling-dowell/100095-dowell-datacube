"""
Setup script for the datacubepp package.
This script uses setuptools to package the datacubepp library, which is a Python client for
interacting with a Dowell Datacube backend API for database and collection management.
Attributes:
    current_dir (Path): The directory where the setup.py file is located.
    long_description (str): The content of the README.md file, used as the long 
    description for the package.
Functions:
    setup: Configures the package with metadata and dependencies.
"""

from pathlib import Path
from setuptools import setup, find_packages


# Read the content of README.md
current_dir = Path(__file__).parent
long_description = (current_dir / "README.md").read_text()

setup(
    name="datacubepp",
    version="1.0.0",
    description="""A Python client for interacting with a Dowell Datacube backend
                 API for database and collection management.""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Muhammad B. Ibrahim",
    author_email="ibrahimmuhammad271@gmail.com",
    url="https://github.com/LL08-MathematicalModelling-dowell/100095-dowell-datacube/backend/Datacube_api_libraries/python_library_datacubp",
    packages=find_packages(include=["datacubepp"]),
    install_requires=[
    "requests>=2.28.0",
    "httpx==0.28.1",
    "pymongo>=4.0.0",
    "pydantic>=1.10.0",
    "typing-extensions>=4.5.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    keywords="API client, MongoDB, database management, Datacube",
    project_urls={
        "Documentation": "https://github.com/LL08-MathematicalModelling-dowell/100095-dowell-datacube/backend/Datacube_api_libraries/python_library/datacubpp#readme",
        "Source": "https://github.com/LL08-MathematicalModelling-dowell/100095-dowell-datacube/backend/Datacube_api_libraries/python_library/datacubpp",
        "Tracker": "https://github.com/LL08-MathematicalModelling-dowell/100095-dowell-datacube/backend/Datacube_api_libraries/python_library/datacubpp/issues",
    },
)
