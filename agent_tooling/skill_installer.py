"""Vercel Skills Installer with Post-Install Inspection & Auto-Repair.

Installs skills via `npx skills add <package>`, consolidates them into the
Cold Skill Vault (`~/.agents/catalog/skills/`), validates/repairs SKILL.md
frontmatter, detects hooks & scripts, and links into `~/.agents/skills/`
without duplicating files across IDEs.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from agent_tooling.profile_switcher import _create_dir_link, _is_link


_SAFE_SPEC_RE = re.compile(r"^[A-Za-z0-9._/@:\-\s]+$")


def inspect_and_repair_skill(
    skill_path: Path,
    home: Path | None = None,
    activate_now: bool = False,
) -> dict[str, Any]:
    """Inspect a skill directory and automatically fix common installation issues."""
    home = home or Path.home()
    cold_root = home / ".agents" / "catalog" / "skills"
    hot_root = home / ".agents" / "skills"
    cold_root.mkdir(parents=True, exist_ok=True)
    hot_root.mkdir(parents=True, exist_ok=True)

    repairs: list[str] = []
    warnings: list[str] = []
    hooks_detected: list[str] = []
    scripts_detected: list[str] = []

    skill_id = skill_path.name

    # 1. Consolidate real folder into Cold Vault if currently sitting directly in hot_root
    canonical_dir = cold_root / skill_id
    if skill_path.resolve().parent == hot_root.resolve() and not _is_link(skill_path):
        if canonical_dir.exists():
            shutil.rmtree(canonical_dir)
        shutil.move(str(skill_path), str(canonical_dir))
        repairs.append(f"Consolidada en Bóveda Fría ({canonical_dir}) para evitar duplicados.")
        if activate_now:
            _create_dir_link(hot_root / skill_id, canonical_dir)
            repairs.append(f"Enlazada en perfil activo vía NTFS Junction ({hot_root / skill_id}).")
        skill_dir = canonical_dir
    else:
        skill_dir = skill_path
        if activate_now and not (hot_root / skill_id).exists() and canonical_dir.exists():
            _create_dir_link(hot_root / skill_id, canonical_dir)
            repairs.append(f"Enlazada en perfil activo vía NTFS Junction ({hot_root / skill_id}).")

    # 2. Check SKILL.md presence (and recover if nested one level down)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        nested = list(skill_dir.glob("*/SKILL.md"))
        if nested:
            src_sub = nested[0].parent
            for child in list(src_sub.iterdir()):
                dst = skill_dir / child.name
                if not dst.exists():
                    shutil.move(str(child), str(dst))
            repairs.append(f"SKILL.md anidado en '{src_sub.name}/' promovido a la raíz de la skill.")
        else:
            warnings.append("No se encontró SKILL.md en la carpeta instalada.")

    # 3. Validate & auto-repair YAML frontmatter in SKILL.md
    if skill_md.exists():
        raw = skill_md.read_text(encoding="utf-8-sig", errors="replace")
        has_fm = raw.lstrip().startswith("---")
        if not has_fm:
            first_line = next((ln.strip("# ").strip() for ln in raw.splitlines() if ln.strip()), skill_id)
            desc = first_line[:140].replace('"', "'")
            fixed = f'---\nname: {skill_id}\ndescription: "{desc}"\n---\n\n' + raw
            skill_md.write_text(fixed, encoding="utf-8")
            repairs.append("Frontmatter YAML (name + description) faltante agregado automáticamente a SKILL.md.")
        else:
            parts = raw.lstrip().split("---", 2)
            if len(parts) >= 3:
                fm_block = parts[1]
                needs_fix = False
                if not re.search(r"^\s*name\s*:", fm_block, re.MULTILINE):
                    fm_block = f"\nname: {skill_id}" + fm_block
                    needs_fix = True
                if not re.search(r"^\s*description\s*:", fm_block, re.MULTILINE):
                    fm_block = fm_block.rstrip() + f'\ndescription: "Skill {skill_id} instalada desde Vercel skills."\n'
                    needs_fix = True
                if needs_fix:
                    skill_md.write_text("---" + fm_block + "---" + parts[2], encoding="utf-8")
                    repairs.append("Campos obligatorios (name/description) reparados en el frontmatter de SKILL.md.")

    # 4. Inspect hooks & scripts
    for item in skill_dir.rglob("*"):
        if not item.is_file():
            continue
        rel = str(item.relative_to(skill_dir)).replace("\\", "/")
        low = rel.lower()
        if "hook" in low:
            hooks_detected.append(rel)
            if item.suffix.lower() == ".json":
                try:
                    raw_h = item.read_text(encoding="utf-8-sig")
                    json.loads(raw_h)
                    if re.search(r'"command"\s*:\s*"[A-Za-z]:\\\\', raw_h):
                        warnings.append(
                            f"Hook {rel} contiene rutas Windows con '\\\\' que fallan en Git Bash (/usr/bin/bash). Usa barras '/'."
                        )
                except Exception as exc:
                    warnings.append(f"Hook JSON inválido en {rel}: {exc}")
        elif low.startswith("scripts/") or item.suffix.lower() in (".ps1", ".mjs", ".py", ".sh"):
            scripts_detected.append(rel)

    if hooks_detected:
        warnings.append(
            f"Hooks detectados ({len(hooks_detected)}): {', '.join(hooks_detected[:4])}. "
            "Verifica si deseas registrarlos en tu IDE (no se sobrescriben hooks existentes sin respaldo)."
        )

    return {
        "skill_id": skill_id,
        "path": str(skill_dir),
        "skill_md_ok": skill_md.exists(),
        "hooks_detected": hooks_detected,
        "scripts_detected": scripts_detected,
        "repairs_applied": repairs,
        "warnings": warnings,
        "status": "ok" if skill_md.exists() else "warn",
    }


def install_vercel_skill(
    package_spec: str,
    activate_now: bool = True,
    home: Path | None = None,
) -> dict[str, Any]:
    """Install a skill via `npx skills add` and run automatic inspection & repair."""
    home = home or Path.home()
    spec = (package_spec or "").strip()
    if not spec or not _SAFE_SPEC_RE.match(spec):
        raise ValueError("Especificación de paquete inválida. Usa formato 'owner/repo' o 'owner/repo --skill nombre'.")

    hot_root = home / ".agents" / "skills"
    cold_root = home / ".agents" / "catalog" / "skills"
    hot_root.mkdir(parents=True, exist_ok=True)
    cold_root.mkdir(parents=True, exist_ok=True)

    before_hot = {d.name for d in hot_root.iterdir() if d.is_dir()}
    before_cold = {d.name for d in cold_root.iterdir() if d.is_dir()}

    # Build safe argv list
    tokens = spec.split()
    cmd = ["npx", "--yes", "skills", "add", *tokens, "--yes"]
    if os.name == "nt":
        proc = subprocess.run(
            ["cmd", "/c", *cmd],
            capture_output=True,
            text=True,
            timeout=95,
            encoding="utf-8",
            errors="replace",
        )
    else:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=95,
            encoding="utf-8",
            errors="replace",
        )

    after_hot = {d.name for d in hot_root.iterdir() if d.is_dir()}
    after_cold = {d.name for d in cold_root.iterdir() if d.is_dir()}

    new_hot = sorted(after_hot - before_hot)
    new_cold = sorted(after_cold - before_cold)

    # Also check explicit --skill <name> or last path segment if already existed
    inspected: list[dict[str, Any]] = []
    targets: list[Path] = [hot_root / n for n in new_hot] + [cold_root / n for n in new_cold if n not in new_hot]

    if not targets:
        # Try guessing skill name from spec (e.g. --skill foo or owner/repo@foo)
        guess = None
        if "--skill" in tokens:
            idx = tokens.index("--skill")
            if idx + 1 < len(tokens):
                guess = tokens[idx + 1]
        elif "@" in tokens[0]:
            guess = tokens[0].split("@", 1)[1]
        else:
            guess = tokens[0].split("/")[-1]
        for base in (hot_root, cold_root):
            cand = base / guess
            if cand.exists() and cand.is_dir():
                targets.append(cand)
                break

    for t in targets:
        inspected.append(inspect_and_repair_skill(t, home=home, activate_now=activate_now))

    out_tail = (proc.stdout or "")[-1200:]
    err_tail = (proc.stderr or "")[-600:]

    return {
        "package": spec,
        "returncode": proc.returncode,
        "installed_count": len(inspected),
        "inspected": inspected,
        "stdout_tail": out_tail.strip(),
        "stderr_tail": err_tail.strip(),
    }
