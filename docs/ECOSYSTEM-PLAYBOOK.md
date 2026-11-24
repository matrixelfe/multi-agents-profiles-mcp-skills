# Guía de Arquitectura, Tips, Hacks y Lecciones Aprendidas — Ecosistema Multi-IDE Agéntico

> **Manual práctico y de campo** basado en la implementación real de **Agent Tooling v3** unificando **OpenCode / OpenChamber, Codex CLI, Google Antigravity, GitHub Copilot (CLI & VS Code) y Claude Code** sobre Windows + PowerShell 5.1.

---

## 1. El Principio Rector: Single Source of Truth (SSOT) en 3 Capas

El error #1 al usar varios IDEs agénticos a la vez es copiar configuraciones, skills y reglas en cada cliente. Eso produce deriva (*drift*), duplicación y fuga de tokens.

La arquitectura que realmente escala separa el estado en **3 capas sin solapamiento**:

| Capa | Formato | Rol exclusivo | Regla de oro |
|---|---|---|---|
| **Estado observado e historial** | `SQLite` (`WAL`, `FK=ON`) | Inventario de clientes, skills, MCPs, auditoría de cambios | Nunca editar a mano; actualizar con `agent-tooling scan`. |
| **Estado deseado (Declarativo)** | `YAML` (`profiles/*.yaml`, `oac-routing.yaml`) | Qué skills y MCPs pertenecen a cada perfil y cómo enrutar modelos | Versionado en Git; **0 secretos**. |
| **Conocimiento y contratos** | `Markdown` (`AGENTS.md`, `SKILL.md`, `.agent-docs/`) | Instrucciones humanas/agénticas y documentación viva | Un solo `AGENTS.md` canónico (`~/.agents/AGENTS.md`) sincronizado vía `sync-instructions`. |

### Jerarquía de Instrucciones en 3 Capas (`sync-instructions`)
Para compartir reglas globales entre **OpenCode/OpenChamber, Codex, Claude Code, GitHub Copilot y Antigravity** sin destruir las reglas nativas de cada IDE:
1. **Capa 1 — Contrato Global Canónico (`~/.agents/AGENTS.md`):** única fuente editable para reglas universales (bóveda fría JIT, `pmb-shared`, `agent-browser`, `.agent-docs/` + `CHANGELOG.md`, `0` secretos).
2. **Capa 2 — Adaptadores Nativos con Bloque Gestionado (`BEGIN/END`):** `agent-tooling sync-instructions` inyecta o actualiza únicamente el bloque `<!-- BEGIN:UNIFIED-AGENTS --> ... <!-- END:UNIFIED-AGENTS -->` dentro de `~/.config/opencode/AGENTS.md`, `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.copilot/copilot-instructions.md` y `~/.gemini/config/plugins/oac-custom-agents/rules/AGENTS.md` (con backup SHA-256), dejando intacto todo el texto nativo de cada cliente fuera del bloque.
3. **Capa 3 — `AGENTS.md` Local del Proyecto:** cada repositorio conserva su propio `AGENTS.md` con su stack y convenciones; nunca es sobrescrito por el sincronizador global.
- **Retroalimentación en 2 velocidades:** el aprendizaje diario va a **PMB (`pmb-shared`)** para no inflar el contexto; solo los patrones recurrentes confirmados (PMB / instintos `ecc-homunculus`) se promueven a `~/.agents/AGENTS.md` y se propagan con `agent-tooling sync-instructions`.

---

## 2. El Hack de los 44,000 Tokens: Bóveda Fría + NTFS Junction Farm

### El problema silencioso
Aunque todos los IDEs modernos usan *Progressive Disclosure* (no leen el cuerpo de `SKILL.md` hasta que se invoca), **sí inyectan el nombre y la descripción de cada skill instalada en el prompt del sistema**.
- Con **343 skills globales**, solo los metadatos consumen **~44,656 tokens (223% del presupuesto de Antigravity)**, forzando al IDE a **recortar ~177 skills al azar** y encareciendo cada turno en OpenCode/Codex.

### La solución (93% de ahorro de contexto, 0 borrados)
1. **Bóveda Maestra Fría (`~/.agents/catalog/skills/`):** almacena el 100% de tus skills instaladas (359+). Nunca se borra nada.
2. **Carpeta Activa (`~/.agents/skills/`):** solo contiene **NTFS Junctions** hacia `Core + Perfil activo` (por ejemplo, **26 skills en `core`** con toda la suite *Superpowers*, bajando de **44,656 → ~3,800 tokens**, **0 excluidas**).
3. **Unión Cross-IDE sin copias (Windows):**
   En Windows no necesitas permisos de administrador para crear **NTFS Junctions** (`mklink /J`):
   ```cmd
   mklink /J "%USERPROFILE%\.gemini\config\skills" "%USERPROFILE%\.agents\skills"
   mklink /J "%USERPROFILE%\.copilot\skills"       "%USERPROFILE%\.agents\skills"
   mklink /J "%USERPROFILE%\.claude\skills"        "%USERPROFILE%\.agents\skills"
   ```
   **Hack clave:** al cambiar el perfil en `~/.agents/skills/` (con `agent-tooling switch-profile web` o el selector del Control Center UI), **los 5 IDEs se actualizan simultáneamente en < 1 segundo**.
4. **Activación Just-in-Time (JIT):** declara en tu `AGENTS.md` que cualquier agente puede leer directamente `C:\Users\edgar\.agents\catalog\skills\<skill>\SKILL.md` bajo demanda sin tenerla precargada globalmente.

---

## 3. Regla de Oro sobre Multimodelo vs. Harnesses Nativos

No cometas el error de forzar un esquema de agentes multimodelo (como **Open Agents Control / OAC**) en harnesses que gestionan sus propios modelos:

| Harness | Qué compartir | Qué dejar nativo |
|---|---|---|
| **OpenCode / OpenChamber** | Skills por perfil + `pmb-shared` + `AGENTS.md` | **OAC V3.4 completo** (19 agentes multimodelo + `oac-routing.yaml` + **Spend Guard `PAYG = DENY`**). |
| **Antigravity, Codex, Copilot, Claude** | Skills por perfil + Bóveda fría JIT + `pmb-shared` + `AGENTS.md` | **Sus propios agentes, subagentes y selector de modelos.** |

**Por qué funciona mejor así:** evita descripciones confusas (*"usa ChatGPT Web Luna"* dentro de Antigravity), ahorra tokens de subagentes duplicados y respeta las optimizaciones nativas de cada plataforma.

---

## 4. Memoria Persistente 100% Cross-IDE (`pmb-shared`)

Si trabajas en Antigravity por la mañana, Codex al mediodía y OpenChamber/Copilot por la tarde, **la memoria no puede vivir aislada por IDE**.

**Hack de configuración:**
Apunta el servidor MCP `pmb-shared` en **todos** tus clientes (`opencode.json`, `.codex/config.toml`, `.claude.json`, `~/.gemini/config/mcp_config.json`, `~/.copilot/mcp-config.json`, `%APPDATA%\Code\User\mcp.json`) exactamente al mismo binario y al mismo workspace:
```json
{
  "command": "<USER_HOME>\\.local\\bin\\pmb-mcp.EXE",
  "env": {
    "PMB_WORKSPACE": "personal",
    "PMB_CWD": "<USER_HOME>"
  }
}
```
Así una decisión arquitectónica o lección guardada desde OpenCode es recordada al instante por Antigravity, Copilot o Codex.

---

## 5. Automatización Web sin Quemar Tokens (`browser-automation`)

Los servidores MCP de navegador tradicionales (Playwright MCP / DevTools) inyectan decenas de schemas de herramientas y árboles DOM gigantescos en cada sesión.

**Estrategia escalonada recomendada:**
1. **Nivel 1 (Por defecto):** `agent-browser` (Vercel Labs) como **CLI + Skill**, usando `snapshot -i` (solo elementos interactivos con refs `@e1`, `@e2`), sesiones aisladas (`--session <id>`) y `close` al terminar.
2. **Nivel 2 (Escalamiento):** `chrome-devtools` MCP **solo** para errores de consola, tráfico HTTP/Network o perfilado de rendimiento.
3. **Nivel 3 (E2E mantenible):** Playwright Test en el repo.
4. **Nivel 4 (Apps nativas Windows):** `computer-use`.

---

## 6. Gotchas y Hacks Reales de Windows + PowerShell 5.1

Problemas reales que aparecieron en producción y cómo resolverlos de raíz:

1. **PowerShell 5.1 splatting con `@e2`:** al llamar `agent-browser fill @e2 "texto"`, PowerShell interpreta `@e2` como una tabla hash (*splatting*). **Solución:** siempre entrecomilla las referencias: `agent-browser fill '@e2' "texto"`.
2. **Rutas extendidas `\\?\C:\...`:** algunos binarios Rust/Node devuelven prefijo `\\?\` que rompe `Join-Path` en PowerShell 5.1. **Solución:** limpia con `-replace '^\\\\\?\\', ''`.
3. **UTF-8 con BOM en Python `tomllib` / `json.loads`:** PowerShell 5.1 `Set-Content -Encoding UTF8` escribe BOM y rompe `tomllib.loads()`. **Solución:** lee siempre con `encoding="utf-8-sig"` en Python.
4. **Antigravity ignorando rutas absolutas en `skills.json`:** usa rutas relativas al home (`"~/.agents/skills"`) más la NTFS Junction en `~/.gemini/config/skills`.
5. **Backups reversibles antes de tocar configs:** nunca sobrescribas un JSON/TOML de usuario sin copiar antes el original a `%LOCALAPPDATA%\agent-tooling-backups\<change-id>\` con hash SHA-256.
6. **Hooks de Claude Code en Windows (`/usr/bin/bash`):** Claude Code ejecuta los hooks mediante Git Bash. Cualquier comando en `~/.claude/settings.json` con barras invertidas sin escapar (`C:\Users\...`) será corrompido por Bash (`C:Users...: command not found`). **Solución:** usa siempre barras diagonales y comillas: `"C:/Users/.../python.exe"`.
7. **PMB MCP en `stdio` para evitar `ECONNREFUSED` y colisión en puerto `8765`:** configura `pmb-shared` siempre con `"type": "stdio"` apuntando a `pmb-mcp.EXE` (en vez de HTTP `:8765`), así nunca choca con `agent-tooling ui` ni falla si no levantaste un daemon HTTP aparte.

---

## 7. Control Center Local & Calidad de UI

Si construyes una consola web local (`http://127.0.0.1:8765`) para gobernar tu ecosistema:
- **Zero-CDN / 100% local:** HTML + CSS + SVG inline puro para que arranque en milisegundos sin internet y sin dependencias rotas.
- **Endpoints ligeros separados para telemetría:** separa `GET /api/live-ram` (polling cada 5s pausable cuando `document.hidden`) de `GET /api/snapshot` (inventario completo).
- **Aísla cada renderizador (`safeRun`):** un cambio de esquema en una sección nunca debe tumbar el resto del dashboard.
- **Control visual anti-ruido:** usa el color verde **solo** en el punto indicador vivo (`.live-beacon`), mantén los nombres de herramientas en alto contraste blanco y usa chips neutros para etiquetas repetitivas (`OK`, nombres de IDEs).
- **Quality gate automatizado:** pasa `sloplint.mjs` (`0 FAIL, 0 REFLEX, 0 WARN`) y pruebas headless en cada cambio de UI.

---

## 8. Qué Subir a GitHub y Qué NO Subir

- **SÍ subir:** motor CLI/UI, perfiles `profiles/*.yaml`, `AGENTS.md`, plantillas limpias `templates/mcp-cross-agent.json` (con `<USER_HOME>`), manifiesto curado `manifests/skills-top.yaml` (con URLs oficiales para actualizar con 1 script), scripts de junctions y tus skills propias auditadas (`0` secretos).
- **NO subir:** las 350+ carpetas completas de skills de terceros, bases `registry.sqlite3`, estados de cuota `quota-state.json`, ni archivos reales `opencode.json` / `.claude.json` / `mcp-config.json` que contengan tokens o IPs privadas.

---

## 9. Checklist Rápido para Replicar Este Ecosistema desde Cero

1. Crea `~/.agents/catalog/skills` y `~/.agents/skills`.
2. Ejecuta `scripts/install-skills.ps1` para instalar el Top curado desde sus repos oficiales.
3. Ejecuta `scripts/setup-junctions.ps1` para enlazar Antigravity, Copilot y Claude a `~/.agents/skills`.
4. Activa el perfil `core` (`agent-tooling switch-profile core`) para mantener el consumo de contexto por debajo del 20%.
5. Conecta `pmb-shared` en todos tus clientes usando `templates/mcp-cross-agent.json`.
6. Lanza `agent-tooling ui` y valida salud, RAM en vivo, perfiles y rollbacks en `http://127.0.0.1:8765`.
