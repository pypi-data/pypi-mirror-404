"""
Cost Katana Python SDK
A simple, unified interface for AI models with built-in cost optimization,
failover, and analytics - no API keys needed in your code!
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="cost-katana",
    version="2.2.6",
    author="Cost Katana Team",
    author_email="support@costkatana.com",
    description="The simplest way to use AI in Python with automatic cost tracking and optimization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Hypothesize-Tech/cost-katana-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    keywords="ai, machine learning, cost optimization, openai, anthropic, aws bedrock, gemini, claude",
    project_urls={
        "Bug Reports": "https://github.com/Hypothesize-Tech/cost-katana-python/issues",
        "Source": "https://github.com/Hypothesize-Tech/cost-katana-python",
        "Documentation": "https://docs.costkatana.com",
    },
    entry_points={
        'console_scripts': [
            'costkatana=cost_katana.cli:main',
        ],
    },
)