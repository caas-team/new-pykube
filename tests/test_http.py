"""
pykube.http unittests
"""

import os
import pytest

from unittest.mock import MagicMock

from pykube import __version__
from pykube.http import HTTPClient, DEFAULT_HTTP_TIMEOUT
from pykube.config import KubeConfig

GOOD_CONFIG_FILE_PATH = os.path.sep.join(["tests", "test_config_with_context.yaml"])


def test_http(monkeypatch):
    cfg = KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)
    api = HTTPClient(cfg)

    mock_send = MagicMock()
    mock_send.side_effect = Exception('MOCK HTTP')
    monkeypatch.setattr('pykube.http.KubernetesHTTPAdapter._do_send', mock_send)

    with pytest.raises(Exception):
        api.get(url='test')

    mock_send.assert_called_once()
    assert mock_send.call_args[0][0].headers['Authorization'] == 'Basic YWRtOnNvbWVwYXNzd29yZA=='
    assert mock_send.call_args[0][0].headers['User-Agent'] == f'pykube-ng/{__version__}'
    # check that the default HTTP timeout was set
    assert mock_send.call_args[1]['timeout'] == DEFAULT_HTTP_TIMEOUT
