from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="topsis_manav_102303990",
    version="1.0.2",
    author="Manav Bhullar",
    author_email="manavbhullar341@gmail.com",
    description="A Python package for TOPSIS method",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_manav_102303990.topsis:run"
        ]
    },
    python_requires=">=3.7",
)