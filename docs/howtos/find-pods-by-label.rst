How to find Pods by label
=========================

This section explains how to find Kubernetes pods by a set of known labels.

Calling :func:`objects <pykube.objects.APIObject.objects>` on the :class:`Pod <pykube.objects.Pod>` class returns a :class:`Query <pykube.query.Query>` object which provides the :func:`filter <pykube.query.BaseQuery.filter>` method.
The ``selector`` parameter can take a dictionary of label names and values to filter by:

.. code-block:: python

    for pod in Pod.objects(api).filter(namespace=pykube.all, selector={'app': 'myapp'}):
         print(pod.namespace, pod.name)

Note that the special value of ``pykube.all`` needs to be passed, otherwise it would only return pods in the current namespace (i.e. usually "default").
