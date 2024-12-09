# pykube.http unittests
import copy
import logging
import tempfile

from . import TestCase

BASE_CONFIG = {
    "clusters": [
        {"name": "test-cluster", "cluster": {"server": "http://localhost:8080"}}
    ],
    "contexts": [
        {
            "name": "test-cluster",
            "context": {"cluster": "test-cluster", "user": "test-user"},
        }
    ],
    "users": [{"name": "test-user", "user": {}}],
    "current-context": "test-cluster",
}

_log = logging.getLogger(__name__)


class TestSession(TestCase):
    def setUp(self):
        self.config = copy.deepcopy(BASE_CONFIG)

    def test_build_session_auth_provider(self):
        """Test that HTTPClient correctly parses the auth-provider config.

        Observed in GKE with kubelet v1.3.
        """
        self.config.update(
            {
                "users": [
                    {
                        "name": "test-user",
                        "user": {
                            "auth-provider": {
                                "config": {
                                    "access-token": "abc",
                                    "expiry": "2016-08-24T16:19:17.19878675-07:00",
                                },
                            },
                        },
                    },
                ]
            }
        )

        gcloud_content = """
{
  "client_id": "myclientid",
  "client_secret": "myclientsecret",
  "refresh_token": "myrefreshtoken",
  "type": "authorized_user"
}

"""

        _log.info("Built config: %s", self.config)
        with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
            f.write(gcloud_content)
