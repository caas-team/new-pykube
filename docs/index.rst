Pykube
======

.. image:: https://img.shields.io/pypi/v/pykube-ng.svg
   :target:  https://pypi.python.org/pypi/pykube-ng/

.. image:: https://img.shields.io/pypi/pyversions/pykube-ng.svg
   :target:  https://pypi.python.org/pypi/pykube-ng/

.. image:: https://img.shields.io/badge/license-apache-blue.svg
   :target:  https://pypi.python.org/pypi/pykube-ng/

Pykube (pykube-ng) is a lightweight Python 3+ client library for Kubernetes.

Installation
------------

To install pykube, use pip::

    pip install pykube-ng

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

There is not much documentation yet, but you can check out the `README on github <https://github.com/hjacobs/pykube>`_ and browse the :ref:`pykube-package`.

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
