from typing import Dict, Any, Optional
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockFixture

import pykube
from pykube.objects import NamespacedAPIObject
from pykube.objects import Pod
from pykube.utils import obj_merge


def test_api_object():
    pod = Pod(None, {"metadata": {"name": "myname"}})
    assert repr(pod) == "<Pod myname>"
    assert str(pod) == "myname"
    assert pod.metadata == {"name": "myname"}
    assert pod.labels == {}
    assert pod.annotations == {}


def test_object_factory_succeeds():
    api = MagicMock()
    api.resource_list.return_value = {
        "resources": [
            {"kind": "ExampleObject", "namespaced": True, "name": "exampleobjects"}
        ]
    }
    ExampleObject = pykube.object_factory(api, "example.org/v1", "ExampleObject")
    assert ExampleObject.kind == "ExampleObject"
    assert ExampleObject.endpoint == "exampleobjects"
    assert ExampleObject.version == "example.org/v1"
    assert NamespacedAPIObject in ExampleObject.mro()


def test_object_factory_raises_for_unknown_kind():
    api = MagicMock()
    api.resource_list.return_value = {
        "resources": [
            {"kind": "ExampleObject", "namespaced": True, "name": "exampleobjects"}
        ]
    }
    with pytest.raises(ValueError):
        pykube.object_factory(api, "example.org/v1", "OtherObject")


def test_set_annotation():
    pod = Pod(None, {"metadata": {"name": "myname"}})
    pod.annotations["foo"] = "bar"
    assert pod.annotations["foo"] == "bar"


def test_set_label():
    pod = Pod(None, {"metadata": {"name": "myname"}})
    pod.labels["foo"] = "bar"
    assert pod.labels["foo"] == "bar"


def test_update():
    pod = Pod(
        None,
        {"metadata": {"name": "john", "kind": "test"}, "annotations": "a long string"},
    )
    pod.obj = {"metadata": {"name": "john"}}
    pod.api = MagicMock()
    pod.api.patch.return_value.json.return_value = obj_merge(
        pod.obj, pod._original_obj, False
    )
    pod.update(is_strategic=False)
    assert pod.metadata == {"name": "john"}
    assert pod.annotations == {}


@pytest.mark.parametrize(
    "port,expected_request_kwargs",
    [
        # empty port - default service port should be used
        (
                None,
                {"url": "services/test_service:9090/proxy//", "namespace": "test_namespace", "version": "v1"}
        ),
        # override the default port, should be included in url
        (
                8080,
                {"url": "services/test_service:8080/proxy//", "namespace": "test_namespace", "version": "v1"},
        ),
    ],
)
def test_service_proxy_http_request(mocker: MockFixture, port: Optional[int],
                                    expected_request_kwargs: Dict[str, Any]) -> None:
    mock_client = mocker.MagicMock(spec=pykube.http.HTTPClient)

    service = pykube.Service(mock_client, {
        "apiVersion": "core/v1",
        "kind": "Service",
        "metadata": {
            "name": "test_service",
            "namespace": "test_namespace",
        },
        "spec": {
            "ports": [
                {"port": 9090}
            ]
        }
    })
    service.proxy_http_request("GET", "/", port)

    request = mock_client.request
    assert request.called
    assert request.call_args_list[0][0] == ("GET",)
    assert request.call_args_list[0][1] == expected_request_kwargs
