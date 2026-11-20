# Agent-Guided Installation Protocol (`INSTALL-WITH-AGENT.md`)

> **Instrucción para agentes AI (Antigravity, OpenCode/OpenChamber, Codex, GitHub Copilot, Claude):**
> Cuando un usuario te diga **"instálame este repo"**, **"configura este framework"** o apunte a `multi-agents-profiles-mcp-skills`, **SIGUE ESTE FLUJO INTERACTIVO PASO A PASO** (no instales ciegamente 350 skills ni omitas la selección por perfil).

---

## Paso 1: Instalar el Framework Base
1. Verifica Python 3.11+ y Node.js 20+.
2. Instala el paquete editable:
   ```powershell
   pip install -e .
   ```
3. Copia las skills propias limpias (`skills/custom/*`) hacia `~/.agents/catalog/skills/` y crea la estructura base `~/.agents/skills/` + `~/.agents/tooling/`.
4. En Windows, ejecuta `scripts/setup-junctions.ps1` para enlazar **Antigravity** (`~/.gemini/config/skills`), **GitHub Copilot** (`~/.copilot/skills`) y **Claude** (`~/.claude/skills`) hacia `~/.agents/skills` vía NTFS Junctions (respaldando cualquier carpeta previa).
5. Instala primero el buscador oficial de Vercel Skills (`find-skills`):
   ```powershell
   npx --yes skills add vercel-labs/skills --skill find-skills --yes
   ```

---

## Paso 2: Preguntar al Usuario qué Tipos de Skills Quiere Agregar
**ANTES** de instalar paquetes de skills de terceros (ya que este repositorio no incluye copias pesadas de terceros para mantenerse ligero y actualizado), **pregunta explícitamente al usuario** qué categorías o perfiles desea instalar (puede elegir **una, varias o todas**):

1. **Core & Superpowers** *(Recomendado)*: memoria `pmb-memory`, `agent-browser`, suite completa `superpowers` (14 skills), `project-docs`, `project-changelog`.
2. **Fullstack, Frontend & UI (`web`)**: `web-design-guidelines`, `ui-ux-pro-max`, `hallmark`, Playwright/React/Tailwind.
3. **Ingeniería, Sistemas & Seguridad (`windows-native`)**: `rust-review`, `modern-python`, `security-review`, `git-cleanup`.
4. **GameDev & 3D (`gamedev`)**: Godot, Unity, Unreal, shaders y modelado procedural.
5. **Mobile — Android / iOS / Expo (`android`)**: Expo Router, Native UI, Gradle, ADB.
6. **Reverse Engineering & Auditoría (`reverse`)**: análisis binario, Ghidra, radare2.
7. **Todo**: instala todos los paquetes en la **Bóveda Fría (`~/.agents/catalog/skills/`)** y deja activo únicamente el perfil `core` (~26 skills) para conservar el **93% de ahorro en tokens**.

---

## Paso 3: Instalar con Vercel `skills` + Inspeccionar y Auto-Reparar
1. Consulta el catálogo ligero [manifests/skills-catalog-by-profile.md](manifests/skills-catalog-by-profile.md) para las opciones elegidas por el usuario.
2. Ejecuta los comandos `npx skills add ...` (o busca adicionales con `npx skills find <tema>` si el usuario pide un dominio específico).
3. Por cada skill instalada, **inspecciona y corrige automáticamente**:
   - **Consolidación en Bóveda Fría:** mueve copias sueltas hacia `~/.agents/catalog/skills/<id>` para evitar duplicados entre IDEs.
   - **Frontmatter `SKILL.md`:** verifica que `SKILL.md` tenga `name` y `description` YAML válidos (y repara si falta).
   - **Hooks y Scripts:** detecta si la skill incluye `hooks/`, `hooks.json` o `scripts/` (`*.ps1`, `*.mjs`, `*.py`, `*.sh`), verifica rutas/sintaxis e informa al usuario si requiere activar algún hook en su IDE (nunca sobrescribe hooks existentes sin backup).
4. Activa el perfil elegido (por defecto `core`) con `switch_active_profile('core')` o desde el Control Center Web.

---

## Paso 4: Validar y Lanzar el Control Center
1. Ejecuta `agent-tooling scan` y `agent-tooling doctor`.
2. Ofrece conectar **`pmb-shared`** (memoria persistente cross-IDE) usando [templates/mcp-cross-agent.json](templates/mcp-cross-agent.json) si `pmb.exe` está instalado.
3. Lanza `agent-tooling ui` (`http://127.0.0.1:8765`) y muestra al usuario que también puede buscar, instalar y auto-reparar nuevas skills desde la pestaña **Skills y MCPs vivos → Instalador Vercel**.
