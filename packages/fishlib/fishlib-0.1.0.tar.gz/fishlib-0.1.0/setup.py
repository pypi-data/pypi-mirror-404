from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fishlib",
    version="0.1.0",
    author="Karen Morton",
    author_email="kmorton319@gmail.com",
    description="A Python library for parsing, standardizing, and comparing seafood product descriptions in foodservice",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KTG0409/fishlib",
    packages=find_packages(),
    package_data={
        'fishlib': ['data/*.json'],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Office/Business",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
        ],
    },
    keywords="seafood, fish, foodservice, parsing, standardization, pricing, comparison",
)
