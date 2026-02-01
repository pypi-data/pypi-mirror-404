from setuptools import setup, find_packages

setup(
    name="spaceops",
    version="0.1.0",
    description="CI/CD pipeline for Databricks Genie spaces - multi-workspace promotion at scale",
    author="SpaceOps Team",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1.0",
        "httpx>=0.27.0",
        "pydantic>=2.5.0",
        "pyyaml>=6.0.0",
        "rich>=13.7.0",
        "deepdiff>=7.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "spaceops=spaceops.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

