================================
How to update a Deployment image
================================

To update the Docker image for an existing deployment:

.. code-block:: python

    from pykube import Deployment, HTTPClient, KubeConfig

    new_docker_image = "hjacobs/kube-web-view"

    api = HTTPClient(KubeConfig.from_file())
    deploy = Deployment.objects(api).get(name="mydeploy")
    deploy.obj["spec"]["template"]["spec"]["containers"][0]["image"] = new_docker_image
    deploy.update()

Note that the call to ``deploy.update()`` might fail if the resource was modified between loading and updating.
In this case you need to retry.
