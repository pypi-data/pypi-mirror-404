"""Setup configuration for streamlit-effects."""

from setuptools import setup, find_packages
import os

# Read version
version_file = os.path.join(
    os.path.dirname(__file__), "streamlit_effects", "_version.py"
)
version_dict = {}
with open(version_file) as f:
    exec(f.read(), version_dict)

# Read README
readme_file = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_file):
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "Animated background effects for Streamlit applications"

setup(
    name="streamlit-effects",
    version=version_dict["__version__"],
    author="Trent Moore",
    author_email="trent@surfsidelabs.com",
    description="Animated background effects for Streamlit apps",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trentmoore/streamlit-effects",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Streamlit",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.20.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "mypy>=0.990",
        ],
    },
)
