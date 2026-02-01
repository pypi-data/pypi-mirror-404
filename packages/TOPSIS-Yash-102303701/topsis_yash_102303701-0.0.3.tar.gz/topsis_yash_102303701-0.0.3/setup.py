from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="TOPSIS-Yash-102303701",
    version="0.0.3",
    author="Yash Sharma",
    author_email="yash@example.com",
    description="TOPSIS implementation using Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_yash_102303701.topsis:main"
        ]
    },
)

