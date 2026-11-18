# Multi-Agent Profiles, MCP & Skills Manager (`agent-tooling` v3)

Un gestor local, ligero, reproducible y portable para organizar **MCPs, plugins, skills y perfiles por proyecto** en múltiples IDEs y agentes de IA sin desperdiciar RAM, tiempo de arranque ni tokens de contexto.

## Clientes y Superficies Soportadas

| Cliente | Superficies | Archivo de Configuración Generado |
|---|---|---|
| **OpenCode V2** | `opencode:local` | `opencode.jsonc` (`mcp.servers.*`) |
| **OpenChamber** | `openchamber:opencode-runtime` | Hereda `opencode.jsonc` |
| **OpenAI Codex** | `codex:local` | `.codex/config.toml` (`[mcp_servers.*]`) |
| **Claude Desktop / Code** | `claude:chat`, `claude:cowork`, `claude:code-local`, `claude:code-cloud` | `.mcp.json` (solo `code-local`) |
| **Google Antigravity** | `antigravity:app`, `antigravity:ide`, `antigravity:cli` | `.agents/mcp_config.json` y `.agents/skills/` |

---

## El Problema que Resuelve

Cuando instalas decenas de servidores MCP (C++, DirectX/PIX, RenderDoc, GameDev, Scraping, DevTools, Android) y cientos de skills de forma **global**:
1. Cada sesión nueva arranca procesos pesados en segundo plano (consumiendo cientos de MB de RAM en reposo).
2. El modelo recibe decenas de schemas de herramientas y descripciones de skills irrelevantes para el proyecto actual, degradando la selección y aumentando el consumo de tokens.

### Arquitectura de 3 Capas
- **Core Global Mínimo:** `0` MCPs especializados activos por defecto; solo skills universales (`5–15` IDs).
- **Catálogo Frío (`~/.agents/catalog/skills/`):** Almacén maestro fuera del escaneo global.
- **Perfiles por Repositorio (`profiles/*.yaml`):** Activación modular y combinable (`web`, `gamedev`, `windows-native`, `android`, `research`, `reverse`, `core`, `experimental`) mediante junctions NTFS / copias verificadas y configuración nativa por cliente.

---

## Instalación Rápida

### Windows (PowerShell 5.1+)
```powershell
git clone https://github.com/esanchezpa/multi-agents-profiles-mcp-skills.git
cd multi-agents-profiles-mcp-skills
.\install.ps1
```

### Linux / macOS / WSL2
```bash
git clone https://github.com/esanchezpa/multi-agents-profiles-mcp-skills.git
cd multi-agents-profiles-mcp-skills
chmod +x install.sh && ./install.sh
```

---

## Uso Diario

### 1. Escanear el ecosistema local (solo lectura)
Descubre clientes instalados, MCPs y skills sin ejecutar ningún servidor ni modificar archivos:
```bash
python -m agent_tooling scan
python -m agent_tooling status
python -m agent_tooling doctor
```

### 2. Aplicar un perfil a un proyecto (Dry-Run por defecto)
```powershell
# Vista previa (-WhatIf por defecto, no modifica nada)
powershell -File "$env:USERPROFILE\.agents\tooling\scripts\apply.ps1" -RepoPath "C:\ruta\a\tu-proyecto" -Profiles web

# Aplicar cambios con respaldo SHA-256 automático
powershell -File "$env:USERPROFILE\.agents\tooling\scripts\apply.ps1" -RepoPath "C:\ruta\a\tu-proyecto" -Profiles gamedev,windows-native -Apply
```

### 3. Revertir cualquier cambio (Rollback Atómico)
```powershell
powershell -File "$env:USERPROFILE\.agents\tooling\scripts\rollback.ps1" -ChangeId <change-id> -Apply
```

---

## Seguridad e Invariantes
- **Sin secretos en Git ni en SQLite:** tokens, PATs y API keys se redactan automáticamente (`agent_tooling/security/redact.py`) y nunca se almacenan en `registry.sqlite3` ni en `registry.yaml`.
- **SQLite en modo seguro:** `PRAGMA foreign_keys = ON`, `journal_mode = WAL`, `busy_timeout = 5000` y copias consistentes vía `sqlite3.Connection.backup()` + `PRAGMA integrity_check`.
- **Detectar no es ejecutar:** escanear un MCP jamás inicia el servidor.

## Pruebas
```bash
python -m pytest -v
```
