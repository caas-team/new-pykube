import json
from unittest.mock import MagicMock

import pytest

from pykube import Pod
from pykube.query import Query


@pytest.fixture
def api():
    return MagicMock()


def test_watch_response_exists(api):
    stream = Query(api, Pod).watch()
    assert hasattr(stream, 'response')
    assert stream.response is None  # not yet executed


def test_watch_response_is_readonly(api):
    stream = Query(api, Pod).watch()
    with pytest.raises(AttributeError):
        stream.response = object()


def test_watch_response_is_set_on_iter(api):
    line1 = json.dumps({'type': 'ADDED', 'object': {}}).encode('utf-8')
    expected_response = MagicMock()
    expected_response.iter_lines.return_value = [line1]
    api.get.return_value = expected_response

    stream = Query(api, Pod).watch()
    next(iter(stream))

    assert stream.response is expected_response

    assert api.get.call_count == 1
    assert api.get.call_args_list[0][1]['stream'] is True
    assert 'watch=true' in api.get.call_args_list[0][1]['url']
