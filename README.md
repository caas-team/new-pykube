# new-pykube

[![PyPI version](https://badge.fury.io/py/new-pykube.svg)](https://pypi.org/project/new-pykube)
[![Downloads](https://static.pepy.tech/badge/new-pykube/month)](https://github.com/caas-team/new-pykube/releases)
[![Python Test](https://github.com/caas-team/new-pykube/actions/workflows/python-tests.yml/badge.svg)](https://github.com/caas-team/new-pykube/actions/workflows/python-tests.yml)

Pykube (new-pykube) is a lightweight Python 3.10+ client library for Kubernetes.

This is a fork of the no longer maintained [pykube-ng](https://codeberg.org/hjacobs/pykube-ng).

## Features

- HTTP interface using requests using kubeconfig for authentication
- Python native querying of Kubernetes API objects

## Installation

To install pykube, use pip:

```bash
pip install new-pykube
```

## Interactive Console

The `pykube` library module can be run as an interactive console locally for quick exploration.
It will automatically load `~/.kube/config` to provide the `api` object, and it loads pykube classes (`Deployment`, `Pod`, ..) into local context:

```bash
python3 -m pykube
>>> [d.name for d in Deployment.objects(api)]
```

## Usage

### Query for all ready pods in a custom namespace:

```python
import operator
import pykube

api = pykube.HTTPClient(pykube.KubeConfig.from_file())
pods = pykube.Pod.objects(api).filter(namespace="gondor-system")
ready_pods = filter(operator.attrgetter("ready"), pods)
```

### Access any attribute of the Kubernetes object:

```python
pod = pykube.Pod.objects(api).filter(namespace="gondor-system").get(name="my-pod")
pod.obj["spec"]["containers"][0]["image"]
```

### Selector query:

```python
pods = pykube.Pod.objects(api).filter(
    namespace="gondor-system",
    selector={"gondor.io/name__in": {"api-web", "api-worker"}},
)
pending_pods = pykube.objects.Pod.objects(api).filter(
    field_selector={"status.phase": "Pending"}
)
```

### Watch query:

```python
watch = pykube.Job.objects(api, namespace="gondor-system")
watch = watch.filter(field_selector={"metadata.name": "my-job"}).watch()

# watch is a generator:
for watch_event in watch:
    print(watch_event.type) # 'ADDED', 'DELETED', 'MODIFIED'
    print(watch_event.object) # pykube.Job object
```

### Create a Deployment:

```python
obj = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": "my-deploy",
        "namespace": "gondor-system"
    },
    "spec": {
        "replicas": 3,
        "selector": {
            "matchLabels": {
                "app": "nginx"
            }
        },
        "template": {
            "metadata": {
                "labels": {
                    "app": "nginx"
                }
            },
            "spec": {
                "containers": [
                    {
                        "name": "nginx",
                        "image": "nginx",
                        "ports": [
                            {"containerPort": 80}
                        ]
                    }
                ]
            }
        }
    }
}
pykube.Deployment(api, obj).create()
```

### Delete a Deployment:

```python
obj = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": "my-deploy",
        "namespace": "gondor-system"
    }
}
pykube.Deployment(api, obj).delete()
```

### Check server version:

```python
api = pykube.HTTPClient(pykube.KubeConfig.from_file())
api.version
```

## Requirements

- Python 3.10+
- requests (included in `install_requires`)
- PyYAML (included in `install_requires`)

## Local Development

You can run pykube against your current kubeconfig context, e.g. local [Minikube](https://github.com/kubernetes/minikube):

```bash
poetry install
poetry run python3
>>> import pykube
>>> config = pykube.KubeConfig.from_file()
>>> api = pykube.HTTPClient(config)
>>> list(pykube.Deployment.objects(api))
```

To run PEP8 (flake8) checks and unit tests including coverage report:

```bash
make test
```

## License

The code in this project is licensed under the [Apache License, version 2.0](./LICENSE)

## Contributing

Easiest way to contribute is to provide feedback! We would love to hear what you like and what you think is missing.
Create an issue and we will take a look. PRs are welcome.

## Code of Conduct

In order to foster a kind, inclusive, and harassment-free community, this project follows the [Contributor Covenant Code of Conduct](http://contributor-covenant.org/version/1/4/).

## Acknowledgments

Thanks to [pykube-ng](https://codeberg.org/hjacobs/pykube-ng) project authored
by [Henning Jacobs](https://github.com/hjacobs).
