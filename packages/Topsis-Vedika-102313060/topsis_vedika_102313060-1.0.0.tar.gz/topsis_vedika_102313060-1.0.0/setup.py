from setuptools import setup, find_packages

setup(
    name="Topsis-Vedika-102313060",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.cli:main"
        ]
    },
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
