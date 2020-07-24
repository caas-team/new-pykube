=======================
How to access a Service
=======================

To access the service defined with your ``Service`` object, you can use the HTTP proxy provided by the API server.
There are convenience methods to do ``GET``, ``POST``, ``PUT`` and ``DELETE`` and the generic ``proxy_http_request`` version,
where you can pass any HTTP verb.

.. code-block:: python

    service = pykube.Service.objects(api).filter(namespace="default").get(name="test")
    res = service.proxy_http_get("my/path")
    assert res is not None
    assert res.content == b"it works"
    assert res.status_code == 200
