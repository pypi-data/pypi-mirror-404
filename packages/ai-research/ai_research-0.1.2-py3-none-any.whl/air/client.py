"""AIR client - main entry point for the SDK."""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Callable

import httpx

from .exceptions import AIRError, AuthError, WebSocketError
from .project import Project
from .ws_session import OneShotResult, WebSocketSession

_DEFAULT_BASE_URL = "http://localhost:8000"
_DEFAULT_TIMEOUT = 120.0  # seconds


class AIR:
    """
    Client for the AIR Backend REST API.

    Usage::

        import air

        client = air.AIR(api_key="air_k1_...")
        keywords = client.keywords("dark matter and lensing", n=5)

        project = client.create_project("my-research", data_description="We study...")
        idea = project.idea()
        project.literature()
        project.methods()
        project.paper(journal="AAS")
        review = project.review()

    Args:
        api_key: AIR API key (``air_k1_...``). Falls back to ``AIR_API_KEY`` env var.
        base_url: Base URL of the AIR backend. Defaults to ``http://localhost:8000``.
        timeout: Default HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        self._api_key = api_key or os.environ.get("AIR_API_KEY", "")
        if not self._api_key:
            raise AuthError(
                "API key required. Pass api_key= or set the AIR_API_KEY environment variable."
            )

        self._base_url = (base_url or os.environ.get("AIR_BASE_URL", _DEFAULT_BASE_URL)).rstrip("/")

        self._client = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "AIR":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self) -> dict:
        """Check if the backend is healthy."""
        resp = self._client.get("/api/health")
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Standalone tools
    # ------------------------------------------------------------------

    def keywords(
        self,
        text: str,
        n: int = 5,
        kw_type: str = "unesco",
    ) -> Any:
        """
        Extract keywords from text.

        Args:
            text: Input text.
            n: Number of keywords to extract.
            kw_type: Keyword type ("unesco", "aas", etc.).

        Returns:
            Keywords result (list or dict depending on kw_type).
        """
        resp = self._client.post(
            "/api/v1/keywords",
            json={"text": text, "n_keywords": n, "kw_type": kw_type},
        )
        self._check(resp)
        return resp.json().get("keywords")

    def arxiv(self, text: str) -> dict:
        """
        Extract arXiv URLs from text and download papers.

        Args:
            text: Input text containing arXiv URLs.

        Returns:
            Dict with download results.
        """
        resp = self._client.post("/api/v1/arxiv", json={"text": text})
        self._check(resp)
        return resp.json().get("result", {})

    def enhance(
        self,
        text: str,
        max_workers: int = 2,
        max_depth: int = 10,
    ) -> str:
        """
        Enhance input text with contextual information from arXiv papers.

        Args:
            text: Input text (may contain arXiv URLs).
            max_workers: Parallel workers for downloading.
            max_depth: Max summarisation depth.

        Returns:
            Enhanced text.
        """
        resp = self._client.post(
            "/api/v1/enhance",
            json={"text": text, "max_workers": max_workers, "max_depth": max_depth},
        )
        self._check(resp)
        return resp.json().get("enhanced_text", "")

    def ocr(self, file_path: str) -> dict:
        """
        Process a PDF with OCR (server-side path).

        Args:
            file_path: Path to the PDF on the server.

        Returns:
            OCR result dict.
        """
        resp = self._client.post("/api/v1/ocr", json={"file_path": file_path})
        self._check(resp)
        return resp.json().get("result", {})

    # ------------------------------------------------------------------
    # Project management
    # ------------------------------------------------------------------

    def create_project(
        self,
        name: str,
        data_description: str = "",
        iteration: int = 0,
    ) -> Project:
        """
        Create a new AIR research project.

        Args:
            name: Project name (used as directory name on server).
            data_description: Description of the research data/topic.
            iteration: Starting iteration number.

        Returns:
            A Project instance for further pipeline steps.
        """
        resp = self._client.post(
            "/api/v1/projects",
            json={
                "name": name,
                "data_description": data_description,
                "iteration": iteration,
            },
        )
        self._check(resp)
        return Project(name, self._client)

    def get_project(self, name: str) -> Project:
        """
        Get an existing project by name.

        Args:
            name: Project name.

        Returns:
            A Project instance.

        Raises:
            AIRError: If the project does not exist.
        """
        resp = self._client.get(f"/api/v1/projects/{name}")
        self._check(resp)
        return Project(name, self._client)

    def list_projects(self) -> list[str]:
        """
        List all projects for this API key.

        Returns:
            List of project names.
        """
        resp = self._client.get("/api/v1/projects")
        self._check(resp)
        return resp.json().get("projects", [])

    def delete_project(self, name: str) -> dict:
        """Delete a project."""
        resp = self._client.delete(f"/api/v1/projects/{name}")
        self._check(resp)
        return resp.json()

    # ------------------------------------------------------------------
    # One-shot / deep-research (local execution via WebSocket)
    # ------------------------------------------------------------------

    def one_shot(
        self,
        task: str,
        *,
        model: str = "gpt-4.1-2025-04-14",
        max_rounds: int = 25,
        max_attempts: int = 1,
        agent: str = "engineer",
        work_dir: str | None = None,
        timeout: int = 86400,
        on_output: Callable[[str], None] | None = lambda s: print(s, end="\n", flush=True),
        python_path: str | None = None,
        **config_overrides: Any,
    ) -> OneShotResult:
        """
        Execute a one-shot task with local code execution.

        The backend orchestrates the AI agent loop while all generated code
        runs locally on your machine in an isolated virtual environment.

        Args:
            task: Natural-language description of the task.
            model: LLM model for the backend agent.
            max_rounds: Maximum agent conversation rounds.
            max_attempts: Retry attempts on failure.
            agent: Agent type (``"engineer"``, etc.).
            work_dir: Local directory for code and outputs.
                Defaults to ``~/ai-scientist``.
            timeout: Maximum wall-clock seconds for the entire session.
            on_output: Callback invoked with streaming text.
            python_path: Explicit Python binary for the task venv.
            **config_overrides: Extra keys merged into the config sent
                to the backend.

        Returns:
            An :class:`OneShotResult` with output text, result data,
            created files, and the local work directory.

        Raises:
            WebSocketError: If the WebSocket connection fails.
            AuthError: If the API key is invalid.
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        base_work_dir = work_dir or os.environ.get("AIR_WORK_DIR", "~/ai-scientist")
        base_work_dir = os.path.expanduser(base_work_dir)
        task_work_dir = os.path.join(base_work_dir, task_id)

        config = {
            "mode": "one-shot",
            "agent": agent,
            "engineerModel": model,
            "maxRounds": max_rounds,
            "maxAttempts": max_attempts,
            "remoteExecution": True,
            **config_overrides,
        }

        session = WebSocketSession(
            base_url=self._base_url,
            api_key=self._api_key,
            task_id=task_id,
            work_dir=task_work_dir,
            on_output=on_output,
            timeout=timeout,
            python_path=python_path,
        )

        coro = session.run(task, config)

        # Sync-to-async bridge: detect whether an event loop is already
        # running (e.g. Jupyter) and handle accordingly.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is None:
            # Normal script — no loop running yet.
            return asyncio.run(coro)
        else:
            # Already inside an event loop (Jupyter, etc.) — run in a
            # background thread to avoid blocking the existing loop.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _check(self, resp: httpx.Response) -> None:
        """Raise appropriate exceptions for error responses."""
        if resp.status_code == 401:
            raise AuthError(resp.json().get("detail", "Authentication failed"))
        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise AIRError(detail, status_code=resp.status_code)

    def __repr__(self) -> str:
        return f"AIR(base_url='{self._base_url}')"
