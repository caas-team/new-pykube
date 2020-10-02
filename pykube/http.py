"""
HTTP request related code.
"""
import base64
import datetime
import json
import logging
import os
import shlex
import subprocess
from typing import Optional

try:
    import google.auth
    from google.auth.transport.requests import Request as GoogleAuthRequest

    google_auth_installed = True
except ImportError:
    google_auth_installed = False
try:
    from requests_oauthlib import OAuth2Session

    oidc_auth_installed = True
except ImportError:
    oidc_auth_installed = False

import requests.adapters

from http import HTTPStatus
from urllib.parse import urlparse

from .exceptions import HTTPError, PyKubeError
from .utils import jsonpath_installed, jsonpath_parse, join_url_path
from .config import KubeConfig

from . import __version__

DEFAULT_HTTP_TIMEOUT = 10  # seconds
EXPIRY_SKEW_PREVENTION_DELAY = datetime.timedelta(minutes=5)
UTC = datetime.timezone.utc
LOG = logging.getLogger(__name__)


class KubernetesHTTPAdapter(requests.adapters.HTTPAdapter):

    # _do_send: the actual send method of HTTPAdapter
    # it can be overwritten in unit tests to mock the actual HTTP calls
    _do_send = requests.adapters.HTTPAdapter.send

    def __init__(self, kube_config: KubeConfig, **kwargs):
        self.kube_config = kube_config

        super().__init__(**kwargs)

    def _persist_credentials(self, config, opts):
        user_name = config.contexts[config.current_context]["user"]
        user = [u["user"] for u in config.doc["users"] if u["name"] == user_name][0]
        auth_config = user["auth-provider"].setdefault("config", {})
        auth_config.update(opts)
        config.persist_doc()
        config.reload()

    def _auth_gcp(self, request, token, expiry, config):
        original_request = request.copy()

        credentials = google.auth.default(
            scopes=[
                "https://www.googleapis.com/auth/cloud-platform",
                "https://www.googleapis.com/auth/userinfo.email",
            ]
        )[0]
        credentials.token = token
        credentials.expiry = expiry

        should_persist = not credentials.valid

        auth_request = GoogleAuthRequest()
        credentials.before_request(
            auth_request, request.method, request.url, request.headers
        )

        if should_persist and config:
            auth_opts = {
                "access-token": credentials.token,
                "expiry": credentials.expiry,
            }
            self._persist_credentials(config, auth_opts)

        def retry(send_kwargs):
            credentials.refresh(auth_request)
            response = self.send(original_request, **send_kwargs)
            if response.ok and config:
                auth_opts = {
                    "access-token": credentials.token,
                    "expiry": credentials.expiry,
                }
                self._persist_credentials(config, auth_opts)
            return response

        return retry

    def _is_valid_jwt(self, token):
        """Validate JWT token for correctness and near expiration"""
        if not token:
            return False
        reserved_characters = frozenset(["=", "+", "/"])
        if any(char in token for char in reserved_characters):
            # Invalid jwt, as it contains url-unsafe chars
            return False
        parts = token.split(".")
        if len(parts) != 3:  # Not a valid JWT
            return False
        padding = (4 - len(parts[1]) % 4) * "="
        if len(padding) == 3:
            # According to spec, 3 padding characters cannot occur
            # in a valid jwt
            # https://tools.ietf.org/html/rfc7515#appendix-C
            return False
        jwt_attributes = json.loads(
            base64.b64decode(parts[1] + padding).decode("utf-8")
        )
        expire = jwt_attributes.get("exp")
        # allow missing exp, but deny tokens that are about to expire soon
        return expire is None or (
            datetime.datetime.fromtimestamp(expire, tz=UTC)
            - EXPIRY_SKEW_PREVENTION_DELAY
        ) > datetime.datetime.utcnow().replace(tzinfo=UTC)

    def _refresh_oidc_token(self, config):
        if not oidc_auth_installed:
            raise ImportError(
                "missing dependencies for OIDC token refresh support "
                "(try pip install pykube-ng[oidc]"
            )
        auth_config = config.user["auth-provider"]["config"]
        if "idp-certificate-authority" in auth_config:
            verify = auth_config["idp-certificate-authority"].filename()
        else:
            verify = None
        oauth = OAuth2Session()
        discovery = oauth.get(
            f"{auth_config['idp-issuer-url']}/.well-known/openid-configuration",
            verify=verify,
            timeout=DEFAULT_HTTP_TIMEOUT,
            withhold_token=True,
        )

        if discovery.status_code != HTTPStatus.OK:
            raise PyKubeError(
                f"Failed to discover OpenID token endpoint - "
                f"HTTP {discovery.status_code}: {discovery.text}"
            )
        discovery = discovery.json()
        refresh = oauth.refresh_token(
            token_url=discovery["token_endpoint"],
            refresh_token=auth_config["refresh-token"],
            client_id=auth_config["client-id"],
            client_secret=auth_config.get("client-secret"),
            verify=verify,
            timeout=DEFAULT_HTTP_TIMEOUT,
        )
        auth_opts = {
            "id-token": refresh["id_token"],
            "refresh-token": refresh["refresh_token"],
        }
        self._persist_credentials(config, auth_opts)

    def send(self, request, **kwargs):
        if "kube_config" in kwargs:
            config = kwargs.pop("kube_config")
        else:
            config = self.kube_config

        _retry_attempt = kwargs.pop("_retry_attempt", 0)
        retry_func = self._setup_request_auth(config, request, kwargs)
        self._setup_request_certificates(config, request, kwargs)

        response = self._do_send(request, **kwargs)

        _retry_status_codes = {HTTPStatus.UNAUTHORIZED}

        if (
            response.status_code in _retry_status_codes
            and retry_func
            and _retry_attempt < 2
        ):
            send_kwargs = {"_retry_attempt": _retry_attempt + 1, "kube_config": config}
            send_kwargs.update(kwargs)
            return retry_func(send_kwargs=send_kwargs)

        return response

    def _setup_request_auth(self, config, request, kwargs):
        """
        Set up authorization for the request.

        Return an optional function to use as a retry manager if the initial request fails
        with an unauthorized error.
        """
        if "Authorization" in request.headers:
            # request already has some auth header (e.g. Bearer token)
            # don't modify/overwrite it
            return None

        if config.user.get("token"):
            request.headers["Authorization"] = "Bearer {}".format(config.user["token"])
            return None

        if "exec" in config.user:
            exec_conf = config.user["exec"]

            api_version = exec_conf["apiVersion"]
            if api_version == "client.authentication.k8s.io/v1alpha1":
                cmd_env_vars = dict(os.environ)
                for env_var in exec_conf.get("env") or []:
                    cmd_env_vars[env_var["name"]] = env_var["value"]

                output = subprocess.check_output(
                    [exec_conf["command"]] + exec_conf["args"], env=cmd_env_vars
                )

                parsed_out = json.loads(output)
                token = parsed_out["status"]["token"]
            else:
                raise NotImplementedError(
                    f"auth exec api version {api_version} not implemented"
                )

            request.headers["Authorization"] = "Bearer {}".format(token)
            return None

        if config.user.get("username") and config.user.get("password"):
            request.prepare_auth((config.user["username"], config.user["password"]))
            return None

        if "auth-provider" in config.user:
            auth_provider = config.user["auth-provider"]
            if auth_provider.get("name") == "gcp":
                dependencies = [google_auth_installed, jsonpath_installed]
                if not all(dependencies):
                    raise ImportError(
                        "missing dependencies for GCP support (try pip install pykube-ng[gcp]"
                    )
                auth_config = auth_provider.get("config", {})
                if "cmd-path" in auth_config:
                    output = subprocess.check_output(
                        [auth_config["cmd-path"]] + shlex.split(auth_config["cmd-args"])
                    )
                    parsed = json.loads(output)
                    token = jsonpath_parse(auth_config["token-key"], parsed)
                    expiry = datetime.datetime.strptime(
                        jsonpath_parse(auth_config["expiry-key"], parsed),
                        "%Y-%m-%dT%H:%M:%SZ",
                    )
                    retry_func = self._auth_gcp(request, token, expiry, None)
                else:
                    retry_func = self._auth_gcp(
                        request,
                        auth_config.get("access-token"),
                        auth_config.get("expiry"),
                        config,
                    )
                return retry_func
            elif auth_provider.get("name") == "oidc":
                auth_config = auth_provider.get("config", {})
                if not self._is_valid_jwt(auth_config.get("id-token")):
                    try:
                        self._refresh_oidc_token(config)
                    # ignoring all exceptions, rely on retries
                    except Exception as oidc_exc:
                        LOG.warning(f"Failed to refresh OpenID token: {oidc_exc}")

                # not using auth_config handle here as the config might have
                # been reloaded during token refresh
                request.headers["Authorization"] = "Bearer {}".format(
                    config.user["auth-provider"]["config"]["id-token"]
                )

        return None

    def _setup_request_certificates(self, config, request, kwargs):
        if "client-certificate" in config.user:
            kwargs["cert"] = (
                config.user["client-certificate"].filename(),
                config.user["client-key"].filename(),
            )
        # setup certificate verification
        if "certificate-authority" in config.cluster:
            kwargs["verify"] = config.cluster["certificate-authority"].filename()
        elif "insecure-skip-tls-verify" in config.cluster:
            kwargs["verify"] = not config.cluster["insecure-skip-tls-verify"]


class HTTPClient:
    """
    Client for interfacing with the Kubernetes API.
    """

    http_adapter_cls = KubernetesHTTPAdapter

    def __init__(
        self,
        config: KubeConfig,
        timeout: float = DEFAULT_HTTP_TIMEOUT,
        dry_run: bool = False,
        verify: bool = True,
        http_adapter: Optional[requests.adapters.HTTPAdapter] = None,
    ):
        """
        Creates a new instance of the HTTPClient.

        :Parameters:
           - `config`: The configuration instance
        """
        self.config = config
        self.timeout = timeout
        self.url = self.config.cluster["server"]
        self.dry_run = dry_run

        session = requests.Session()
        session.headers["User-Agent"] = f"pykube-ng/{__version__}"
        if not http_adapter:
            http_adapter = self.http_adapter_cls(self.config)
        session.mount("https://", http_adapter)
        session.mount("http://", http_adapter)
        self.session = session
        self.session.verify = verify

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        pr = urlparse(value)
        self._url = pr.geturl()

    @property
    def version(self):
        """
        Get Kubernetes API version
        """
        response = self.get(version="", base="/version")
        response.raise_for_status()
        data = response.json()
        return (data["major"], data["minor"])

    def resource_list(self, api_version):
        cached_attr = f"_cached_resource_list_{api_version}"
        if not hasattr(self, cached_attr):
            r = self.get(version=api_version)
            r.raise_for_status()
            setattr(self, cached_attr, r.json())
        return getattr(self, cached_attr)

    def get_kwargs(self, **kwargs) -> dict:
        """
        Creates a full URL to request based on arguments.

        :Parametes:
           - `kwargs`: All keyword arguments to build a kubernetes API endpoint
        """
        version = kwargs.pop("version", "v1")
        if version == "v1":
            base = kwargs.pop("base", "/api")
        elif "/" in version:
            base = kwargs.pop("base", "/apis")
        else:
            if "base" not in kwargs:
                raise TypeError("unknown API version; base kwarg must be specified.")
            base = kwargs.pop("base")
        if version.startswith("/"):
            # for compatibility with pykube-ng 20.1.0 when calling api.get(version="/apis"):
            # posixpath.join() was throwing away everything before the first "absolute" path (i.e. starting with a slash)
            bits = [version]
        else:
            bits = [base, version]
        # Overwrite (default) namespace from context if it was set
        if "namespace" in kwargs:
            n = kwargs.pop("namespace")
            if n is not None:
                if n:
                    namespace = n
                else:
                    namespace = self.config.namespace
                if namespace:
                    bits.extend(["namespaces", namespace])
        url = kwargs.get("url", "")
        bits.append(url)
        kwargs["url"] = self.url + join_url_path(*bits, join_empty=True)
        if "timeout" not in kwargs:
            # apply default HTTP timeout
            kwargs["timeout"] = self.timeout
        if self.dry_run:
            # Add http query param for dryRun
            params = kwargs.get("params", {})
            params["dryRun"] = "All"
            kwargs["params"] = params
        return kwargs

    def raise_for_status(self, resp):
        try:
            resp.raise_for_status()
        except Exception:
            # attempt to provide a more specific exception based around what
            # Kubernetes returned as the error.
            if resp.headers["content-type"] == "application/json":
                payload = resp.json()
                if payload["kind"] == "Status":
                    raise HTTPError(resp.status_code, payload["message"])
            raise

    def request(self, *args, **kwargs):
        """
        Makes an API request based on arguments.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.request(*args, **self.get_kwargs(**kwargs))

    def get(self, *args, **kwargs):
        """
        Executes an HTTP GET.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.get(*args, **self.get_kwargs(**kwargs))

    def options(self, *args, **kwargs):
        """
        Executes an HTTP OPTIONS.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.options(*args, **self.get_kwargs(**kwargs))

    def head(self, *args, **kwargs):
        """
        Executes an HTTP HEAD.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.head(*args, **self.get_kwargs(**kwargs))

    def post(self, *args, **kwargs):
        """
        Executes an HTTP POST.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.post(*args, **self.get_kwargs(**kwargs))

    def put(self, *args, **kwargs):
        """
        Executes an HTTP PUT.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.put(*args, **self.get_kwargs(**kwargs))

    def patch(self, *args, **kwargs):
        """
        Executes an HTTP PATCH.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.patch(*args, **self.get_kwargs(**kwargs))

    def delete(self, *args, **kwargs):
        """
        Executes an HTTP DELETE.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.delete(*args, **self.get_kwargs(**kwargs))
