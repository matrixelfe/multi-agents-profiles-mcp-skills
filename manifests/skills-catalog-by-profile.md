# Catálogo Curado de Skills por Perfil (Agent-Guided Installer)

> Este archivo es leído automáticamente por cualquier agente (Antigravity, OpenCode, Codex, Copilot, Claude) cuando un usuario dice **"instálame este repo"** y elige qué perfiles de skills desea agregar usando **Vercel `skills` (`npx skills find` / `npx skills add`)**.
>
> Todas las skills instaladas se guardan en la **Bóveda Fría (`~/.agents/catalog/skills/`)** y solo las del perfil activo se enlazan a `~/.agents/skills/` (ahorro del **93%** de tokens).

---

## 0. Buscador base (se instala siempre primero)
| Skill | Comando de instalación (`npx skills`) | Repo oficial |
|---|---|---|
| `find-skills` | `npx skills add vercel-labs/skills --skill find-skills` | https://github.com/vercel-labs/skills |

---

## 1. Core & Superpowers (Recomendado para todos)
| Skill | Comando de instalación | Repo oficial | Notas / Hooks |
|---|---|---|---|
| `superpowers` (14 skills) | `npx skills add obra/superpowers` | https://github.com/obra/superpowers | Suite completa (TDD, debugging, plans, verification) |
| `agent-browser` | `npx skills add vercel-labs/agent-browser` | https://github.com/vercel-labs/agent-browser | CLI + Skill (`npm i -g agent-browser`) |
| `pmb-memory` | `pmb connect` | https://github.com/pmb-memory/pmb | Memoria persistente cross-IDE (`pmb-shared`) |
| `project-docs` | *(Local en `skills/custom/project-docs`)* | Este repo | Incluye scripts `audit.mjs` y `check-docs.mjs` |
| `project-changelog` | *(Local en `skills/custom/project-changelog`)* | Este repo | Mantiene `.agent-docs/CHANGELOG.md` |

---

## 2. Fullstack, Frontend & UI Design (`web`)
| Skill | Comando de instalación | Repo oficial | Notas |
|---|---|---|---|
| `web-design-guidelines` | `npx skills add vercel-labs/agent-skills --skill web-design-guidelines` | https://github.com/vercel-labs/agent-skills | Auditoría UX/UI oficial de Vercel |
| `ui-ux-pro-max` | `npx skills add nextlevelbuilder/ui-ux-pro-max-skill` | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | Sistemas de diseño, tipografía e iconos SVG |
| `hallmark` | `npx skills add hallmark-design/hallmark` | https://github.com/hallmark-design/hallmark | Incluye linter `sloplint.mjs` |
| `playwright` | `npx skills find playwright` | https://skills.sh | E2E testing mantenible |

---

## 3. Ingeniería, Sistemas & Seguridad (`windows-native` / `security`)
| Skill | Comando de instalación | Repo oficial | Notas |
|---|---|---|---|
| `rust-review` | `npx skills add trailofbits/skills --skill rust-review` | https://github.com/trailofbits/skills | Auditoría Rust, `unsafe` y FFI |
| `modern-python` | `npx skills add trailofbits/skills --skill modern-python` | https://github.com/trailofbits/skills | `uv`, `ruff`, `ty`, tooling moderno |
| `security-review` | `npx skills add trailofbits/skills --skill security-review` | https://github.com/trailofbits/skills | Seguridad APIs, auth y secretos |
| `git-cleanup` | `npx skills add trailofbits/skills --skill git-cleanup` | https://github.com/trailofbits/skills | Higiene de ramas y repos |

---

## 4. GameDev & 3D (`gamedev`)
| Skill | Comando de instalación | Repo oficial | Notas |
|---|---|---|---|
| `gamedev-*` (Godot / Unity / Blender / Shaders) | `npx skills find gamedev` | https://skills.sh | Se instalan en Bóveda Fría (0 tokens en sesiones generales) |

---

## 5. Mobile — Android / iOS / Expo (`android`)
| Skill | Comando de instalación | Repo oficial | Notas |
|---|---|---|---|
| `expo` / `react-native` | `npx skills find expo` | https://skills.sh | Expo Router, Native UI, builds móviles |
| `android` | `npx skills find android` | https://skills.sh | Gradle, ADB, arquitectura Android |

---

## 6. Reverse Engineering & Auditoría Binaria (`reverse`)
| Skill | Comando de instalación | Repo oficial | Notas |
|---|---|---|---|
| `reverse-engineering` | `npx skills find reverse-engineering` | https://skills.sh | Ghidra, radare2, análisis binario y firmware |

---

## Protocolo de Inspección y Auto-Reparación Post-Instalación
Al instalar cualquier skill, el agente (o el Instalador Web de `agent-tooling ui`) **debe verificar y corregir automáticamente**:
1. **Ubicación canónica:** mover carpetas duplicadas desde `.claude/skills` o `.codex/skills` hacia la **Bóveda Fría (`~/.agents/catalog/skills/<id>`)** y crear NTFS Junction en `~/.agents/skills/<id>` solo si pertenece al perfil activo.
2. **Validación de `SKILL.md`:** comprobar que exista `SKILL.md` en la raíz de la skill con frontmatter YAML válido (`name` y `description`); si falta frontmatter, repararlo automáticamente.
3. **Detección de Hooks y Scripts:** inspeccionar si la skill trae `hooks/`, `hooks.json` o `scripts/` (`*.ps1`, `*.mjs`, `*.py`, `*.sh`), validar que sus rutas relativas existan y reportar si requiere registrar un hook en el IDE sin sobrescribir configuración existente.
4. **Reindexado:** ejecutar `agent-tooling scan` para reflejar la nueva skill en SQLite y en el Control Center UI.
