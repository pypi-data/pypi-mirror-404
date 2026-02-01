"""Exception classes for the AIR SDK."""


class AIRError(Exception):
    """Base exception for AIR SDK errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AuthError(AIRError):
    """Raised when authentication fails (invalid or missing API key)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class TaskTimeoutError(AIRError):
    """Raised when an async task exceeds the polling timeout."""

    def __init__(self, task_id: str, timeout: float):
        super().__init__(
            f"Task {task_id} did not complete within {timeout}s",
            status_code=None,
        )
        self.task_id = task_id
        self.timeout = timeout
