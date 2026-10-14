"""Local MCP server for the packaged iKH Curriculum Authoring Skill.

No model inference or AI-provider API calls happen in this process. A compatible
local client (for example, ChatGPT Desktop with a local plugin) supplies the
reasoning model; this server exposes the Skill and executes workspace tools.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .jobs import JobStore
from .local_tools import execute_tool

mcp = FastMCP("ikh-curriculum-local-bridge")
_store = JobStore()


def _repository_root() -> Path:
    # local-bridge/src/ikh_bridge/mcp_server.py -> repository root
    return Path(__file__).resolve().parents[3]


def _workspace() -> Path:
    raw = os.environ.get("IKH_BRIDGE_WORKSPACE", "").strip()
    root = Path(raw).expanduser().resolve() if raw else _repository_root()
    if not root.is_dir():
        raise ValueError(f"Configured workspace is not a directory: {root}")
    return root


def _skill_file() -> Path:
    raw = os.environ.get("IKH_BRIDGE_SKILL_FILE", "").strip()
    path = Path(raw).expanduser().resolve() if raw else (
        _repository_root() / "skills" / "ikh-curriculum-authoring" / "SKILL.md"
    )
    if not path.is_file():
        raise FileNotFoundError(
            f"iKH Curriculum Authoring Skill was not found: {path}. "
            "Set IKH_BRIDGE_SKILL_FILE to the canonical SKILL.md."
        )
    return path


def _logged_execute(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    ws = _workspace()
    job_id = _store.create("ikh-curriculum-authoring", tool_name, str(ws))
    try:
        res = execute_tool(tool_name, args, ws)
        status = "COMPLETED" if res.get("ok") else "FAILED"
        out_summary = f"bytes: {res.get('bytes')}" if "bytes" in res else f"entries: {len(res.get('entries', []))}" if "entries" in res else ""
        err = res.get("error") or res.get("stderr") or ""
        _store.finish(job_id, status, 0 if status == "COMPLETED" else 1, stdout=out_summary, stderr=err)
        return res
    except Exception as exc:
        _store.finish(job_id, "FAILED", 1, error=str(exc))
        raise


@mcp.tool()
def get_bridge_status() -> dict[str, Any]:
    """Check local workspace and canonical Skill availability. Call this first."""
    workspace = _workspace()
    skill = _skill_file()
    job_id = _store.create("ikh-curriculum-authoring", "get_bridge_status", str(workspace))
    _store.finish(job_id, "COMPLETED", 0, stdout="Checked bridge and workspace readiness")
    return {
        "ok": True,
        "bridge": "ikh-curriculum-local-bridge",
        "mode": "local_mcp_tools_no_model_api",
        "workspace": str(workspace),
        "workspace_exists": workspace.is_dir(),
        "skill_file": str(skill),
        "skill_exists": skill.is_file(),
        "skill_bytes": skill.stat().st_size,
        "note": (
            "Tools execute locally. The connected MCP client supplies AI reasoning. "
            "This server does not call an AI-provider API."
        ),
    }


@mcp.tool()
def get_curriculum_skill() -> dict[str, Any]:
    """Load the canonical iKH Skill. MUST be called before curriculum work."""
    path = _skill_file()
    content = path.read_text(encoding="utf-8")
    job_id = _store.create("ikh-curriculum-authoring", "get_curriculum_skill", str(_workspace()))
    _store.finish(job_id, "COMPLETED", 0, stdout=f"Loaded Skill {len(content)} bytes")
    return {
        "ok": True,
        "path": str(path),
        "name": "iKH Curriculum Authoring Skill",
        "content": content,
        "instruction": (
            "Treat this file as the normative workflow. Inspect the target course's "
            "own canonical files and validators before editing. Honor evidence, plan, "
            "content-lock and QA gates. Report PASS, FAIL, BLOCKED and NOT VERIFIED "
            "separately; never claim a check passed unless a local tool ran it."
        ),
    }


@mcp.tool()
def list_files(path: str = ".") -> dict[str, Any]:
    """List files and directories inside the configured local curriculum workspace."""
    return _logged_execute("list_files", {"path": path})


@mcp.tool()
def read_file(path: str) -> dict[str, Any]:
    """Read a UTF-8 text file inside the local workspace; protected paths are blocked."""
    return _logged_execute("read_file", {"path": path})


@mcp.tool()
def write_file(path: str, content: str) -> dict[str, Any]:
    """Create or update a UTF-8 text file when the user's task authorizes changes."""
    return _logged_execute("write_file", {"path": path, "content": content})


@mcp.tool()
def run_command(argv: list[str], cwd: str = ".", timeout_seconds: int = 60) -> dict[str, Any]:
    """Run an allowlisted Python test/validator or read-only Git command; no shell/install/commit/push."""
    return _logged_execute(
        "run_command",
        {"argv": argv, "cwd": cwd, "timeout_seconds": timeout_seconds},
    )


@mcp.tool()
def fetch_url(url: str) -> dict[str, Any]:
    """Fetch a public HTTPS source page using GET only; local/private IP targets are blocked."""
    return _logged_execute("fetch_url", {"url": url})


def main() -> None:
    # MCP stdio is local process communication; do not expose a network listener.
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
