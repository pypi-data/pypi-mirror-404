from setuptools import setup, find_packages

setup(
    name="RedaTade",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["requests"],
    author="Reda",
    description="Stats and Config Library for Challenge Bot",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
