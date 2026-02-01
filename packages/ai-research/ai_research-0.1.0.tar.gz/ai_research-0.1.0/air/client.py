"""AIR client - main entry point for the SDK."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .exceptions import AIRError, AuthError
from .project import Project

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
