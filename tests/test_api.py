import json
import operator
import pytest
import responses

import pykube
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


@pytest.fixture
def api(kubeconfig):
    config = KubeConfig.from_file(str(kubeconfig))
    return HTTPClient(config)


def test_get_ready_pods(api, requests_mock):
    # example from README
    with requests_mock as rsps:
        rsps.add(responses.GET, 'https://localhost:9443/api/v1/namespaces/gondor-system/pods',
                 json={'items': [
                      {'metadata': {'name': 'pod-1'}, 'status': {}},
                      {'metadata': {'name': 'pod-2'}, 'status': {'conditions': [{'type': 'Ready', 'status': 'True'}]}}
                 ]})
        pods = pykube.Pod.objects(api).filter(namespace="gondor-system")
        ready_pods = list(filter(operator.attrgetter("ready"), pods))
        assert len(ready_pods) == 1
        assert ready_pods[0].name == 'pod-2'


def test_get_pod_by_name(api, requests_mock):
    # example from README
    with requests_mock as rsps:
        rsps.add(responses.GET, 'https://localhost:9443/api/v1/namespaces/gondor-system/pods/my-pod',
                 json={'spec': {'containers': [{'image': 'hjacobs/kube-janitor'}]}})
        rsps.add(responses.GET, 'https://localhost:9443/api/v1/namespaces/gondor-system/pods/other-pod',
                 status=404)

        pod = pykube.Pod.objects(api).filter(namespace="gondor-system").get(name="my-pod")
        assert pod.obj["spec"]["containers"][0]["image"] == 'hjacobs/kube-janitor'

        pod = pykube.Pod.objects(api).filter(namespace="gondor-system").get_or_none(name="my-pod")
        assert pod.obj["spec"]["containers"][0]["image"] == 'hjacobs/kube-janitor'

        pod = pykube.Pod.objects(api).filter(namespace="gondor-system").get_or_none(name="other-pod")
        assert pod is None


def test_selector_query(api, requests_mock):
    # example from README
    with requests_mock as rsps:
        rsps.add(responses.GET, 'https://localhost:9443/api/v1/namespaces/gondor-system/pods?labelSelector=gondor.io%2Fname+in+%28api-web%2Capi-worker%29',
                 json={'items': [{'meta': {}}]})

        pods = pykube.Pod.objects(api).filter(
            namespace="gondor-system",
            selector={"gondor.io/name__in": {"api-web", "api-worker"}},
        )
        assert len(list(pods)) == 1

        rsps.add(responses.GET, 'https://localhost:9443/api/v1/namespaces/default/pods?fieldSelector=status.phase%3DPending',
                 json={'items': [{'meta': {}}]})

        pending_pods = pykube.objects.Pod.objects(api).filter(
            field_selector={"status.phase": "Pending"}
        )

        assert len(list(pending_pods)) == 1


def test_list_deployments(api, requests_mock):
    with requests_mock as rsps:
        rsps.add(responses.GET, 'https://localhost:9443/apis/apps/v1/namespaces/default/deployments',
                 json={'items': []})

        assert list(Deployment.objects(api)) == []
        assert len(rsps.calls) == 1
        # ensure that we passed the token specified in kubeconfig..
        assert rsps.calls[0].request.headers['Authorization'] == 'Bearer testtoken'


def test_list_and_update_deployments(api, requests_mock):
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
