from setuptools import setup, find_packages

setup(
    name="marock",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.7",
    description="Marock allows you to colour up your texts, marock.help() for more info. ",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Marcy",
)

