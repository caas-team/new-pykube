import pytest

from unittest.mock import MagicMock

from pykube import Pod, ObjectDoesNotExist

from pykube.query import Query


@pytest.fixture
def api():
    return MagicMock()


def test_get(api):
    with pytest.raises(ObjectDoesNotExist):
        Query(api, Pod).get(namespace='myns')


def test_get_one_object(api):
    response = MagicMock()
    response.json.return_value = {'items': [{'metadata': {'name': 'pod1'}}]}
    api.get.return_value = response
    pod = Query(api, Pod).get(namespace='myns')
    assert pod.name == 'pod1'


def test_get_more_than_one_object(api):
    response = MagicMock()
    response.json.return_value = {'items': [{'metadata': {'name': 'pod1'}}, {'metadata': {'name': 'pod2'}}]}
    api.get.return_value = response
    with pytest.raises(ValueError):
        Query(api, Pod).get(namespace='myns')


def test_filter_by_namespace(api):
    Query(api, Pod).filter(namespace='myns').execute()
    api.get.assert_called_once_with(namespace='myns', url='pods', version='v1')


def test_filter_by_labels_eq(api):
    Query(api, Pod).filter(selector={'application': 'myapp', 'component': 'backend'}).execute()
    api.get.assert_called_once_with(url='pods?labelSelector=application%3Dmyapp%2Ccomponent%3Dbackend', version='v1')


def test_filter_by_labels_neq(api):
    Query(api, Pod).filter(selector={'application__neq': 'myapp'}).execute()
    api.get.assert_called_once_with(url='pods?labelSelector=application+%21%3D+myapp', version='v1')


def test_filter_by_labels_in(api):
    Query(api, Pod).filter(selector={'application__in': ['foo', 'bar']}).execute()
    api.get.assert_called_once_with(url='pods?labelSelector=application+in+%28bar%2Cfoo%29', version='v1')


def test_filter_by_labels_notin(api):
    Query(api, Pod).filter(selector={'application__notin': ['foo', 'bar']}).execute()
    api.get.assert_called_once_with(url='pods?labelSelector=application+notin+%28bar%2Cfoo%29', version='v1')


def test_filter_invalid_selector(api):
    with pytest.raises(ValueError):
        Query(api, Pod).filter(selector={'application__x': 'foo'}).execute()


def test_filter_selector_string(api):
    Query(api, Pod).filter(selector='application=foo').execute()
    api.get.assert_called_once_with(url='pods?labelSelector=application%3Dfoo', version='v1')
