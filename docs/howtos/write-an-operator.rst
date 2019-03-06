How to write an Operator
========================

Pykube can be used to implement Kubernetes Operators. Here is how to write a very simple operator which adds a label ``foo`` with value ``bar`` to every deployment object which has the ``pykube-test-operator`` annotation:

.. code-block:: python

    # simplified example script, no error handling!
    import pykube, time

    while True:
        try:
            # running in cluster
            config = pykube.KubeConfig.from_service_account()
        except FileNotFoundError:
            # not running in cluster => load local ~/.kube/config for testing
            config = pykube.KubeConfig.from_file()
        api = pykube.HTTPClient(config)
        for deploy in pykube.Deployment.objects(api, namespace=pykube.all):
            if 'pykube-test-operator' in deploy.annotations:
                print(f'Updating deployment {deploy.namespace}/{deploy.name}..')
                deploy.labels['foo'] = 'bar'
                deploy.update()
        time.sleep(15)

Save the above Python script as ``main.py``.

Testing
-------

You can now test the script locally with Pipenv_ and Minikube_ (run ``minikube start`` first):

.. code-block:: bash

    pipenv install pykube-ng
    pipenv run python3 main.py

See the operator in action by creating a deployment with the right annotation:

.. code-block:: bash

    kubectl run nginx --image=nginx
    kubectl annotate deploy nginx pykube-test-operator=true

The operator should should now assign the ``foo`` label to the ``nginx`` deployment.

Building the Docker image
-------------------------

Create a ``Dockerfile`` in the same directory as ``main.py``:

.. code-block:: Dockerfile

    FROM python:3.7-alpine3.9

    WORKDIR /

    RUN pip3 install pykube-ng

    COPY main.py /

    ENTRYPOINT ["python3", "main.py"]

Now build it:

.. code-block:: bash

    docker build -t pykube-test-operator .

You need to push the Docker image to some Docker registry before you can deploy it.


Deployment
----------

Now deploy the Docker image to your Kubernetes cluster using a service account with the necessary permissions (in this case to list and update deployments).
To create such an service account with the necessary RBAC rights create ``rbac.yaml`` with these contents:

.. code-block:: yaml

    apiVersion: v1
    kind: ServiceAccount
    metadata:
      name: pykube-test-operator
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: ClusterRole
    metadata:
      name: pykube-test-operator
    rules:
    - apiGroups:
      - apps
      resources:
      - deployments
      verbs:
      - get
      - watch
      - list
      - update
      - patch
    ---
    apiVersion: rbac.authorization.k8s.io/v1
    kind: ClusterRoleBinding
    metadata:
      name: pykube-test-operator
    roleRef:
      apiGroup: rbac.authorization.k8s.io
      kind: ClusterRole
      name: pykube-test-operator
    subjects:
    - kind: ServiceAccount
      name: pykube-test-operator
      namespace: default

Apply the RBAC role via ``kubectl apply -f rbac.yaml``.

Finally, the deployment of the operator would then look like (``deployment.yaml``):

.. code-block:: yaml

    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: pykube-test-operator
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: pykube-test-operator
      template:
        metadata:
          labels:
            app: pykube-test-operator
        spec:
          serviceAccountName: pykube-test-operator
          containers:
          - name: operator
            # this image needs have been pushed to some Docker registry!
            image: pykube-test-operator
            resources:
              limits:
                memory: 50Mi
              requests:
                cpu: 5m
                memory: 50Mi
            securityContext:
              readOnlyRootFilesystem: true
              runAsNonRoot: true
              runAsUser: 1000

Create the deployment via ``kubectl apply -f deployment.yaml``.

You should now have a working operator deployment in your cluster.

.. _Pipenv: https://pipenv.readthedocs.io/en/latest/
.. _Minikube: https://github.com/kubernetes/minikube
