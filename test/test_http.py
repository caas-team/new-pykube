"""
pykube.http unittests
"""

import os
import pytest

from unittest.mock import MagicMock

from pykube.http import HTTPClient
from pykube.config import KubeConfig

GOOD_CONFIG_FILE_PATH = os.path.sep.join(["test", "test_config_with_context.yaml"])


def test_http(monkeypatch):
    cfg = KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)
    session = HTTPClient(cfg).session

    mock_send = MagicMock()
    mock_send.side_effect = Exception('MOCK HTTP')
    monkeypatch.setattr('requests.adapters.HTTPAdapter.send', mock_send)

    with pytest.raises(Exception):
        session.get('http://localhost:9090/test')

    mock_send.assert_called_once()
    assert mock_send.call_args[0][0].headers['Authorization'] == 'Basic YWRtOnNvbWVwYXNzd29yZA=='
