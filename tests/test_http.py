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
CONFIG_WITH_INSECURE_SKIP_TLS_VERIFY = os.path.sep.join(["tests", "test_config_with_insecure_skip_tls_verify.yaml"])
CONFIG_WITH_OIDC_AUTH = os.path.sep.join(["tests", "test_config_with_oidc_auth.yaml"])


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


def test_http_with_dry_run(monkeypatch):
    cfg = KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)
    api = HTTPClient(cfg, dry_run=True)

    mock_send = MagicMock()
    mock_send.side_effect = Exception('MOCK HTTP')
    monkeypatch.setattr('pykube.http.KubernetesHTTPAdapter._do_send', mock_send)

    with pytest.raises(Exception):
        api.get(url='test')

    mock_send.assert_called_once()
    # check that dry run http parameters were set
    assert mock_send.call_args[0][0].url == "http://localhost/api/v1/test?dryRun=All"


def test_http_insecure_skip_tls_verify(monkeypatch):
    cfg = KubeConfig.from_file(CONFIG_WITH_INSECURE_SKIP_TLS_VERIFY)
    api = HTTPClient(cfg)

    mock_send = MagicMock()
    mock_send.side_effect = Exception('MOCK HTTP')
    monkeypatch.setattr('pykube.http.KubernetesHTTPAdapter._do_send', mock_send)

    with pytest.raises(Exception):
        api.get(url='test')

    mock_send.assert_called_once()
    # check that SSL is not verified
    assert not mock_send.call_args[1]['verify']


def test_http_do_not_overwrite_auth(monkeypatch):
    cfg = KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)
    api = HTTPClient(cfg)

    mock_send = MagicMock()
    mock_send.side_effect = Exception('MOCK HTTP')
    monkeypatch.setattr('pykube.http.KubernetesHTTPAdapter._do_send', mock_send)

    with pytest.raises(Exception):
        api.get(url='test', headers={'Authorization': 'Bearer testtoken'})

    mock_send.assert_called_once()
    assert mock_send.call_args[0][0].headers['Authorization'] == 'Bearer testtoken'


def test_http_with_oidc_auth(monkeypatch):
    cfg = KubeConfig.from_file(CONFIG_WITH_OIDC_AUTH)
    api = HTTPClient(cfg)

    mock_send = MagicMock()
    mock_send.side_effect = Exception('MOCK HTTP')
    monkeypatch.setattr('pykube.http.KubernetesHTTPAdapter._do_send', mock_send)

    with pytest.raises(Exception):
        api.get(url='test')

    mock_send.assert_called_once()
    assert mock_send.call_args[0][0].headers['Authorization'] == 'Bearer some-id-token'
