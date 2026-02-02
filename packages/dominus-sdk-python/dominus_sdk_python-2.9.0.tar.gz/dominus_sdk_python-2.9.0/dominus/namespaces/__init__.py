"""Dominus SDK Namespaces v2.8"""
from .secrets import SecretsNamespace
from .db import DbNamespace
from .redis import RedisNamespace
from .files import FilesNamespace
from .auth import AuthNamespace
from .ddl import DdlNamespace
from .logs import LogsNamespace
from .open import OpenNamespace
from .health import HealthNamespace
from .portal import PortalNamespace
from .courier import CourierNamespace
from .workflow import WorkflowNamespace
from .ai import (
    AiNamespace,
    RagSubNamespace,
    ArtifactsSubNamespace,
    ResultsSubNamespace,
    WorkflowSubNamespace,
)

__all__ = [
    "SecretsNamespace",
    "DbNamespace",
    "RedisNamespace",
    "FilesNamespace",
    "AuthNamespace",
    "DdlNamespace",
    "LogsNamespace",
    "OpenNamespace",
    "HealthNamespace",
    "PortalNamespace",
    "CourierNamespace",
    "WorkflowNamespace",
    "AiNamespace",
    "RagSubNamespace",
    "ArtifactsSubNamespace",
    "ResultsSubNamespace",
    "WorkflowSubNamespace",
]
