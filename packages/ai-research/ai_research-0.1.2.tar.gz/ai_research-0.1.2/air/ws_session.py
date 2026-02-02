"""WebSocket session for AIR one-shot / deep-research execution.

Connects to the backend via WebSocket, submits a task, and handles the
full message loop — executing code locally, installing packages, and
writing files until the backend signals completion.

This is a Python port of air-ui's ``useWebSocket.ts``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from urllib.parse import urlencode

import websockets
import websockets.asyncio.client

from .executor import ExecutionResult, FileInfo, LocalCodeExecutor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class OneShotResult:
    """Returned by :meth:`AIR.one_shot` when the task finishes."""

    task_id: str
    output: str
    result: Any = None
    files_created: list[FileInfo] = field(default_factory=list)
    work_dir: str = ""
    error: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_task_id(backend_path: str) -> str | None:
    """Extract a ``task_*`` segment from a backend work_dir path."""
    for part in reversed(backend_path.split("/")):
        if part.startswith("task_"):
            return part
    return None


def _http_to_ws(url: str) -> str:
    """Convert an ``http(s)://`` URL to ``ws(s)://``."""
    if url.startswith("https://"):
        return "wss://" + url[len("https://"):]
    if url.startswith("http://"):
        return "ws://" + url[len("http://"):]
    return url


# ---------------------------------------------------------------------------
# WebSocketSession
# ---------------------------------------------------------------------------


class WebSocketSession:
    """Manage a single WebSocket task session with the AIR backend.

    Parameters
    ----------
    base_url:
        HTTP(S) base URL of the backend (e.g. ``http://localhost:8000``).
    api_key:
        AIR API key used for authentication.
    task_id:
        Unique identifier for this task.
    work_dir:
        Local directory where code and outputs are stored.
    on_output:
        Optional callback invoked with streaming text from the backend
        and from local code execution.
    timeout:
        Maximum wall-clock seconds for the entire session.
    python_path:
        Explicit Python binary for the venv.  ``None`` → auto-detect.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        task_id: str,
        work_dir: str,
        on_output: Callable[[str], None] | None = None,
        timeout: int = 86400,
        python_path: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._task_id = task_id
        self._work_dir = work_dir
        self._on_output = on_output
        self._timeout = timeout
        self._python_path = python_path

        self._executor: LocalCodeExecutor | None = None
        self._all_files: list[FileInfo] = []

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def run(self, task: str, config: dict) -> OneShotResult:
        """Connect, submit *task*, and drive the execution loop to completion."""
        # Build WS URL
        ws_base = _http_to_ws(self._base_url)
        params = urlencode({"api_key": self._api_key})
        ws_url = f"{ws_base}/ws/{self._task_id}?{params}"

        # Create executor
        self._executor = LocalCodeExecutor(self._work_dir, python_path=self._python_path)
        await self._executor.initialize()

        output_parts: list[str] = []
        result_data: Any = None
        errors: list[str] = []

        def _out(text: str) -> None:
            output_parts.append(text)
            if self._on_output:
                self._on_output(text)

        try:
            async with websockets.asyncio.client.connect(
                ws_url,
                open_timeout=30,
                close_timeout=10,
                max_size=2**24,  # 16 MiB
            ) as ws:
                # Submit task
                await ws.send(json.dumps({
                    "type": "task_submit",
                    "task": task,
                    "config": config,
                }))

                # Message loop
                while True:
                    raw = await ws.recv()
                    msg = json.loads(raw)
                    msg_type = msg.get("type", "")

                    if msg_type == "output":
                        data = msg.get("data", "")
                        if data:
                            _out(data)

                    elif msg_type == "status":
                        text = msg.get("message", "")
                        if text:
                            _out(f"Status: {text}\n")

                    elif msg_type == "result":
                        result_data = msg.get("data")

                    elif msg_type == "error":
                        err = msg.get("message", "Unknown error")
                        errors.append(err)
                        _out(f"Error: {err}\n")

                    elif msg_type == "complete":
                        _out("Task execution completed\n")
                        break

                    elif msg_type == "execute_code":
                        await self._handle_execute_code(ws, msg, _out)

                    elif msg_type == "install_packages":
                        await self._handle_install_packages(ws, msg, _out)

                    elif msg_type == "write_file":
                        await self._handle_write_file(msg, _out)

                    elif msg_type == "heartbeat":
                        pass  # keep-alive

                    else:
                        logger.debug("Unknown message type: %s", msg_type)

        except websockets.exceptions.ConnectionClosed as exc:
            errors.append(f"WebSocket closed: {exc}")
        except Exception as exc:
            errors.append(str(exc))

        return OneShotResult(
            task_id=self._task_id,
            output="".join(output_parts),
            result=result_data,
            files_created=self._all_files,
            work_dir=self._work_dir,
            error="; ".join(errors) if errors else None,
        )

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    async def _handle_execute_code(self, ws, msg: dict, out: Callable[[str], None]) -> None:
        execution_id = msg.get("execution_id", "")
        code_blocks = msg.get("code_blocks", [])
        timeout = msg.get("timeout", 86400)

        # Acknowledge immediately
        await ws.send(json.dumps({
            "type": "execution_ack",
            "execution_id": execution_id,
        }))

        n = len(code_blocks)
        out(f"\n--- Executing code ({n} block(s)) ---\n")

        assert self._executor is not None

        try:
            result: ExecutionResult = await self._executor.execute_code_blocks(
                code_blocks,
                timeout=timeout,
                on_output=out,
            )

            # Send result to backend
            await ws.send(json.dumps({
                "type": "execution_result",
                "execution_id": execution_id,
                "result": {
                    "exit_code": result.exit_code,
                    "output": result.output,
                    "code_file": result.code_file,
                },
            }))

            # Report files created
            if result.files_created:
                self._all_files.extend(result.files_created)
                await ws.send(json.dumps({
                    "type": "files_created",
                    "execution_id": execution_id,
                    "files": [
                        {"path": f.path, "size": f.size, "mime": f.mime}
                        for f in result.files_created
                    ],
                }))
                out(f"\nCreated {len(result.files_created)} file(s)\n")

            out(f"\n--- Execution complete (exit code: {result.exit_code}) ---\n")

        except Exception as exc:
            error_msg = str(exc)
            out(f"\nExecution error: {error_msg}\n")
            await ws.send(json.dumps({
                "type": "execution_error",
                "execution_id": execution_id,
                "error": error_msg,
            }))

    async def _handle_install_packages(self, ws, msg: dict, out: Callable[[str], None]) -> None:
        packages = msg.get("packages", [])
        out(f"\n--- Installing packages: {', '.join(packages)} ---\n")

        assert self._executor is not None

        result = await self._executor.install_packages(packages, on_output=out)

        await ws.send(json.dumps({
            "type": "install_complete",
            "packages": packages,
            "success": result.success,
            "failed": result.failed,
        }))

        if result.success:
            out("Packages installed successfully\n")
        else:
            out(f"Failed packages: {', '.join(result.failed)}\n")

    async def _handle_write_file(self, msg: dict, out: Callable[[str], None]) -> None:
        file_path = msg.get("path", "")
        content = msg.get("content", "")
        encoding = msg.get("encoding", "utf-8")

        if not file_path:
            return

        assert self._executor is not None

        try:
            await self._executor.write_file(file_path, content, encoding=encoding)
            out(f"File written: {file_path}\n")
        except Exception as exc:
            out(f"Failed to write file {file_path}: {exc}\n")
