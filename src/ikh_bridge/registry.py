"""Discover Skills in a configured local directory."""
from __future__ import annotations

import os
from pathlib import Path

from .manifest import ManifestError, SkillSpec, load_skill


def default_library() -> Path:
    override = os.environ.get("IKH_BRIDGE_SKILLS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    # 1. In standalone repo / package: check repo root / skills or relative ./skills
    package_dir = Path(__file__).resolve().parent  # src/ikh_bridge
    repo_root = package_dir.parents[1]  # ikh-local-bridge
    if (repo_root / "skills").is_dir():
        return repo_root / "skills"
    
    # 2. Check current working directory ./skills
    cwd_skills = Path.cwd().resolve() / "skills"
    if cwd_skills.is_dir():
        return cwd_skills

    # 3. Check legacy monorepo layout (parents[3] / skills)
    monorepo_skills = Path(__file__).resolve().parents[3] / "skills"
    if monorepo_skills.is_dir():
        return monorepo_skills

    # 4. Default user-level skill library: ~/.ikh-skills
    user_skills = Path.home() / ".ikh-skills"
    return user_skills



def discover_skills(library: Path | None = None) -> tuple[list[SkillSpec], list[dict[str, str]]]:
    library = (library or default_library()).expanduser().resolve()
    found: list[SkillSpec] = []
    errors: list[dict[str, str]] = []
    if not library.is_dir():
        return found, [{"path": str(library), "error": "Skill library directory does not exist"}]

    for child in sorted(library.iterdir(), key=lambda p: p.name.casefold()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if not (child / "SKILL.md").is_file() and not (child / "skill.json").is_file():
            continue
        try:
            found.append(load_skill(child))
        except ManifestError as exc:
            errors.append({"path": child.name, "error": str(exc)})
    return found, errors
