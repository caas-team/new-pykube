import pykube


def test_api_object():
    pod = pykube.Pod(None, {'metadata': {'name': 'myname'}})
    assert repr(pod) == '<Pod myname>'
    assert str(pod) == 'myname'
    assert pod.metadata == {'name': 'myname'}
    assert pod.labels == {}
    assert pod.annotations == {}
