---
name: code-mode
description: Code-Mode execution engine (UTCP). Allows AI agents to execute multi-step tool workflows, external APIs, and MCP tools through sandboxed TypeScript code chains instead of dozens of iterative JSON function calls. Includes `utcp` CLI and MCP bridge integration.
---

# UTCP Code Mode

> **Upstream Repository:** [https://github.com/universal-tool-calling-protocol/code-mode](https://github.com/universal-tool-calling-protocol/code-mode)  
> **Packages:** `@utcp/code-mode-cli`, `@utcp/code-mode-mcp`, `@utcp/code-mode`  
> **Purpose:** Transforms LLMs from repetitive tool callers into sandboxed TypeScript code executors (67%–88% latency & token reduction).

Code Mode transforms agents from repetitive tool callers into TypeScript code executors. Instead of dumping hundreds of tools into the context window, it exposes dynamic discovery and single-pass tool chaining.

## Capabilities

1. **Batch Tool Chaining**: Execute complex sequences (e.g., fetch PR, filter comments, submit review) in 1 execution turn instead of 10-15 round trips.
2. **Dynamic Tool Discovery**: Search and import only the relevant tool schemas on demand (`utcp search`).
3. **Multi-protocol Access**: Supports HTTP/OpenAPI, local and remote MCP servers, CLIs, files, and text.
4. **Isolated Sandbox**: Code runs inside an isolated V8 runtime sandbox with safe top-level `await` and `return`.

---

## CLI Usage (`utcp`)

Use the global `utcp` CLI directly from the shell:

```bash
# Search tools & view TypeScript interfaces
utcp search "search repositories"

# List all available tool names
utcp list

# View tool details & input schemas
utcp info <tool_name>

# Execute a TypeScript tool chain
utcp run <<'EOF'
const result = await myapi.some_endpoint({ param: "value" });
return result;
EOF
```

---

## MCP Server Bridge

Code Mode is also configured as an MCP server (`code-mode`) across agents:
- **Executable**: `mcp-bridge` (or `npx -y @utcp/code-mode-mcp`)
- **Default Config**: `C:\Users\edgar\.agents\.utcp_config.json`
- **Exposed Tools**:
  - `call_tool_chain`: Run arbitrary TypeScript code with registered manuals.
  - `search_tools`: Discover available tools dynamically based on queries.
