"""Local stdio MCP server for explicitly registered Bridge instances.

The connected client supplies reasoning; this process does not call an AI provider.
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .instances import BridgeInstance, get_instance
from .jobs import JobStore
from .local_tools import execute_tool

mcp = FastMCP("ikh-local-bridge")
_store = JobStore()


def _instance(instance_id: str = "default") -> BridgeInstance:
    """Resolve only an explicitly registered, enabled workspace instance."""
    return get_instance(instance_id)


def _logged_execute(tool_name: str, args: dict[str, Any], instance_id: str = "default") -> dict[str, Any]:
    instance = _instance(instance_id)
    job_id = _store.create("instance:" + instance.id, tool_name, str(instance.workspace))
    try:
        result = execute_tool(tool_name, args, instance.workspace)
        status = "COMPLETED" if result.get("ok") else "FAILED"
        if "bytes" in result:
            summary = "bytes: " + str(result.get("bytes"))
        elif "entries" in result:
            summary = "entries: " + str(len(result.get("entries", [])))
        elif "returncode" in result:
            summary = "returncode: " + str(result.get("returncode"))
        else:
            summary = ""
        error = result.get("error") or result.get("stderr") or ""
        exit_code = result.get("returncode", 0 if result.get("ok") else 1)
        _store.finish(job_id, status, exit_code, stdout=summary, stderr=error)
        return result
    except Exception as exc:
        _store.finish(job_id, "FAILED", 1, error=str(exc))
        raise


@mcp.tool()
def list_bridge_instances() -> dict[str, Any]:
    """List only configured instances; disabled instances are shown but cannot be selected."""
    from .instances import load_instances

    instances = load_instances()
    return {
        "instances": [
            {
                "id": item.id,
                "name": item.name,
                "enabled": item.enabled,
                "workspace": str(item.workspace),
                "skill_file": str(item.skill_file),
            }
            for item in instances.values()
        ]
    }


@mcp.tool()
def get_bridge_status(instance_id: str = "default") -> dict[str, Any]:
    """Check one explicitly configured Bridge instance and its canonical Skill."""
    instance = _instance(instance_id)
    job_id = _store.create("instance:" + instance.id, "get_bridge_status", str(instance.workspace))
    _store.finish(job_id, "COMPLETED", 0, stdout="Checked bridge instance readiness")
    return {
        "ok": True,
        "bridge": "ikh-local-bridge",
        "mode": "local_mcp_tools_no_model_api",
        "instance_id": instance.id,
        "instance_name": instance.name,
        "workspace": str(instance.workspace),
        "workspace_exists": instance.workspace.is_dir(),
        "skill_file": str(instance.skill_file),
        "skill_exists": instance.skill_file.is_file(),
        "skill_bytes": instance.skill_file.stat().st_size,
        "note": "Tools use application-level workspace path checks, not an OS sandbox. This process does not call an AI-provider API.",
    }


@mcp.tool()
def get_curriculum_skill(instance_id: str = "default") -> dict[str, Any]:
    """Load the canonical Skill configured for the selected Bridge instance."""
    instance = _instance(instance_id)
    content = instance.skill_file.read_text(encoding="utf-8")
    job_id = _store.create("instance:" + instance.id, "get_curriculum_skill", str(instance.workspace))
    _store.finish(job_id, "COMPLETED", 0, stdout="Loaded Skill " + str(len(content)) + " bytes")
    return {
        "ok": True,
        "instance_id": instance.id,
        "path": str(instance.skill_file),
        "name": "iKH Curriculum Authoring Skill",
        "content": content,
        "instruction": "Treat this file as the normative workflow. Inspect canonical files and validators before editing. Preserve evidence and QA gates. Report PASS, FAIL, BLOCKED, and NOT VERIFIED separately.",
    }


@mcp.tool()
def list_files(path: str = ".", instance_id: str = "default") -> dict[str, Any]:
    """List direct children of a directory inside the selected instance workspace."""
    return _logged_execute("list_files", {"path": path}, instance_id)


@mcp.tool()
def read_file(path: str, instance_id: str = "default") -> dict[str, Any]:
    """Read a UTF-8 text file inside the selected instance workspace."""
    return _logged_execute("read_file", {"path": path}, instance_id)


@mcp.tool()
def write_file(path: str, content: str, instance_id: str = "default") -> dict[str, Any]:
    """Create or update a UTF-8 text file inside the selected instance workspace."""
    return _logged_execute("write_file", {"path": path, "content": content}, instance_id)


@mcp.tool()
def run_command(
    argv: list[str],
    cwd: str = ".",
    timeout_seconds: int = 60,
    instance_id: str = "default",
) -> dict[str, Any]:
    """Run an allowlisted Python test/validator or read-only Git command in the selected instance."""
    return _logged_execute(
        "run_command",
        {"argv": argv, "cwd": cwd, "timeout_seconds": timeout_seconds},
        instance_id,
    )


@mcp.tool()
def fetch_url(url: str, instance_id: str = "default") -> dict[str, Any]:
    """Fetch a public HTTPS source page; private/local IPs and unsafe redirects are blocked."""
    return _logged_execute("fetch_url", {"url": url}, instance_id)


def main() -> None:
    # MCP stdio is local process communication; no network listener is opened.
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
