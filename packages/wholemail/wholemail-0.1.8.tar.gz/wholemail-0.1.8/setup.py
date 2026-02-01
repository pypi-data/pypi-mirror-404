
import setuptools
from setuptools import setup, find_packages

long_description = ""
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="wholemail",
    version="0.1.8",
    author="Victor Kipkemboi",
    author_email="scriptilapia@gmail.com",
    long_description =long_description,
    long_description_content_type="text/markdown",
    description="A lucid Python package built to facilitate easy sending of emails and other common generic functionality like sending authentication code emails",
    url="https://github.com/victhepythonista/wholemail",
    project_urls={
        "Bug Tracker": "https://github.com/victhepythonista/wholemail/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    packages=["wholemail"],
    python_requires=">=3.6",
    install_requires=[
          'Jinja2', "code_monger" , "bs4",
      ],
 
)