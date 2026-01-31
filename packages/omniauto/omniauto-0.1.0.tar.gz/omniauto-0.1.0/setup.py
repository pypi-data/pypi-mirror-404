# setup.py - REEMPLAZA completamente con esto:
from setuptools import setup, find_packages
import os

# Leer README automáticamente
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="omniauto",
    version="0.1.0",
    author="Dancenot0",
    author_email="dancenot02@gmail.com",
    description="Single Point of Truth dinámico para proyectos Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Dancenot0/omniauto",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: Software Development :: Build Tools",
    ],
    python_requires=">=3.7",
    install_requires=[
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "omniauto=omniauto.cli:main",
        ],
    },
    include_package_data=True,
    keywords=[
        "automation", "discovery", "registry", "dynamic",
        "framework", "modules", "auto-import", "plugin",
        "decorator", "single-point-of-truth", "spoft"
    ],
    project_urls={
        "Bug Tracker": "https://github.com/Dancenot0/omniauto/issues",
        "Documentation": "https://github.com/Dancenot0/omniauto#readme",
        "Source Code": "https://github.com/Dancenot0/omniauto",
        "Changelog": "https://github.com/Dancenot0/omniauto/releases",
    },
)