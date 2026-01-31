from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="claude-code-plugins",
    version="1.0.0",
    description="Bundled plugins for Claude Code including Agent SDK development tools, PR review toolkit, and commit workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Anthropic",
    author_email="support@anthropic.com",
    url="https://github.com/anthropics/claude-code",
    packages=find_packages(),
    include_package_data=True,
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
        "Topic :: Software Development :: Libraries",
    ],
    keywords="claude claude-code plugins ai development",
    project_urls={
        "Documentation": "https://code.claude.com/docs",
        "Source": "https://github.com/anthropics/claude-code",
        "Issues": "https://github.com/anthropics/claude-code/issues",
    },
)
