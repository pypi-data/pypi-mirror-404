"""Setup script for compress-lightreach package."""

from setuptools import setup, find_packages
import os

# Read README for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Intelligent compression algorithms for LLM prompts that reduce token usage"

# Read version from _version.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "pcompresslr", "_version.py")
    with open(version_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="compress-lightreach",
    version=get_version(),
    author="Light Reach",
    author_email="jonathankt@lightreach.io",
    description="Intelligent compression algorithms for LLM prompts that reduce token usage",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://compress.lightreach.io",
    project_urls={
        "Homepage": "https://compress.lightreach.io",
        "Documentation": "https://compress.lightreach.io/docs",
        "Source": "https://github.com/lightreach/compress-lightreach",
        "Bug Tracker": "https://github.com/lightreach/compress-lightreach/issues",
    },
    packages=find_packages(exclude=["tests", "scripts", "api", "compressors", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "tiktoken>=0.5.0",
        "requests>=2.31.0",
        "urllib3>=2.0.0",
    ],
    include_package_data=True,
    extras_require={
        "api": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.0.0",
            "python-multipart>=0.0.6",
        ],
    },
    entry_points={
        "console_scripts": [
            "pcompresslr=pcompresslr.cli:main",
        ],
    },
)

