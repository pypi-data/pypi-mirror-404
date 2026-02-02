"""AIR SDK - Python client for the AIR Backend API."""

from .client import AIR
from .project import Project
from .exceptions import AIRError, AuthError, ExecutionError, TaskTimeoutError, WebSocketError
from .ws_session import OneShotResult
from .executor import FileInfo

__version__ = "0.1.2"

__all__ = [
    "AIR",
    "Project",
    "AIRError",
    "AuthError",
    "ExecutionError",
    "TaskTimeoutError",
    "WebSocketError",
    "OneShotResult",
    "FileInfo",
]
