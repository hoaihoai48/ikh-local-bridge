"""Workspace-scoped tools exposed to the local Skill agent."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

MAX_READ_BYTES = 200_000
MAX_OUTPUT_CHARS = 30_000
COMMAND_TIMEOUT_SECONDS = 120


def _resolve_workspace_path(workspace: Path, relative_path: str) -> Path:
    root = workspace.resolve()
    raw = Path(relative_path or ".")
    target = (root / raw).resolve() if not raw.is_absolute() else raw.resolve()
    if not target.is_relative_to(root):
        raise ValueError("Path escapes the selected workspace")
    return target


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {"type": "function", "function": {
            "name": "list_files",
            "description": "List files and directories directly inside a workspace-relative directory.",
            "parameters": {"type": "object", "properties": {
                "path": {"type": "string", "description": "Relative directory path; use '.' for workspace root"}
            }, "required": ["path"], "additionalProperties": False}
        }},
        {"type": "function", "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file inside the selected workspace.",
            "parameters": {"type": "object", "properties": {
                "path": {"type": "string", "description": "Workspace-relative file path"}
            }, "required": ["path"], "additionalProperties": False}
        }},
        {"type": "function", "function": {
            "name": "write_file",
            "description": "Create or replace a UTF-8 text file inside the selected workspace. Creates parent directories as needed.",
            "parameters": {"type": "object", "properties": {
                "path": {"type": "string", "description": "Workspace-relative file path"},
                "content": {"type": "string", "description": "Complete file content"}
            }, "required": ["path", "content"], "additionalProperties": False}
        }},
        {"type": "function", "function": {
            "name": "run_command",
            "description": "Run a local command in the selected workspace. Provide argv as an array, not a shell command string. Commands execute with the current user's permissions; never use destructive or unrelated commands.",
            "parameters": {"type": "object", "properties": {
                "argv": {"type": "array", "items": {"type": "string"}, "minItems": 1,
                         "description": "Executable and arguments, e.g. ['python', '-m', 'pytest', '-q']"},
                "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 120}
            }, "required": ["argv"], "additionalProperties": False}
        }},
    ]


def execute_tool(name: str, args: dict[str, Any], workspace: Path) -> dict[str, Any]:
    if name == "list_files":
        target = _resolve_workspace_path(workspace, str(args.get("path", ".")))
        if not target.is_dir():
            raise ValueError("Directory does not exist")
        entries = []
        for item in sorted(target.iterdir(), key=lambda p: p.name.casefold()):
            entries.append({"name": item.name, "type": "directory" if item.is_dir() else "file"})
        return {"ok": True, "path": str(target.relative_to(workspace.resolve())), "entries": entries[:2000]}
    if name == "read_file":
        target = _resolve_workspace_path(workspace, str(args.get("path", "")))
        if not target.is_file():
            raise ValueError("File does not exist")
        size = target.stat().st_size
        if size > MAX_READ_BYTES:
            raise ValueError(f"File is {size} bytes; limit is {MAX_READ_BYTES}. Read a smaller file or split it.")
        return {"ok": True, "path": str(target.relative_to(workspace.resolve())),
                "content": target.read_text(encoding="utf-8")}
    if name == "write_file":
        relative = str(args.get("path", ""))
        if not relative or relative == ".":
            raise ValueError("A file path is required")
        target = _resolve_workspace_path(workspace, relative)
        content = args.get("content")
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(target.relative_to(workspace.resolve())),
                "bytes_written": target.stat().st_size}
    if name == "run_command":
        argv = args.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(part, str) for part in argv):
            raise ValueError("argv must be a non-empty array of strings")
        if any(not part.strip() for part in argv):
            raise ValueError("argv items must not be empty")
        timeout = args.get("timeout_seconds", COMMAND_TIMEOUT_SECONDS)
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= COMMAND_TIMEOUT_SECONDS:
            raise ValueError(f"timeout_seconds must be from 1 to {COMMAND_TIMEOUT_SECONDS}")
        completed = subprocess.run(
            argv, cwd=str(workspace.resolve()), shell=False, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
        return {"ok": completed.returncode == 0, "argv": argv, "exit_code": completed.returncode,
                "stdout": completed.stdout[-MAX_OUTPUT_CHARS:],
                "stderr": completed.stderr[-MAX_OUTPUT_CHARS:]}
    raise ValueError(f"Unknown local tool: {name}")
