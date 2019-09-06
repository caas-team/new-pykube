Changelog
=========

19.9.2
------

* add ``dry_run`` option to ``HTTPClient`` to only make `dry run requests <https://kubernetes.io/blog/2019/01/14/apiserver-dry-run-and-kubectl-diff/>`_

19.9.1
------

* support "oidc" auth type in KubeConfig (basic support with existing "id-token")

19.9.0
------

* changed to `Calendar Versioning <http://calver.org>`_
* add convenience function ``KubeConfig.from_env()`` to load KubeConfig from in-cluster ServiceAccount or local KUBECONFIG

0.30
----

* allow passing a custom ``Authorization header`` with ``HTTPClient.get(..., headers=..)`` without getting overwritten

0.28
----

* support tabular representation like what kubectl uses (``Query.as_table()`` method)

0.27
----

* allow passing arbitrary parameters to the ``watch`` query

0.26
----

* remember streaming response
* exclude "tests" from packaging

0.25
----

* add CustomResourceDefinition to top-level imports (allowing from pykube import CustomResourceDefinition)

0.24
----

* add ``CustomResourceDefinition`` class
* add ``patch`` method to APIObject class
* improve user-friendliness of ``object_factory``

0.23
----

* remove debug print statement

0.22
----

* fix GCP support

0.21
----

* add optional ``propagation_policy`` parameter to APIObject.delete(), see https://pykube.readthedocs.io/en/latest/api/pykube.html#pykube.objects.APIObject.delete

0.20
----

* Fix handling of annotations and labels if the object had none set before

0.19
----

* Added interactive console (invoke with ``python3 -m pykube``)

0.18
----

* Added ``PodDisruptionBudget``
* Added HTTP timeout (default: 10 seconds)

0.17
----

* New release as ``pykube-ng``
* Removed Python 2.7 compatibility
* Removed HTTPie plugin
* Added some tests
