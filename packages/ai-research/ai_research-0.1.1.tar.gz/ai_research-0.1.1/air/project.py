"""Project class - wraps a single AIR research project."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from .exceptions import AIRError, TaskTimeoutError

if TYPE_CHECKING:
    import httpx


class Project:
    """
    A AIR research project accessed via the AIR API.

    Provides methods for each pipeline step (idea, literature, methods,
    paper, review) and file access.

    Do not instantiate directly -- use ``AIR.create_project()`` or
    ``AIR.get_project()`` instead.
    """

    def __init__(self, name: str, client: "httpx.Client", poll_interval: float = 3.0):
        self.name = name
        self._client = client
        self._poll_interval = poll_interval

    def _poll_task(self, task_id: str, timeout: float) -> dict:
        """Poll a task until it completes or the timeout expires."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            resp = self._client.get(f"/api/v1/tasks/{task_id}")
            resp.raise_for_status()
            data = resp.json()

            if data["status"] == "completed":
                result_resp = self._client.get(f"/api/v1/tasks/{task_id}/result")
                result_resp.raise_for_status()
                return result_resp.json()

            if data["status"] == "failed":
                result_resp = self._client.get(f"/api/v1/tasks/{task_id}/result")
                result_resp.raise_for_status()
                result_data = result_resp.json()
                raise AIRError(
                    f"Task {task_id} failed: {result_data.get('error', 'unknown error')}"
                )

            time.sleep(self._poll_interval)

        raise TaskTimeoutError(task_id, timeout)

    def _run_step(
        self,
        step: str,
        timeout: float,
        **body_overrides: Any,
    ) -> dict:
        """Submit a pipeline step and poll until done."""
        resp = self._client.post(
            f"/api/v1/projects/{self.name}/{step}",
            json=body_overrides if body_overrides else {},
        )
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
        return self._poll_task(task_id, timeout)

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    def _read_output_file(self, path: str) -> str | None:
        """Try to read a project file, return None if not found."""
        try:
            return self.get_file(path)
        except Exception:
            return None

    def idea(
        self,
        mode: str = "fast",
        iteration: int = 0,
        timeout: float = 600,
        **kwargs: Any,
    ) -> str:
        """
        Run idea generation.

        Args:
            mode: Execution mode ("fast" uses LangGraph, "full" uses P&C).
            iteration: Project iteration number.
            timeout: Max seconds to wait for completion.

        Returns:
            The generated idea text.
        """
        self._run_step("idea", timeout=timeout, mode=mode, iteration=iteration, **kwargs)
        return self._read_output_file(f"Iteration{iteration}/input_files/idea.md") or ""

    def literature(self, iteration: int = 0, timeout: float = 600, **kwargs: Any) -> str:
        """Run literature search."""
        self._run_step("literature", timeout=timeout, iteration=iteration, **kwargs)
        return self._read_output_file(f"Iteration{iteration}/input_files/literature.md") or ""

    def methods(
        self,
        mode: str = "fast",
        iteration: int = 0,
        timeout: float = 600,
        **kwargs: Any,
    ) -> str:
        """Run methods development."""
        self._run_step("methods", timeout=timeout, mode=mode, iteration=iteration, **kwargs)
        return self._read_output_file(f"Iteration{iteration}/input_files/methods.md") or ""

    def paper(
        self,
        journal: str = "NONE",
        iteration: int = 0,
        timeout: float = 900,
        **kwargs: Any,
    ) -> str:
        """Run paper writing."""
        self._run_step("paper", timeout=timeout, journal=journal, iteration=iteration, **kwargs)
        return self._read_output_file(f"Iteration{iteration}/paper_output/paper_v4_final.tex") or ""

    def review(self, iteration: int = 0, timeout: float = 600, **kwargs: Any) -> str:
        """Run review."""
        self._run_step("review", timeout=timeout, iteration=iteration, **kwargs)
        return self._read_output_file(f"Iteration{iteration}/input_files/referee.md") or ""

    # ------------------------------------------------------------------
    # File access
    # ------------------------------------------------------------------

    def get_file(self, path: str) -> str:
        """
        Read a file from the project.

        Args:
            path: Relative path within the project (e.g. "Iteration0/input_files/idea.md").

        Returns:
            File content as a string (base64 for binary files).
        """
        resp = self._client.get(f"/api/v1/projects/{self.name}/files/{path}")
        resp.raise_for_status()
        return resp.json()["content"]

    def list_files(self) -> list[dict]:
        """
        List all files in the project.

        Returns:
            List of dicts with keys: relative_path, size, mtime.
        """
        resp = self._client.get(f"/api/v1/projects/{self.name}")
        resp.raise_for_status()
        return resp.json().get("files", [])

    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> dict:
        """
        Write a file to the project.

        Args:
            path: Relative path within the project.
            content: File content.
            encoding: "utf-8" or "base64".

        Returns:
            Server response dict.
        """
        resp = self._client.post(
            f"/api/v1/projects/{self.name}/files",
            json={"path": path, "content": content, "encoding": encoding},
        )
        resp.raise_for_status()
        return resp.json()

    def delete(self) -> dict:
        """Delete this project from the server."""
        resp = self._client.delete(f"/api/v1/projects/{self.name}")
        resp.raise_for_status()
        return resp.json()

    def __repr__(self) -> str:
        return f"Project('{self.name}')"
