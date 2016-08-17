import os
import re
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def get_version():
    raw_init_file = read("cloudpassage/__init__.py")
    rx_compiled = re.compile(r"\s*__version__\s*=\s*\"(\S+)\"")
    ver = rx_compiled.search(raw_init_file).group(1)
    return ver

setup(
    name="cloudpassage",
    version=get_version(),
    author="CloudPassage",
    author_email="toolbox@cloudpassage.com",
    description="Python SDK for CloudPassage Halo API",
    license="BSD",
    keywords="cloudpassage halo api sdk",
    url="http://github.com/cloudpassage/cloudpassage-halo-python-sdk",
    packages=["cloudpassage"],
    install_requires=["requests", "pyaml"],
    long_description=read("README.rst"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Topic :: Security",
        "License :: OSI Approved :: BSD License"
        ],
    )
