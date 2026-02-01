from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="insa-its",
    version="2.4.0",
    author="YuyAI / InsAIts Team",
    author_email="info@yuyai.pro",
    description="Open-core multi-LLM communication monitoring, hallucination detection & deciphering for agent systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nomadu27/InsAIts",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "requests>=2.26.0",
        "websocket-client>=1.0.0",
    ],
    extras_require={
        "local": ["sentence-transformers>=2.2.0"],
        "graph": ["networkx>=2.6.0"],
        "full": ["sentence-transformers>=2.2.0", "networkx>=2.6.0"],
    },
)