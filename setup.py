import sys

from setuptools import setup, find_packages


with open("README.rst") as fp:
    long_description = fp.read()

install_requires = [
    "requests>=2.12",
    "PyYAML",
    "six>=1.10.0",
    "tzlocal",
]

if sys.version_info < (3,):
    install_requires.extend([
        "ipaddress",
    ])

setup(
    name="pykube-ng",
    version="0.17a1",
    description="Python client library for Kubernetes",
    long_description=long_description,
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
    entry_points={
        "httpie.plugins.transport.v1": [
            "httpie_pykube = pykube.contrib.httpie_plugin:PyKubeTransportPlugin"
        ],
    },
    install_requires=install_requires,
    extras_require={
        "gcp": [
            "google-auth",
            "jsonpath-ng",
        ]
    },
)
