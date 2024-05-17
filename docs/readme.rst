Pykube
======

.. image:: https://img.shields.io/pypi/v/new-pykube.svg
   :target:  https://pypi.python.org/pypi/new-pykube/

.. image:: https://img.shields.io/pypi/pyversions/new-pykube.svg
   :target:  https://pypi.python.org/pypi/new-pykube/

.. image:: https://img.shields.io/badge/license-apache-blue.svg
   :target:  https://pypi.python.org/pypi/new-pykube/

Pykube (new-pykube) is a lightweight Python 3+ client library for Kubernetes.

Installation
------------

To install pykube, use pip::

    pip install new-pykube

Usage
-----

Query for all ready pods in a custom namespace:

.. code:: python

    import operator
    import pykube

    api = pykube.HTTPClient(pykube.KubeConfig.from_file())
    pods = pykube.Pod.objects(api).filter(namespace="gondor-system")
    ready_pods = filter(operator.attrgetter("ready"), pods)

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :glob:

   howtos/index
   api/modules
   README <readme>
   changelog
   users



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
