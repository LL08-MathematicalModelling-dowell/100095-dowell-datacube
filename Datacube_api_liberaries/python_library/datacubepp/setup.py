from setuptools import setup, find_packages
from pathlib import Path

# Read the content of README.md
current_dir = Path(__file__).parent
long_description = (current_dir / "README.md").read_text()

setup(
    name="datacubepp",
    version="1.0.0",
    description="A Python client for interacting with a Dowell Datacube backend API for database and collection management.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Muhammad B. Ibrahim",
    author_email="ibrahimmuhammad271@gmail.com",
    url="https://github.com/your-repo/mypackage",
    packages=find_packages(),
    install_requires=[
    "requests>=2.28.0",
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
    keywords="API client, MongoDB, database management",
    project_urls={
        "Documentation": "https://github.com/your-repo/mypackage#readme",
        "Source": "https://github.com/your-repo/mypackage",
        "Tracker": "https://github.com/your-repo/mypackage/issues",
    },
)
