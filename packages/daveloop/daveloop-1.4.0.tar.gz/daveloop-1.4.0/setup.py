#!/usr/bin/env python3
"""
DaveLoop - Self-Healing Debug Agent
Setup configuration for pip installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="daveloop",
    version="1.4.0",
    description="Self-healing debug agent powered by Claude Code CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dave Bruzil",
    url="https://github.com/davebruzil/DaveLoop",
    py_modules=["daveloop", "daveloop_swebench"],
    python_requires=">=3.7",
    install_requires=[
        # No external dependencies - uses only stdlib
    ],
    entry_points={
        "console_scripts": [
            "daveloop=daveloop:main",
            "daveloop-swebench=daveloop_swebench:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["daveloop_prompt.md", "daveloop_maestro_prompt.md", "daveloop_web_prompt.md"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Quality Assurance",
    ],
    keywords="debugging ai claude automation agent",
)
