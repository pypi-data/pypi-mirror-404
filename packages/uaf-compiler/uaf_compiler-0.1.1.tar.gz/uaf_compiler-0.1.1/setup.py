from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="uaf_compiler",
    version="0.1.1",
    author="Vaibhav Haswani",
    author_email="vaibhav@defaultloop.com", # Placeholder or need to ask? I'll use a generic one or omit if unsure, but author field is good. I will use the name provided.
    description="Universal Agent File (UAF) Compiler & Protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DefaultLoop/uaf-compiler", # Assuming URL based on project name
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    install_requires=[
        "pyyaml",
        "pydantic",
    ],
    entry_points={
        "console_scripts": [
            "uaf=uaf_compiler.main:main",
        ],
    },
)
