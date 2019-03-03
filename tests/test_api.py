import json
import pytest
import responses

from pykube import KubeConfig, HTTPClient, Deployment


@pytest.fixture
def kubeconfig(tmpdir):
    kubeconfig = tmpdir.join('kubeconfig')
    kubeconfig.write('''
apiVersion: v1
clusters:
- cluster: {server: 'https://localhost:9443'}
  name: test
contexts:
- context: {cluster: test, user: test}
  name: test
current-context: test
kind: Config
preferences: {}
users:
- name: test
  user: {token: testtoken}
    ''')
    return kubeconfig


@pytest.fixture
def requests_mock():
    return responses.RequestsMock(target='pykube.http.KubernetesHTTPAdapter._do_send')


def test_list_deployments(kubeconfig, monkeypatch, requests_mock):
    config = KubeConfig.from_file(str(kubeconfig))
    api = HTTPClient(config)

    with requests_mock as rsps:
        rsps.add(responses.GET, 'https://localhost:9443/apis/apps/v1/namespaces/default/deployments',
                 json={'items': []})

        assert list(Deployment.objects(api)) == []
        assert len(rsps.calls) == 1
        # ensure that we passed the token specified in kubeconfig..
        assert rsps.calls[0].request.headers['Authorization'] == 'Bearer testtoken'


def test_list_and_update_deployments(kubeconfig, monkeypatch, requests_mock):
    config = KubeConfig.from_file(str(kubeconfig))
    api = HTTPClient(config)

    with requests_mock as rsps:
        rsps.add(responses.GET, 'https://localhost:9443/apis/apps/v1/namespaces/default/deployments',
                 json={'items': [{'metadata': {'name': 'deploy-1'}, 'spec': {'replicas': 3}}]})

        deployments = list(Deployment.objects(api))
        assert len(deployments) == 1
        deploy = deployments[0]
        assert deploy.name == 'deploy-1'
        assert deploy.namespace == 'default'
        assert deploy.replicas == 3

        deploy.replicas = 2

        rsps.add(responses.PATCH, 'https://localhost:9443/apis/apps/v1/namespaces/default/deployments/deploy-1',
                 json={'items': [{'metadata': {'name': 'deploy-1'}, 'spec': {'replicas': 2}}]})

        deploy.update()
        assert len(rsps.calls) == 2

        assert json.loads(rsps.calls[-1].request.body) == {"metadata": {"name": "deploy-1"}, "spec": {"replicas": 2}}
