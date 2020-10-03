"""
Python client for Kubernetes
"""

__version__ = "20.10.0"

from .config import KubeConfig  # noqa: F401
from .exceptions import KubernetesError, PyKubeError, ObjectDoesNotExist  # noqa: F401
from .http import HTTPClient  # noqa: F401
from .objects import (  # noqa: F401
    object_factory,
    ConfigMap,
    CronJob,
    CustomResourceDefinition,
    DaemonSet,
    Deployment,
    Endpoint,
    Event,
    HorizontalPodAutoscaler,
    Ingress,
    Job,
    LimitRange,
    Namespace,
    Node,
    PersistentVolume,
    PersistentVolumeClaim,
    Pod,
    PodDisruptionBudget,
    PodSecurityPolicy,
    ReplicationController,
    ReplicaSet,
    ResourceQuota,
    Secret,
    Service,
    ServiceAccount,
    StatefulSet,
    Role,
    ClusterRole,
    RoleBinding,
    ClusterRoleBinding,
)
from .query import now, all_ as all, everything  # noqa: F401
