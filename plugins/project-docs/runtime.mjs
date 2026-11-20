/** OpenCode V2 runtime. SDK boundaries are injectable, domain code is not.
 * Unknown identities and ambiguous execution correlation always fail closed.
 */
import { appendFileSync } from "node:fs"
import { realpath } from "node:fs/promises"
import { relative, resolve, isAbsolute, join } from "node:path"
import { randomUUID } from "node:crypto"
import { execFile } from "node:child_process"
import { canonicalizePath, resolveSessionScope, sameWorktree, containsPath } from "./scope.mjs"
import { createSyncState } from "./sync-state.mjs"

const PREFIX = "[project-docs sync]"
const EDIT_TOOLS = new Set(["edit", "write"])
const TERMINAL = new Set(["session.execution.succeeded", "session.execution.failed", "session.execution.interrupted"])
const dataOf = (event) => event?.data ?? event?.properties?.data ?? {}

export async function defaultFindWorktreeRoot(directory) {
  try {
    return await new Promise((yes, no) => execFile("git", ["-C", directory, "rev-parse", "--show-toplevel"],
      { timeout: 3000, windowsHide: true, maxBuffer: 65536 },
      (error, out) => error ? no(error) : yes(out.trim() || null)))
  } catch { return null }
}

export default async function setupRuntime(ctx, { pluginDir, config = {}, deps = {} } = {}) {
  const cfg = { dryRun: true, attachOnPrompt: true, debounceMs: 1500, ...config }
  const iid = randomUUID().slice(0, 8)
  const log = (reason, fields = {}) => {
    const line = JSON.stringify({ time: new Date().toISOString(), iid, reason, ...fields })
    // Never log exception messages, prompts, tool input, or file contents.
    try { appendFileSync(join(pluginDir, "runtime.log"), line + "\n") } catch {}
    deps.log?.({ iid, reason, ...fields })
  }
  const d = {
    getSession: (input) => ctx.session.get(input),
    findWorktreeRoot: defaultFindWorktreeRoot,
    realpath,
    registerPromptHook: (cb) => ctx.session.hook("prompt", cb),
    registerToolHook: (cb) => ctx.tool.hook("execute.after", cb),
    eventSubscribe: (opts) => ctx.event.subscribe(opts),
    sendSynthetic: typeof ctx?.session?.synthetic === "function" ? (i) => ctx.session.synthetic(i) : null,
    sendPromptQueue: (i) => ctx.session.prompt(i),
    ...deps,
  }
  if (deps.noSynthetic) d.sendSynthetic = null
  const location = deps.location?.() ?? ctx?.location
  const state = createSyncState()
  const sessions = new Map()
  const dispatches = new Map() // dispatch ID -> immutable scope/batch + admission correlation
  const runs = new Map() // session ID -> actual execution token and delivered input ownership
  const failed = new Set() // explicit ordinary prompt is required to retry a failed send/run
  const registrations = []
  const controller = new AbortController()
  let disposed = false
  let sending = false // one transport at a time per instance/worktree
  let timer = null
  const sessionState = (sid) => {
    if (!sessions.has(sid)) sessions.set(sid, { attached: false })
    const st = sessions.get(sid)
    return { ...st, origin: [...dispatches.values()].some(r => r.scope.sessionID === sid) }
  }
  const scopeOf = (sid) => resolveSessionScope(sid, d)
  let instanceScope = null
  if (!cfg.disabled) {
    try {
      const directory = await canonicalizePath(location?.directory, d)
      const root = await d.findWorktreeRoot(directory)
      if (root) instanceScope = { directory, worktreeRoot: await canonicalizePath(root, d) }
    } catch {}
  }
  log(cfg.disabled ? "disabled" : instanceScope ? "ready" : "passive-no-git", {
    worktree: instanceScope?.worktreeRoot ?? null, dryRun: cfg.dryRun,
  })
  const ownRecord = (sid) => [...dispatches.values()].find(r => r.scope.sessionID === sid)
  const authorized = (scope) => !disposed && sameWorktree(scope, instanceScope)
  const schedule = () => {
    if (timer || disposed) return
    timer = setTimeout(() => { timer = null; if (!disposed) log("pending-ready", { worktree: instanceScope?.worktreeRoot }) },
      Number.isFinite(cfg.debounceMs) && cfg.debounceMs >= 0 ? cfg.debounceMs : 1500)
    timer.unref?.()
  }
  function promptText(record) {
    const root = record.scope.worktreeRoot
    return [
      `${PREFIX} origin=oac.project-docs mode=sync dryRun=${cfg.dryRun} dispatch=${record.id}`,
      "@project-docs",
      `Run the project-docs skill in **sync** mode for this repository (${root}).`,
      `Directory precondition: before any file access verify that your current Git worktree is ${root} (subdirectories are allowed). If it differs or cannot be verified, stop without changing directory: project-docs sync -> blocked (not this worktree, dispatch=${record.id}).`,
      `Changed paths in this repo: ${record.batch.paths.slice(0, 12).map(e => relative(root, e.path).replaceAll("\\", "/")).join(", ")}.`,
      cfg.dryRun ? "DRY-RUN / PROPOSAL ONLY: do not edit any file; report the exact changes you would make." : "Apply the smallest accurate documentation updates.",
      "Follow the skill's changelog delegation rules exactly. End with its one-line report.",
    ].join("\n")
  }
  async function dispatchSync(sid) {
    if (disposed || !instanceScope || sending || ownRecord(sid) || failed.has(sid)) return
    sending = true // acquire before the first await, not after snapshotting
    let record
    try {
      const scope = await scopeOf(sid)
      if (!authorized(scope)) { log("destination-rejected", { source: sid, destination: sid }); return }
      const batch = state.snapshot(scope)
      if (!batch) return
      // Recheck every path now: a junction may have changed since capture.
      for (const { path } of batch.paths) {
        const now = await canonicalizePath(path, d)
        if (now !== path || !containsPath(scope.worktreeRoot, now)) {
          log("path-changed-before-send", { source: sid, batch: batch.id }); return
        }
      }
      record = { id: `d${randomUUID().replaceAll("-", "")}`, scope, batch, inboxID: null, run: null, accepted: false }
      record.text = promptText(record)
      dispatches.set(record.id, record)
      // Same final guard for BOTH transports. The SDK has no verified atomic
      // compare-and-send location precondition; the receiver checks again.
      const current = await scopeOf(sid)
      if (!authorized(current) || !sameWorktree(current, scope)) {
        dispatches.delete(record.id)
        log("moved-before-send", { destination: sid, batch: batch.id }); return
      }
      const input = { sessionID: sid, text: record.text, delivery: "queue",
        metadata: { projectDocs: { dispatchID: record.id, worktreeRoot: scope.worktreeRoot } } }
      const receipt = d.sendSynthetic ? await d.sendSynthetic(input) : await d.sendPromptQueue(input)
      record.inboxID = receipt?.data?.id ?? receipt?.id ?? record.inboxID
      record.accepted = true
      state.acknowledge(batch)
      log("dispatched", { worktree: scope.worktreeRoot, source: sid, destination: sid, batch: batch.id, dispatch: record.id, inbox: record.inboxID })
    } catch {
      if (record) dispatches.delete(record.id)
      failed.add(sid)
      log("send-failed-pending-preserved", { destination: sid, batch: record?.batch.id })
    } finally { sending = false }
  }
  async function promptHook(event) {
    if (disposed || !instanceScope) return
    const sid = event?.sessionID
    if (typeof sid !== "string" || !sid) return
    const scope = await scopeOf(sid)
    if (!authorized(scope)) return
    const text = event?.prompt?.text ?? ""
    if (text.startsWith(PREFIX)) {
      const id = event.metadata?.projectDocs?.dispatchID
      const record = dispatches.get(id)
      if (!record || record.scope.sessionID !== sid || !sameWorktree(record.scope, scope) || text !== record.text) {
        log("unrecognized-sync-prompt", { destination: sid }); return
      }
      return // text alone never creates an origin flag
    }
    failed.delete(sid) // explicit user input permits one retry after failure
    if (!sessions.has(sid)) sessions.set(sid, { attached: false })
    const st = sessions.get(sid)
    if (st.attached || cfg.dryRun || !cfg.attachOnPrompt) return
    if (!text.includes("@project-docs")) event.prompt.text = `${text}\n\n@project-docs (bootstrap documentation for this worktree only)`
    st.attached = true
  }
  async function toolHook(event) {
    if (disposed || !instanceScope || event?.status !== "completed" || !EDIT_TOOLS.has(event.tool)) return
    const sid = event.sessionID
    if (typeof sid !== "string" || !sid) return
    const scope = await scopeOf(sid)
    if (!authorized(scope)) return // authorize BEFORE accepting or canonicalizing the edit
    const input = event.input ?? {}
    const path = input.filePath ?? input.path ?? input.file_path
    if (typeof path !== "string" || !path) return
    const canonical = await canonicalizePath(isAbsolute(path) ? path : resolve(scope.directory, path), d)
    const fresh = await scopeOf(sid)
    if (!authorized(fresh) || !sameWorktree(scope, fresh) || !containsPath(scope.worktreeRoot, canonical)) return
    const run = runs.get(sid)
    // Ignore only a positively correlated sync-only execution. A normal run
    // while a notice is merely queued is not suppressed.
    if (run?.own.size && !run.foreignInput) return
    state.mark(scope, canonical)
    schedule()
  }
  async function eventHook(event) {
    if (disposed || !instanceScope) return
    const data = dataOf(event)
    const sid = data.sessionID
    if (typeof sid !== "string" || !sid) return
    const scope = await scopeOf(sid)
    if (!authorized(scope)) return // foreign events change no bookkeeping
    if (event.type === "session.execution.started") {
      const token = data.executionID ?? event.id
      if (token) runs.set(sid, { token, own: new Set(), foreignInput: false })
      return
    }
    if (event.type === "session.inbox.enqueued") {
      const id = data.item?.payload?.metadata?.projectDocs?.dispatchID
      const record = dispatches.get(id)
      if (record?.scope.sessionID === sid && sameWorktree(scope, record.scope)) record.inboxID = data.inboxID
      return
    }
    if (event.type === "session.inbox.delivered") {
      const run = runs.get(sid)
      if (!run) return // missing start: cannot correlate, preserve snapshots
      const record = [...dispatches.values()].find(r => r.scope.sessionID === sid && r.inboxID === data.inboxID)
      if (record) { record.run = run.token; run.own.add(record.id) }
      else run.foreignInput = true
      return
    }
    if (!TERMINAL.has(event.type)) return
    const run = runs.get(sid)
    if (run && data.executionID && run.token !== data.executionID) return
    if (run?.own.size) {
      for (const id of run.own) {
        const record = dispatches.get(id)
        if (!record || record.run !== run.token) continue
        if (event.type !== "session.execution.succeeded") {
          state.restore(record.batch)
          failed.add(sid)
          log("generation-failed-restored", { source: sid, batch: record.batch.id, dispatch: id })
        }
        dispatches.delete(id)
      }
      runs.delete(sid)
      return // never recursively sync from our own execution
    }
    runs.delete(sid)
    if (event.type === "session.execution.succeeded") await dispatchSync(sid)
  }
  function safe(fn, reason) {
    return async (...args) => { try { await fn(...args) } catch { log(reason) } }
  }
  if (!cfg.disabled && instanceScope) {
    try {
      registrations.push(await d.registerPromptHook(safe(promptHook, "prompt-hook-error")))
      registrations.push(await d.registerToolHook(safe(toolHook, "tool-hook-error")))
    } catch {
      disposed = true
      await Promise.allSettled(registrations.map(r => r?.dispose?.()))
      throw new Error("project-docs hook registration failed")
    }
  }
  const eventTask = (async () => {
    if (cfg.disabled || !instanceScope) return
    try {
      for await (const event of d.eventSubscribe({ signal: controller.signal })) {
        if (disposed) break
        await safe(eventHook, "event-handler-error")(event)
      }
    } catch { if (!disposed) log("subscription-ended-pending-preserved") }
  })()
  return {
    unload: async () => {
      if (disposed) return
      disposed = true
      controller.abort()
      clearTimeout(timer)
      await Promise.allSettled(registrations.map(r => r?.dispose?.()))
      log("unloaded", { worktree: instanceScope?.worktreeRoot })
    },
    _inspect: {
      pendingFor: sid => state.pending({ sessionID: sid, worktreeRoot: instanceScope?.worktreeRoot }),
      sessionState,
      worktreeRoot: () => instanceScope?.worktreeRoot ?? null,
      dispatches,
      eventTask,
    },
  }
}
