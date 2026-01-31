from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Core dependencies required for the package to work
requirements = [
    "click>=8.0.0",
    "websockets>=10.0",
    "aiohttp>=3.8.0",
    "pydantic>=2.0.0",
    "rich>=13.0.0",
    "requests>=2.28.0",
    "beautifulsoup4>=4.11.0",
    "psutil>=5.9.0",
    "cryptography>=3.4.0",
    "keyring>=23.0.0",
]

# Optional AI provider dependencies
extras_require = {
    "openai": ["openai>=1.0.0"],
    "anthropic": ["anthropic>=0.7.0"],
    "google": ["google-genai>=0.1.0"],
    "together": ["together>=0.2.0"],
    "git": ["gitpython>=3.1.0"],
    "dev": [
        "pytest>=7.0.0",
        "black>=22.0.0",
        "flake8>=5.0.0",
        "mypy>=1.0.0",
    ],
    "all": [
        "openai>=1.0.0",
        "anthropic>=0.7.0",
        "google-genai>=0.1.0",
        "together>=0.2.0",
        "gitpython>=3.1.0",
    ]
}

setup(
    name="cognautic-cli",
    version="1.2.4",
    author="Cognautic",
    author_email="cognautic@gmail.com",
    description="A Python-based CLI AI coding agent that provides agentic development capabilities with multi-provider AI support and real-time interaction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cognautic/cognautic-cli",
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
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "cognautic=cognautic.cli:main",
        ],
    },
)
