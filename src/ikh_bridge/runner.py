"""Execute explicitly declared Python entrypoints without invoking a shell."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .jobs import JobStore
from .manifest import SkillSpec, ToolSpec


class RunRejected(ValueError):
    """Raised when a requested tool is not permitted."""


def run_tool(skill: SkillSpec, tool: ToolSpec, workspace: Path, store: JobStore) -> dict:
    skill_root = skill.directory.resolve()
    entrypoint = (skill_root / tool.entrypoint).resolve()
    if not entrypoint.is_relative_to(skill_root) or not entrypoint.is_file():
        raise RunRejected("Tool entrypoint is outside the Skill folder or missing")

    workspace = workspace.expanduser().resolve()
    if not workspace.is_dir():
        raise RunRejected("Workspace must be an existing directory")

    job_id = store.create(skill.slug, tool.id, str(workspace))
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "HOME": str(Path.home()),
        "IKH_BRIDGE_WORKSPACE": str(workspace),
    }
    try:
        completed = subprocess.run(
            [sys.executable, str(entrypoint)],
            cwd=str(workspace),
            env=env,
            capture_output=True,
            text=True,
            timeout=tool.timeout_seconds,
            check=False,
            shell=False,
        )
        status = "COMPLETED" if completed.returncode == 0 else "FAILED"
        store.finish(job_id, status, completed.returncode, completed.stdout, completed.stderr)
        return {
            "job_id": job_id,
            "status": status,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "mode": "registered_python_entrypoint",
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        store.finish(job_id, "FAILED", None, stdout, stderr, "Tool timed out")
        return {"job_id": job_id, "status": "FAILED", "error": "Tool timed out"}
    except OSError as exc:
        store.finish(job_id, "FAILED", None, error=str(exc))
        return {"job_id": job_id, "status": "FAILED", "error": str(exc)}
