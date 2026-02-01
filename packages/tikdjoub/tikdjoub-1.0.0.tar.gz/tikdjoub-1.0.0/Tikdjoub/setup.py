from setuptools import setup, find_packages

setup(
    name="Tikdjoub",
    version="0.1.0",
    description="TikTok signature generator",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="djoub",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "pycryptodome",
        "uuid",         
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
