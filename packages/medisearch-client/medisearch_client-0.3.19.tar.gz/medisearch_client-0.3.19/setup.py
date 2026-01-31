"""Setup file for the medisearch_client package."""

from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="medisearch_client",
    version="0.3.19",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "aiohttp>=3.9.0",
        "rich>=13.0.0",  # Required for test client
        "urllib3>=2.0.0",
    ],
    extras_require={
        "test": [
            "rich>=13.0.0",
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-timeout>=2.2.0",
        ],
        "dev": [
            "black>=24.0.0",
            "isort>=5.13.0",
            "mypy>=1.8.0",
            "pylint>=3.0.0",
            "ruff>=0.2.0",
        ],
    },
    python_requires=">=3.10",
    author="Michal Pandy",
    author_email="founders@medisearch.io",
    description="A Python client for the MediSearch medical information API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MediSearch/medisearch_client_python",
    project_urls={
        "Documentation": "https://docs.medisearch.io",
        "Source": "https://github.com/MediSearch/medisearch_client_python",
        "Issues": "https://github.com/MediSearch/medisearch_client_python/issues",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="medical, healthcare, api, search, research, medisearch",
)
