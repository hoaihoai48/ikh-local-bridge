"""Load and validate the machine-readable Skill runtime contract."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_TOOL_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class ManifestError(ValueError):
    """Raised when a Skill manifest is invalid."""


@dataclass(frozen=True)
class ToolSpec:
    id: str
    description: str
    entrypoint: str
    timeout_seconds: int = 60


@dataclass(frozen=True)
class SkillSpec:
    slug: str
    name: str
    version: str
    description: str
    directory: Path
    has_instructions: bool
    tools: tuple[ToolSpec, ...]


def load_skill(directory: Path) -> SkillSpec:
    """Load a Skill folder. SKILL.md-only folders are discoverable but not runnable."""
    directory = directory.resolve()
    instructions = directory / "SKILL.md"
    manifest_path = directory / "skill.json"

    if not directory.is_dir():
        raise ManifestError("Skill path is not a directory")

    if not manifest_path.is_file():
        return SkillSpec(
            slug=directory.name,
            name=directory.name,
            version="unmanaged",
            description="No skill.json manifest; visible for discovery only.",
            directory=directory,
            has_instructions=instructions.is_file(),
            tools=(),
        )

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"Cannot read skill.json: {exc}") from exc

    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ManifestError("skill.json must be an object with schema_version: 1")

    slug = data.get("slug")
    name = data.get("name")
    version = data.get("version", "0.1.0")
    description = data.get("description", "")
    if not isinstance(slug, str) or not _SLUG.fullmatch(slug):
        raise ManifestError("slug must contain lowercase letters, digits, and hyphens")
    if slug != directory.name:
        raise ManifestError("manifest slug must match the Skill directory name")
    if not isinstance(name, str) or not name.strip():
        raise ManifestError("name is required")
    if not isinstance(version, str) or not version.strip():
        raise ManifestError("version must be a non-empty string")
    if not isinstance(description, str):
        raise ManifestError("description must be a string")

    raw_tools = data.get("tools", [])
    if not isinstance(raw_tools, list):
        raise ManifestError("tools must be a list")

    tools: list[ToolSpec] = []
    seen: set[str] = set()
    for raw in raw_tools:
        if not isinstance(raw, dict):
            raise ManifestError("each tool must be an object")
        tool_id = raw.get("id")
        entrypoint = raw.get("entrypoint")
        tool_description = raw.get("description", "")
        timeout = raw.get("timeout_seconds", 60)
        if not isinstance(tool_id, str) or not _TOOL_ID.fullmatch(tool_id):
            raise ManifestError("tool id is invalid")
        if tool_id in seen:
            raise ManifestError(f"duplicate tool id: {tool_id}")
        seen.add(tool_id)
        if not isinstance(entrypoint, str) or not entrypoint.endswith(".py"):
            raise ManifestError(f"{tool_id}: entrypoint must be a relative .py path")
        relative = Path(entrypoint)
        if relative.is_absolute() or ".." in relative.parts:
            raise ManifestError(f"{tool_id}: entrypoint must not escape the Skill folder")
        if not isinstance(tool_description, str):
            raise ManifestError(f"{tool_id}: description must be a string")
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 600:
            raise ManifestError(f"{tool_id}: timeout_seconds must be between 1 and 600")
        resolved = (directory / relative).resolve()
        if not resolved.is_relative_to(directory) or not resolved.is_file():
            raise ManifestError(f"{tool_id}: entrypoint is missing or outside the Skill folder")
        tools.append(ToolSpec(tool_id, tool_description, entrypoint, timeout))

    return SkillSpec(
        slug=slug,
        name=name.strip(),
        version=version,
        description=description,
        directory=directory,
        has_instructions=instructions.is_file(),
        tools=tuple(tools),
    )
