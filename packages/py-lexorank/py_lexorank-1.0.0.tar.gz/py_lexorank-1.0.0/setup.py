from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="py-lexorank",  # 更新包名
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Lightweight, dependency-free Python implementation of LexoRank algorithm for fractional indexing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ixfcao/lexorank-py",
    packages=find_packages(),
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
    ],
    python_requires=">=3.7",
    install_requires=[],
)