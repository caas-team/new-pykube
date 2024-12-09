# pykube.http unittests
import os
from pathlib import Path
from unittest import mock

import pytest

from pykube import __version__
from pykube.config import KubeConfig
from pykube.http import DEFAULT_HTTP_TIMEOUT
from pykube.http import HTTPClient


BASEDIR = Path("tests")
GOOD_CONFIG_FILE_PATH = BASEDIR / "test_config_with_context.yaml"
CONFIG_WITH_INSECURE_SKIP_TLS_VERIFY = (
    BASEDIR / "test_config_with_insecure_skip_tls_verify.yaml"
)
CONFIG_WITH_OVERRIDES = BASEDIR / "test_config_overrides.yaml"
CONFIG_WITH_OIDC_AUTH = BASEDIR / "test_config_with_oidc_auth.yaml"


def test_http(monkeypatch):
    cfg = KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)
    api = HTTPClient(cfg)

    mock_send = mock.MagicMock()
    mock_send.side_effect = Exception("MOCK HTTP")
    monkeypatch.setattr("pykube.http.KubernetesHTTPAdapter._do_send", mock_send)

    with pytest.raises(Exception):
        api.get(url="test")

    mock_send.assert_called_once()
    assert (
        mock_send.call_args[0][0].headers["Authorization"]
        == "Basic YWRtOnNvbWVwYXNzd29yZA=="
    )
    assert (
        mock_send.call_args[0][0].headers["User-Agent"] == f"new-pykube/{__version__}"
    )
    # check that the default HTTP timeout was set
    assert mock_send.call_args[1]["timeout"] == DEFAULT_HTTP_TIMEOUT


def test_http_with_dry_run(monkeypatch):
    cfg = KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)
    api = HTTPClient(cfg, dry_run=True)

    mock_send = mock.MagicMock()
    mock_send.side_effect = Exception("MOCK HTTP")
    monkeypatch.setattr("pykube.http.KubernetesHTTPAdapter._do_send", mock_send)

    with pytest.raises(Exception):
        api.get(url="test")

    mock_send.assert_called_once()
    # check that dry run http parameters were set
    assert mock_send.call_args[0][0].url == "http://localhost/api/v1/test?dryRun=All"


def test_http_insecure_skip_tls_verify(monkeypatch):
    cfg = KubeConfig.from_file(CONFIG_WITH_INSECURE_SKIP_TLS_VERIFY)
    api = HTTPClient(cfg)

    mock_send = mock.MagicMock()
    mock_send.side_effect = Exception("MOCK HTTP")
    monkeypatch.setattr("pykube.http.KubernetesHTTPAdapter._do_send", mock_send)

    with pytest.raises(Exception):
        api.get(url="test")

    mock_send.assert_called_once()
    # check that SSL is not verified
    assert not mock_send.call_args[1]["verify"]


def test_http_override_certificate_authority(monkeypatch):
    cfg = KubeConfig.from_file(CONFIG_WITH_OVERRIDES)
    api = HTTPClient(cfg, dry_run=True)

    k = mock.patch.dict(
        os.environ, {"PYKUBE_SSL_CERTIFICATE_AUTHORITY": "/var/foo/bar/ca"}
    )
    k.start()
    mock_send = mock.MagicMock()
    mock_send.side_effect = Exception("MOCK HTTP")
    monkeypatch.setattr("pykube.http.KubernetesHTTPAdapter._do_send", mock_send)

    with pytest.raises(Exception):
        api.get(url="test")

    mock_send.assert_called_once()
    # Check path to overwritten CA is used
    assert mock_send.call_args[1]["verify"] == "/var/foo/bar/ca"
    k.stop()


def test_http_do_not_overwrite_auth(monkeypatch):
    cfg = KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)
    api = HTTPClient(cfg)

    mock_send = mock.MagicMock()
    mock_send.side_effect = Exception("MOCK HTTP")
    monkeypatch.setattr("pykube.http.KubernetesHTTPAdapter._do_send", mock_send)

    with pytest.raises(Exception):
        api.get(url="test", headers={"Authorization": "Bearer testtoken"})

    mock_send.assert_called_once()
    assert mock_send.call_args[0][0].headers["Authorization"] == "Bearer testtoken"


def test_http_with_oidc_auth_no_refresh(monkeypatch):
    cfg = KubeConfig.from_file(CONFIG_WITH_OIDC_AUTH)
    api = HTTPClient(cfg)

    mock_send = mock.MagicMock()
    mock_send.side_effect = Exception("MOCK HTTP")
    monkeypatch.setattr("pykube.http.KubernetesHTTPAdapter._do_send", mock_send)

    with mock.patch(
        "pykube.http.KubernetesHTTPAdapter._is_valid_jwt", return_value=True
    ) as mock_jwt:
        with pytest.raises(Exception):
            api.get(url="test")
        mock_jwt.assert_called_once_with("some-id-token")

    mock_send.assert_called_once()
    assert mock_send.call_args[0][0].headers["Authorization"] == "Bearer some-id-token"


def test_get_kwargs():
    cfg = KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)
    api = HTTPClient(cfg)

    assert api.get_kwargs(version="v1") == {
        "timeout": 10,
        "url": "http://localhost/api/v1/",
    }
    assert api.get_kwargs(version="/apis") == {
        "timeout": 10,
        "url": "http://localhost/apis/",
    }
    assert api.get_kwargs(version="storage.k8s.io/v1") == {
        "timeout": 10,
        "url": "http://localhost/apis/storage.k8s.io/v1/",
    }
