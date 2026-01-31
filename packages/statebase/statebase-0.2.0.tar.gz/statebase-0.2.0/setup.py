from setuptools import setup, find_packages
import pathlib

# Read the README
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="statebase",
    version="0.2.0",
    description="The Reliability Layer for Production AI Agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/StateBase/statebase-python",
    author="StateBase Team",
    author_email="hello@statebase.org",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="ai, agents, memory, state, llm",
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0"
    ],
    project_urls={
        "Bug Reports": "https://github.com/StateBase/statebase-python/issues",
        "Source": "https://github.com/StateBase/statebase-python",
    },
)
