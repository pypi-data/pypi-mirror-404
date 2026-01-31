# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def read_readme():
    if os.path.exists("README.md"):
        with open("README.md", encoding="utf-8") as f:
            return f.read()
    return ""


setup(
    name="shiftaiagenticinfra-sdk-python",
    version="0.0.6",
    description="Shiftai Agentic Infra Python SDK",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="ShiftAI",
    author_email="s.tadakamalla@theshiftai.in",
    # url="https://github.com/shiftai/communication-infrastructure",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

