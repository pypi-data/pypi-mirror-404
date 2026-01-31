"""
Risk Mirror SDK - Python Package Setup
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read() if f else ""

setup(
    name="risk-mirror",
    version="1.0.1",
    author="RTN Labs",
    author_email="support@risk-mirror.com",
    description="Deterministic AI Safety Toolkit - Python SDK & CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/myProjectsRavi/risk-mirror-core",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[],  # Zero dependencies - uses stdlib only
    extras_require={
        "dev": ["pytest", "pytest-cov", "mypy"],
    },
    entry_points={
        "console_scripts": [
            "risk-mirror=risk_mirror.cli:main",
        ],
    },
    keywords=["ai-safety", "pii", "secrets", "prompt-security", "deterministic", "cli"],
)
