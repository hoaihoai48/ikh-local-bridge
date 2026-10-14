"""Explicit registry for workspaces exposed through the MCP server.

The registry is an application-level authorization boundary, not an OS sandbox.
Use trusted, locally controlled configuration files and least-privilege workspaces.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

_INSTANCE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class InstanceConfigError(ValueError):
    """Raised when an instance is missing, disabled, or misconfigured."""


@dataclass(frozen=True)
class BridgeInstance:
    id: str
    name: str
    workspace: Path
    skill_file: Path
    enabled: bool = True


def _resolve_dir(value: object, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise InstanceConfigError(f"{field} must be a non-empty path")
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise InstanceConfigError(f"{field} directory does not exist: {path}")
    return path


def _resolve_file(value: object, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise InstanceConfigError(f"{field} must be a non-empty path")
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise InstanceConfigError(f"{field} file does not exist: {path}")
    return path


def load_instances(config_path: Path | None = None) -> dict[str, BridgeInstance]:
    """Load explicit instances, or expose a single legacy default instance.

    If IKH_BRIDGE_INSTANCES_CONFIG is set, invalid config fails closed: there is
    no fallback to environment-based default workspace.
    """
    raw_config = os.environ.get("IKH_BRIDGE_INSTANCES_CONFIG", "").strip()
    if config_path is None and raw_config:
        config_path = Path(raw_config).expanduser().resolve()

    if config_path is not None:
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InstanceConfigError(f"Cannot read instance config: {exc}") from exc
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise InstanceConfigError("Instance config must be an object with schema_version: 1")
        raw_instances = data.get("instances")
        if not isinstance(raw_instances, list) or not raw_instances:
            raise InstanceConfigError("instances must be a non-empty list")
        result: dict[str, BridgeInstance] = {}
        for item in raw_instances:
            if not isinstance(item, dict):
                raise InstanceConfigError("each instance must be an object")
            instance_id = item.get("id")
            if not isinstance(instance_id, str) or not _INSTANCE_ID.fullmatch(instance_id):
                raise InstanceConfigError("instance id must use lowercase letters, digits, underscore, or hyphen")
            if instance_id in result:
                raise InstanceConfigError(f"duplicate instance id: {instance_id}")
            enabled = item.get("enabled", False)
            if not isinstance(enabled, bool):
                raise InstanceConfigError(f"{instance_id}: enabled must be boolean")
            name = item.get("name", instance_id)
            if not isinstance(name, str) or not name.strip():
                raise InstanceConfigError(f"{instance_id}: name must be non-empty")
            workspace = _resolve_dir(item.get("workspace"), f"{instance_id}.workspace")
            skill_file = _resolve_file(item.get("skill_file"), f"{instance_id}.skill_file")
            result[instance_id] = BridgeInstance(instance_id, name.strip(), workspace, skill_file, enabled)
        return result

    # Backward-compatible single-instance mode. This is intentionally disabled
    # whenever an explicit config path is provided but invalid.
    workspace_raw = os.environ.get("IKH_BRIDGE_WORKSPACE", "").strip()
    workspace = Path(workspace_raw).expanduser().resolve() if workspace_raw else Path.cwd().resolve()
    if not workspace.is_dir():
        raise InstanceConfigError(f"Configured workspace is not a directory: {workspace}")
    skill_raw = os.environ.get("IKH_BRIDGE_SKILL_FILE", "").strip()
    if skill_raw:
        skill_file = Path(skill_raw).expanduser().resolve()
    else:
        candidates = (
            Path(__file__).resolve().parents[2] / "skills" / "ikh-curriculum-authoring" / "SKILL.md",
            Path.home() / ".ikh-skills" / "ikh-curriculum-authoring" / "SKILL.md",
        )
        skill_file = next((p.resolve() for p in candidates if p.is_file()), candidates[0].resolve())
    if not skill_file.is_file():
        raise InstanceConfigError(
            f"Skill was not found: {skill_file}; set IKH_BRIDGE_SKILL_FILE or configure an instance registry"
        )
    return {"default": BridgeInstance("default", "Default", workspace, skill_file, True)}


def get_instance(instance_id: str = "default") -> BridgeInstance:
    instances = load_instances()
    if instance_id not in instances:
        raise InstanceConfigError(f"Unknown Bridge instance: {instance_id}")
    instance = instances[instance_id]
    if not instance.enabled:
        raise InstanceConfigError(f"Bridge instance is disabled: {instance_id}")
    return instance
