How to use the Interactive Console
==================================

Pykube can be started as an interactive Python console:

.. code-block:: bash

     python3 -m pykube

The interactive console automatically loads the Kubernetes configuration from the default location (``~/.kube/config``) and
provides the objects ``api`` and ``config``:

.. code-block:: python

     >>> api
     <pykube.http.HTTPClient object at 0x7f2112263160>

     >>> config
     <pykube.config.KubeConfig object at 0x7f6631bbc2e8>

All standard classes from :ref:`pykube-package` are automatically imported, so you can use them, e.g.:

.. code-block:: python

    >>> for deploy in Deployment.objects(api):
    ...     print(f'{deploy.name}: {deploy.replicas}')

You can also pass a Python command via the ``-c`` option for non-interactive usage:

.. code-block:: bash

    python3 -m pykube -c 'print(config.current_context, api.version)'
