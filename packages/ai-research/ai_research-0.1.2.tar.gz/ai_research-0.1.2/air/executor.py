"""Local code executor for the AIR SDK.

Manages an isolated Python virtual environment and executes code blocks
via subprocess — a Python port of air-ui's ``FrontendCodeExecutor``.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import mimetypes
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class FileInfo:
    """Metadata for a file created during execution."""

    path: str  # relative to work_dir
    size: int
    mime: str


@dataclass
class ExecutionResult:
    """Result of executing one or more code blocks."""

    exit_code: int
    output: str
    code_file: str
    files_created: list[FileInfo] = field(default_factory=list)


@dataclass
class InstallResult:
    """Result of installing packages."""

    success: bool
    output: str
    failed: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LANG_EXTENSIONS = {
    "python": "py",
    "py": "py",
    "bash": "sh",
    "sh": "sh",
    "shell": "sh",
}

_MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
    ".csv": "text/csv",
    ".json": "application/json",
    ".txt": "text/plain",
    ".py": "text/x-python",
    ".sh": "text/x-shellscript",
    ".md": "text/markdown",
    ".html": "text/html",
    ".npy": "application/octet-stream",
    ".fits": "application/fits",
    ".pkl": "application/octet-stream",
}

_SKIP_DIRS = {".venv", "node_modules", "__pycache__", ".git"}

# Package name validation (same safeguard as air-ui)
_PACKAGE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")

# Base packages pre-installed into every new venv
_BASE_PACKAGES = ["numpy", "matplotlib", "pandas", "scipy"]


async def _find_python_binary() -> str:
    """Locate a Python >= 3.9 binary on the system."""
    home = str(Path.home())
    candidates = [
        "/opt/homebrew/bin/python3",
        "/opt/homebrew/bin/python3.13",
        "/opt/homebrew/bin/python3.12",
        "/opt/homebrew/bin/python3.11",
        "/opt/homebrew/bin/python3.10",
        "/opt/homebrew/bin/python3.9",
        "/usr/local/bin/python3",
        "/usr/local/bin/python3.13",
        "/usr/local/bin/python3.12",
        "/usr/local/bin/python3.11",
        "/usr/local/bin/python3.10",
        "/usr/local/bin/python3.9",
        os.path.join(home, ".pyenv", "shims", "python3"),
        os.path.join(home, "miniconda3", "bin", "python3"),
        os.path.join(home, "anaconda3", "bin", "python3"),
        "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/3.9/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/Current/bin/python3",
        "/usr/bin/python3",
    ]

    for candidate in candidates:
        try:
            proc = await asyncio.create_subprocess_exec(
                candidate, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
            text = stdout.decode().strip()
            m = re.search(r"Python (\d+)\.(\d+)", text)
            if m and int(m.group(1)) >= 3 and int(m.group(2)) >= 9:
                logger.info("Found Python %s.%s at %s", m.group(1), m.group(2), candidate)
                return candidate
        except (OSError, FileNotFoundError):
            continue

    logger.warning("Could not find Python 3.9+, falling back to python3")
    return "python3"


def _extract_filename(code: str) -> str | None:
    """Extract a filename directive from the first line of code."""
    first_line = code.split("\n", 1)[0].strip()
    patterns = [
        re.compile(r"^<!--\s*(filename:)?(.+?)\s*-->$"),
        re.compile(r"^/\*\s*(filename:)?(.+?)\s*\*/$"),
        re.compile(r"^//\s*(filename:)?(.+?)$"),
        re.compile(r"^#\s*(filename:)?(.+?)$"),
    ]
    for pat in patterns:
        m = pat.match(first_line)
        if m:
            name = m.group(2).strip()
            if name and " " not in name and "." in name:
                if name.startswith("codebase/"):
                    name = name[len("codebase/"):]
                return name.rsplit("/", 1)[-1]
    return None


def _get_mime(ext: str) -> str:
    return _MIME_MAP.get(ext, mimetypes.guess_type(f"f{ext}")[0] or "application/octet-stream")


# ---------------------------------------------------------------------------
# LocalCodeExecutor
# ---------------------------------------------------------------------------


class LocalCodeExecutor:
    """Execute code in a local, isolated Python virtual environment.

    Parameters
    ----------
    work_dir:
        Root directory for this task. Sub-folders ``codebase/``, ``data/``,
        ``plots/`` will be created automatically.
    python_path:
        Explicit Python binary to use for creating the venv.  When *None*,
        the executor searches common system paths for Python >= 3.9.
    """

    def __init__(self, work_dir: str, python_path: str | None = None) -> None:
        self.work_dir = os.path.expanduser(work_dir)
        self._venv_path = os.path.join(self.work_dir, ".venv")
        self._python_path = python_path
        self._initialized = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Create directories and virtual environment (idempotent)."""
        if self._initialized:
            return

        for sub in ("codebase", "data", "plots"):
            os.makedirs(os.path.join(self.work_dir, sub), exist_ok=True)

        # Resolve python binary
        if self._python_path:
            self._python_path = os.path.expanduser(self._python_path)
        else:
            self._python_path = await _find_python_binary()

        logger.info("Using Python: %s", self._python_path)

        # Create venv if missing
        if not os.path.isdir(self._venv_path):
            logger.info("Creating virtual environment at %s", self._venv_path)
            proc = await asyncio.create_subprocess_exec(
                self._python_path, "-m", "venv", self._venv_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to create venv (exit {proc.returncode})")

            # Pre-install base packages
            pip = self._pip_path
            try:
                await self._run_pip(["install", "--upgrade", "pip"])
                await self._run_pip(["install"] + _BASE_PACKAGES)
                logger.info("Base packages installed")
            except Exception as exc:
                logger.warning("Failed to install some base packages: %s", exc)

        self._initialized = True

    async def execute_code_blocks(
        self,
        code_blocks: list[dict],
        timeout: int = 86400,
        on_output: Callable[[str], None] | None = None,
    ) -> ExecutionResult:
        """Execute a list of ``{code, language}`` dicts.

        Returns an :class:`ExecutionResult` with captured output and a list
        of files created/modified during execution.
        """
        await self.initialize()

        before = self._scan_work_dir()
        all_output = ""
        exit_code = 0
        code_file = ""

        for block in code_blocks:
            code = block["code"]
            lang = block.get("language", "python").lower()

            # Determine filename
            filename = _extract_filename(code)
            if not filename:
                h = hashlib.md5(code.encode()).hexdigest()[:8]
                ts = int(time.time() * 1000)
                ext = _LANG_EXTENSIONS.get(lang, "txt")
                filename = f"code_{ts}_{h}.{ext}"

            code_file = os.path.join(self.work_dir, "codebase", filename)
            os.makedirs(os.path.dirname(code_file), exist_ok=True)
            with open(code_file, "w") as f:
                f.write(code)

            # Choose interpreter
            if lang in ("python", "py"):
                cmd = [self._venv_python, "-u", code_file]
            elif lang in ("bash", "sh", "shell"):
                cmd = ["bash", code_file]
            else:
                all_output += f"Unsupported language: {lang}\n"
                exit_code = 1
                break

            try:
                result = await self._run_command(cmd, timeout, on_output)
                all_output += result["output"]
                exit_code = result["exit_code"]
                if exit_code != 0:
                    break
            except asyncio.TimeoutError:
                all_output += f"\nExecution timed out after {timeout} seconds"
                exit_code = 124
                break

        after = self._scan_work_dir()
        files_created = self._diff_files(before, after)

        return ExecutionResult(
            exit_code=exit_code,
            output=all_output,
            code_file=code_file,
            files_created=files_created,
        )

    async def install_packages(
        self,
        packages: list[str],
        on_output: Callable[[str], None] | None = None,
    ) -> InstallResult:
        """Install Python packages into the task venv."""
        await self.initialize()

        failed: list[str] = []
        all_output = ""

        for pkg in packages:
            if not _PACKAGE_NAME_RE.match(pkg):
                failed.append(pkg)
                all_output += f"Invalid package name: {pkg}\n"
                continue
            try:
                out = await self._run_pip(["install", pkg], timeout=300)
                all_output += out + "\n"
            except Exception as exc:
                failed.append(pkg)
                all_output += f"Failed to install {pkg}: {exc}\n"

        if on_output:
            on_output(all_output)

        return InstallResult(
            success=len(failed) == 0,
            output=all_output,
            failed=failed,
        )

    async def write_file(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """Write a file relative to ``work_dir``."""
        full = os.path.join(self.work_dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding=encoding) as f:
            f.write(content)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _venv_python(self) -> str:
        return os.path.join(self._venv_path, "bin", "python")

    @property
    def _pip_path(self) -> str:
        return os.path.join(self._venv_path, "bin", "pip")

    async def _run_pip(self, args: list[str], timeout: int = 300) -> str:
        proc = await asyncio.create_subprocess_exec(
            self._pip_path, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.work_dir,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise
        if proc.returncode != 0:
            raise RuntimeError(f"pip {' '.join(args)} failed (exit {proc.returncode})")
        return stdout.decode()

    async def _run_command(
        self,
        cmd: list[str],
        timeout: int,
        on_output: Callable[[str], None] | None,
    ) -> dict:
        """Spawn a subprocess and stream output."""
        venv_bin = os.path.join(self._venv_path, "bin")
        env = {
            **os.environ,
            "PATH": f"{venv_bin}{os.pathsep}{os.environ.get('PATH', '')}",
            "PYTHONUNBUFFERED": "1",
            "MPLBACKEND": "Agg",
            "VIRTUAL_ENV": self._venv_path,
        }

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.work_dir,
            env=env,
        )

        output_parts: list[str] = []

        async def _read_stream():
            assert proc.stdout is not None
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode(errors="replace")
                output_parts.append(text)
                if on_output:
                    on_output(text)

        try:
            await asyncio.wait_for(_read_stream(), timeout=timeout)
            await proc.wait()
        except asyncio.TimeoutError:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
            raise

        return {"exit_code": proc.returncode or 0, "output": "".join(output_parts)}

    # ------------------------------------------------------------------
    # File scanning
    # ------------------------------------------------------------------

    def _scan_work_dir(self) -> dict[str, tuple[float, int]]:
        """Return ``{abspath: (mtime, size)}`` for all files in work_dir."""
        result: dict[str, tuple[float, int]] = {}
        self._scan_dir(self.work_dir, result)
        return result

    def _scan_dir(self, directory: str, out: dict[str, tuple[float, int]]) -> None:
        try:
            entries = os.scandir(directory)
        except OSError:
            return
        with entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in _SKIP_DIRS:
                        continue
                    self._scan_dir(entry.path, out)
                elif entry.is_file(follow_symlinks=False):
                    try:
                        st = entry.stat()
                        out[entry.path] = (st.st_mtime, st.st_size)
                    except OSError:
                        pass

    def _diff_files(
        self,
        before: dict[str, tuple[float, int]],
        after: dict[str, tuple[float, int]],
    ) -> list[FileInfo]:
        new_files: list[FileInfo] = []
        for fpath, (mtime, size) in after.items():
            prev = before.get(fpath)
            if prev is None or prev[0] < mtime:
                rel = os.path.relpath(fpath, self.work_dir)
                ext = os.path.splitext(fpath)[1].lower()
                new_files.append(FileInfo(path=rel, size=size, mime=_get_mime(ext)))
        return new_files
