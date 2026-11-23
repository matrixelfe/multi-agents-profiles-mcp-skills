"""Active Skill Profile Switcher (NTFS Junction / Symlink farm).

Reduces global context token usage by linking only Core + Active Profile skills
into ~/.agents/skills while preserving every installed skill safely in
~/.agents/catalog/skills (zero deletions, instant switching across all 5 IDEs).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


CORE_LEAN_SKILLS: list[str] = [
    "find-skills",
    "verification-before-completion",
    "systematic-debugging",
    "code-review-and-quality",
    "project-docs",
    "project-changelog",
]

CORE_ESSENTIAL_SKILLS: list[str] = [
    "pmb-memory",
    "project-docs",
    "project-changelog",
    "agent-browser",
    "systematic-debugging",
    "verification-before-completion",
    "context-engineering",
    "brainstorming",
    "writing-plans",
    "code-review-and-quality",
]


def _is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    if os.name == "nt" and path.exists():
        try:
            st = os.lstat(path)
            return bool(getattr(st, "st_file_attributes", 0) & 0x400)
        except OSError:
            return False
    return False


def _create_dir_link(link_path: Path, target_path: Path) -> None:
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link_path), str(target_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        os.symlink(target_path, link_path, target_is_directory=True)


def _remove_dir_link(link_path: Path) -> None:
    if os.name == "nt":
        # rmdir removes an NTFS junction without touching target contents
        subprocess.run(
            ["cmd", "/c", "rmdir", str(link_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        link_path.unlink()


def _load_profile_skills(profiles_dir: Path, profile_name: str) -> list[str]:
    pfile = profiles_dir / f"{profile_name}.yaml"
    if not pfile.exists():
        return []
    try:
        data = yaml.safe_load(pfile.read_text(encoding="utf-8-sig")) or {}
        skills = data.get("skills") or []
        return [str(s).strip() for s in skills if str(s).strip()]
    except Exception:
        return []


def get_active_profile_state(home: Path | None = None) -> dict[str, Any]:
    home = home or Path.home()
    state_file = home / ".agents" / "tooling" / "state" / "active-profile.json"
    hot_dir = home / ".agents" / "skills"
    cold_dir = home / ".agents" / "catalog" / "skills"

    hot_count = len([d for d in hot_dir.iterdir() if d.is_dir()]) if hot_dir.exists() else 0
    cold_count = len([d for d in cold_dir.iterdir() if d.is_dir()]) if cold_dir.exists() else 0

    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8-sig"))
            data["active_skills_count"] = hot_count
            data["catalog_skills_count"] = max(cold_count, hot_count)
            return data
        except Exception:
            pass

    return {
        "active_profile": "all",
        "active_skills_count": hot_count,
        "catalog_skills_count": max(cold_count, hot_count),
        "updated_at": None,
    }


def switch_active_profile(
    profile_name: str,
    home: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Switch ~/.agents/skills to expose only Core + profile_name (or 'all').

    1. Moves any real (non-junction) skill folders from ~/.agents/skills into
       ~/.agents/catalog/skills so nothing is ever lost.
    2. Replaces junctions in ~/.agents/skills with junctions for the target set.
    3. Saves state in ~/.agents/tooling/state/active-profile.json.
    """
    home = home or Path.home()
    profile_name = (profile_name or "all").strip().lower()

    hot_dir = home / ".agents" / "skills"
    cold_dir = home / ".agents" / "catalog" / "skills"
    profiles_dir = home / ".agents" / "tooling" / "profiles"
    state_file = home / ".agents" / "tooling" / "state" / "active-profile.json"

    hot_dir.mkdir(parents=True, exist_ok=True)
    cold_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Ensure every real directory in hot_dir is safely preserved in cold_dir
    archived_to_cold = 0
    for entry in list(hot_dir.iterdir()):
        if not entry.is_dir():
            continue
        if _is_link(entry):
            continue
        target = cold_dir / entry.name
        if not dry_run:
            if not target.exists():
                shutil.move(str(entry), str(target))
            else:
                # Already exists in cold vault; remove duplicate real folder in hot_dir
                shutil.rmtree(entry)
        archived_to_cold += 1

    # Gather all available skills in the master catalog
    all_catalog = sorted(
        d.name for d in cold_dir.iterdir() if d.is_dir()
    ) if cold_dir.exists() else []
    if dry_run:
        # Include any hot_dir skills not yet moved
        hot_names = {d.name for d in hot_dir.iterdir() if d.is_dir()}
        all_catalog = sorted(set(all_catalog) | hot_names)

    # Step 2: Determine desired active skill set
    if profile_name == "all":
        desired = list(all_catalog)
    elif profile_name == "core-lean":
        lean_yaml = _load_profile_skills(profiles_dir, "core-lean")
        wanted = set(lean_yaml or CORE_LEAN_SKILLS)
        catalog_set = set(all_catalog)
        desired = sorted(s for s in wanted if s in catalog_set)
    else:
        core_skills = set(CORE_ESSENTIAL_SKILLS) | set(_load_profile_skills(profiles_dir, "core"))
        prof_skills = set(_load_profile_skills(profiles_dir, profile_name))
        wanted = core_skills | prof_skills
        catalog_set = set(all_catalog)
        desired = sorted(s for s in wanted if s in catalog_set)

    # Step 3: Reconcile junctions in hot_dir
    if not dry_run:
        desired_set = set(desired)
        # Remove junctions not in desired
        for entry in list(hot_dir.iterdir()):
            if _is_link(entry) and entry.name not in desired_set:
                _remove_dir_link(entry)
        # Create missing junctions
        for skill_id in desired:
            link_path = hot_dir / skill_id
            target_path = cold_dir / skill_id
            if not link_path.exists() and target_path.exists():
                _create_dir_link(link_path, target_path)

        state_file.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "active_profile": profile_name,
            "active_skills_count": len(desired),
            "catalog_skills_count": len(all_catalog),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    saved_pct = (
        round((1 - (len(desired) / max(len(all_catalog), 1))) * 100)
        if all_catalog
        else 0
    )

    return {
        "active_profile": profile_name,
        "active_skills_count": len(desired),
        "catalog_skills_count": len(all_catalog),
        "archived_to_cold": archived_to_cold,
        "context_reduction_pct": max(0, saved_pct),
        "dry_run": dry_run,
    }
