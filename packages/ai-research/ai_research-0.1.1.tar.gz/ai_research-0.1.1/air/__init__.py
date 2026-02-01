"""AIR SDK - Python client for the AIR Backend API."""

from .client import AIR
from .project import Project
from .exceptions import AIRError, AuthError, TaskTimeoutError

__version__ = "0.1.1"

__all__ = [
    "AIR",
    "Project",
    "AIRError",
    "AuthError",
    "TaskTimeoutError",
]
