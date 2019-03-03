import sys

from pathlib import Path
from setuptools import setup, find_packages


def read_version(package):
    with (Path(package) / '__init__.py').open('r') as fd:
        for line in fd:
            # do not use "exec" here and do manual parsing to not require deps
            if line.startswith('__version__ = '):
                return line.split()[-1].strip().strip('\'')


with open("README.rst") as fp:
    long_description = fp.read()

install_requires = [
    "requests>=2.12",
    "PyYAML"
]

if sys.version_info < (3,):
    install_requires.extend([
        "ipaddress",
    ])

setup(
    name="pykube-ng",
    version=read_version('pykube'),
    description="Python client library for Kubernetes",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author="Eldarion, Inc.",
    author_email="development@eldarion.com",
    license="Apache",
    url="https://github.com/hjacobs/pykube",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
    ],
    zip_safe=False,
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={
        "gcp": [
            "google-auth",
            "jsonpath-ng",
        ]
    },
)
