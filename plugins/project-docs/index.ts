/**
 * oac.project-docs — OpenCode V2 server plugin entry for the `project-docs`
 * skill.
 *
 * This file keeps ONLY the plugin registration (`Plugin.define`, plugin id
 * and configuration loading). The executable setup — hooks and async
 * coordination — lives in `runtime.mjs`, which is importable by plain Node
 * (no SDK import) so the tests drive the exact code the plugin runs.
 *
 * Behavior summary (see runtime.mjs for details):
 * 1. On the first real user prompt of a session inside THIS instance's
 *    worktree, attach the `project-docs` skill via an `@project-docs`
 *    mention append. Skipped entirely while dry-run is ON.
 * 2. Observe successful edit/write tool calls and mark the worktree dirty.
 * 3. When a session execution succeeds with pending changes, dispatch ONE
 *    queued sync prompt — but only to a session whose CURRENT location is
 *    verifiably inside this instance's git worktree (isolation contract).
 *
 * Config (optional): project-docs.config.json next to this file —
 *   { "disabled": false, "dryRun": true, "attachOnPrompt": true, "debounceMs": 1500 }
 * ctx.options (opencode.json object form) overrides the file; defaults keep
 * dry-run ON so the pilot starts without any real documentation writes.
 *
 * runtime.log is append-only evidence. Runtime lines include iid= to
 * distinguish plugin instances; startup entries precede instance creation.
 */
import { Plugin } from "@opencode/plugin"
import { existsSync, readFileSync, appendFileSync } from "node:fs"
import { join, dirname } from "node:path"
import setupRuntime from "./runtime.mjs"

/** Append-only runtime log next to the plugin: observable evidence on disk. */
function fileLog(pluginDir, msg) {
  try {
    appendFileSync(
      join(pluginDir, "runtime.log"),
      `${new Date().toISOString()} ${msg}\n`,
    )
  } catch {}
}

function resolvePluginDir() {
  try {
    const p = decodeURIComponent(
      new URL(import.meta.url).pathname.replace(/^\/(?=[A-Za-z]:)/, ""),
    )
    return dirname(p)
  } catch {
    return "."
  }
}

export function loadConfig(ctx, pluginDir) {
  const defaults = { disabled: false, dryRun: true, attachOnPrompt: true }
  let file = {}
  try {
    const p = join(pluginDir, "project-docs.config.json")
    if (existsSync(p)) file = JSON.parse(readFileSync(p, "utf8"))
  } catch {}
  let opts = {}
  try {
    if (ctx.options && typeof ctx.options === "object") opts = ctx.options
  } catch {}
  return { ...defaults, ...file, ...opts }
}

export default Plugin.define({
  id: "oac.project-docs",
  async setup(ctx) {
    const pluginDir = resolvePluginDir()
    try {
      fileLog(pluginDir, "setup start")
    } catch {}
    try {
      const cfg = loadConfig(ctx, pluginDir)
      const runtime = await setupRuntime(ctx, { pluginDir, config: cfg })
      // Unload hook: cancel timers and subscriptions, dispose registrations.
      return () => {
        try {
          void Promise.resolve(runtime?.unload?.()).catch?.(() => {})
        } catch {}
      }
    } catch (e) {
      // Setup failure must be visible and recoverable; hooks from a previous
      // good build stay registered until this one succeeds.
      try {
        fileLog(pluginDir, `setup FAILED: ${e}`)
      } catch {}
      return undefined
    }
  },
})
