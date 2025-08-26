# pykube.config unittests
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from . import TestCase
from pykube import config
from pykube import exceptions
from pykube.config import BytesOrFile

CERT_DUMMY = b"dummy"

BASEDIR = Path("tests")
GOOD_CONFIG_FILE_PATH = BASEDIR / "test_config.yaml"
DEFAULTUSER_CONFIG_FILE_PATH = BASEDIR / "test_config_default_user.yaml"


def test_from_service_account_no_file(tmpdir):
    with pytest.raises(FileNotFoundError):
        config.KubeConfig.from_service_account(path=str(tmpdir))


def test_from_service_account(tmpdir):
    namespace_file = Path(tmpdir) / "namespace"
    token_file = Path(tmpdir) / "token"
    ca_file = Path(tmpdir) / "ca.crt"

    with namespace_file.open("w") as fd:
        fd.write("mynamespace")

    with token_file.open("w") as fd:
        fd.write("mytok")

    with ca_file.open("w") as fd:
        fd.write("myca")

    os.environ["KUBERNETES_SERVICE_HOST"] = "127.0.0.1"
    os.environ["KUBERNETES_SERVICE_PORT"] = "9443"

    cfg = config.KubeConfig.from_service_account(path=str(tmpdir))

    assert cfg.doc["clusters"][0]["cluster"] == {
        "server": "https://127.0.0.1:9443",
        "certificate-authority": str(ca_file),
    }
    assert cfg.doc["users"][0]["user"]["token"] == "mytok"
    assert cfg.namespace == "mynamespace"


def test_from_url():
    cfg = config.KubeConfig.from_url("http://localhost:8080")
    assert cfg.doc["clusters"][0]["cluster"] == {"server": "http://localhost:8080"}
    assert "users" not in cfg.doc


@pytest.fixture
def kubeconfig(tmpdir):
    kubeconfig = tmpdir.join("kubeconfig")
    kubeconfig.write(
        """
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
    """
    )
    return kubeconfig


@pytest.mark.parametrize(
    "kubeconfig_env,expected_path",
    [(None, "~/.kube/config"), ("/some/path", "/some/path")],
)
def test_from_default_kubeconfig(
    kubeconfig_env, expected_path, monkeypatch, kubeconfig
):
    mock = MagicMock()
    mock.return_value.expanduser.return_value = Path(kubeconfig)
    monkeypatch.setattr(config, "Path", mock)

    if kubeconfig_env is None:
        monkeypatch.delenv("KUBECONFIG", raising=False)
    else:
        monkeypatch.setenv("KUBECONFIG", kubeconfig_env)

    cfg = config.KubeConfig.from_file()
    mock.assert_called_with(expected_path)
    assert cfg.doc["clusters"][0]["cluster"] == {"server": "https://localhost:9443"}


class TestConfig(TestCase):
    def setUp(self):
        self.cfg = config.KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)

    def tearDown(self):
        self.cfg = None

    def test_init(self):
        """
        Test Config instance creation.
        """
        # Ensure that a valid creation works
        self.assertEqual(GOOD_CONFIG_FILE_PATH, self.cfg.filepath)

        # Ensure that if a file does not exist the creation fails
        self.assertRaises(
            exceptions.PyKubeError, config.KubeConfig.from_file, "doesnotexist"
        )

    def test_cert_temp_file_creation(self):
        """
        Verify the certificate data in the config is written to /tmp without leaks.
        https://codeberg.org/hjacobs/pykube-ng/issues/3
        """
        self.cfg.set_current_context("thename")

        num_cert_files = len(
            {
                self.cfg.cluster["certificate-authority"].filename(),
                self.cfg.cluster["certificate-authority"].filename(),
                self.cfg.cluster["certificate-authority"].filename(),
            }
        )

        self.assertEqual(1, num_cert_files)

    def test_set_current_context(self):
        """
        Verify set_current_context works as expected.
        """
        self.cfg.set_current_context("new_context")
        self.assertEqual("new_context", self.cfg.current_context)

    def test_clusters(self):
        """
        Verify clusters works as expected.
        """
        self.assertEqual(
            "http://localhost",
            self.cfg.clusters.get("thecluster", {}).get("server", None),
        )
        self.assertEqual(
            CERT_DUMMY,
            self.cfg.clusters.get("thecluster", {})
            .get("certificate-authority", {"_bytes": None})
            ._bytes,
        )

    def test_users(self):
        """
        Verify users works as expected.
        """
        self.__validate_user_certs(self.cfg.users.get("admin", {}))

    def test_contexts(self):
        """
        Verify contexts works as expected.
        """
        self.assertEqual(
            {"cluster": "thecluster", "user": "admin"},
            self.cfg.contexts.get("thename", None),
        )

    def test_cluster(self):
        """
        Verify cluster works as expected.
        """
        # Without a current_context this should fail
        try:
            cluster = self.cfg.cluster
            self.fail(
                "cluster was found without a current context set: {}".format(cluster)
            )
        except exceptions.PyKubeError:
            # We should get an error
            pass

        self.cfg.set_current_context("thename")
        self.assertEqual("http://localhost", self.cfg.cluster.get("server", None))
        self.assertEqual(
            CERT_DUMMY,
            self.cfg.cluster.get("certificate-authority", {"_bytes": None})._bytes,
        )

    def test_user(self):
        """
        Verify user works as expected.
        """
        # Without a current_context this should fail
        try:
            user = self.cfg.user
            self.fail("user was found without a current context set: {}".format(user))
        except exceptions.PyKubeError:
            # We should get an error
            pass

        self.cfg.set_current_context("thename")
        self.__validate_user_certs(self.cfg.user)

    def test_default_user(self):
        """
        User can sometimes be specified as 'default' with no corresponding definition
        """
        test_config = config.KubeConfig.from_file(DEFAULTUSER_CONFIG_FILE_PATH)
        test_config.set_current_context("a_context")
        self.assertIsNotNone(test_config.user)

    def test_namespace(self):
        self.cfg.set_current_context("thename")
        self.assertEqual("default", self.cfg.namespace)
        self.cfg.set_current_context("context_with_namespace")
        self.assertEqual("foospace", self.cfg.namespace)

    def __validate_user_certs(self, d: dict):
        key = d["client-key"]
        data = d["client-certificate"]

        self.assertIsInstance(data, BytesOrFile)
        self.assertIsInstance(key, BytesOrFile)

        self.assertEqual(CERT_DUMMY, data._bytes)
        self.assertEqual(CERT_DUMMY, key._bytes)
