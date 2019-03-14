API Modules
===========

Pykube exports its main classes on the package level, so you can do:

.. code-block:: python

    from pykube import KubeConfig, HTTPClient, Pod

* :class:`KubeConfig <pykube.config.KubeConfig>` is the main configuration class to load ``~/.kube/config`` or from in-cluster service account
* :class:`HTTPClient <pykube.http.HTTPClient>` represents the Kubernetes API client
* Kubernetes resource kinds (:class:`Pod <pykube.objects.Pod>`, etc) are defined in :mod:`pykube.objects`


.. toctree::
   :maxdepth: 4

   pykube
