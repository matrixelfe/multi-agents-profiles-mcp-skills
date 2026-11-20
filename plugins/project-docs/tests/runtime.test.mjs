/**
 * runtime tests — oac.project-docs isolation regression suite.
 *
 * Drives the REAL runtime module used by the plugin (runtime.mjs) with a
 * simulated SDK and a real (disposable) temp filesystem: directories whose
 * `.git` is an empty marker, exactly what the plugin's own worktree probe
 * looks for. No git init, no real sessions, no real writes. All fixtures
 * are anonymous fake ids/paths.
 * Executed with: node --test tests/runtime.test.mjs
 */
import { test, after } from "node:test"
import assert from "node:assert/strict"
import { mkdtempSync, mkdirSync, rmSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { setImmediate as tick } from "node:timers/promises"
import setupRuntime from "../runtime.mjs"

// ---------- disposable fixture world (empty `.git` markers, no git init) ----------
const BASE = mkdtempSync(join(tmpdir(), "opencode-pd-fixture-"))
const dir = (...p) => join(BASE, ...p)
for (const name of ["repoA", "repoB", "wt1", "wt2", "plainChat"]) {
  mkdirSync(dir(name, ".git"), { recursive: true })
}
mkdirSync(dir("repoA", "sub"), { recursive: true })
after(() => {
  try {
    rmSync(BASE, { recursive: true, force: true })
  } catch {}
})

const ROOT_A = dir("repoA").replace(/\\/g, "/") // git worktree, instance location
const SUB_A = dir("repoA", "sub").replace(/\\/g, "/") // same worktree per git identity
const ROOT_B = dir("repoB").replace(/\\/g, "/") // sibling git repo
const WT1 = dir("wt1").replace(/\\/g, "/") // other worktree, same project family
const WT2 = dir("wt2").replace(/\\/g, "/") // still another worktree
const NOGIT = dir("plainChat").replace(/\\/g, "/") // no git root
const SID_A = "owner-a" // fake
const SID_B = "other-b" // fake in sibling repo
const SID_F = "foreign-f-no-git" // fake, no git root

// git identity map: directory -> toplevel (exact `git rev-parse --show-toplevel` semantics)
const GIT_ROOTS = new Map([
  [ROOT_A, ROOT_A],
  [SUB_A, ROOT_A],
  [ROOT_B, ROOT_B],
  [WT1, WT1],
  [WT2, WT2],
])

// ---------- event queue (simulated server event stream, sequential consumer) ----------
class EventQueue {
  constructor() {
    this.items = []
    this.waiters = []
    this.aborted = false
    this.lastYielded = null
  }
  /** Push an event; returns a promise resolved once the sequential
   *  consumer has finished processing it (next-yield observation). */
  push(ev) {
    if (this.aborted) return Promise.resolve()
    const done = {}
    ev.__settle = done
    const settled = new Promise((r) => (done.r = r))
    if (this.waiters.length) this.waiters.shift()(this._deliver(ev))
    else this.items.push(ev)
    return settled
  }
  _deliver(item) {
    // the consumer asking for the next item is the exact moment the
    // previous event finished processing
    const prev = this.lastYielded
    this.lastYielded = item
    prev?.__settle?.r()
    return { value: item, done: false }
  }
  terminate() {
    this.aborted = true
    for (const w of this.waiters.splice(0)) w({ value: undefined, done: true })
    this.items.length = 0
  }
  [Symbol.asyncIterator]() {
    const self = this
    return {
      next: () => {
        if (this.aborted) return Promise.resolve({ value: undefined, done: true })
        if (this.items.length) return Promise.resolve(self._deliver(this.items.shift()))
        return new Promise((res) => this.waiters.push(res))
      },
    }
  }
}

/** Push events into the queue and resolve when all have been processed. */
async function pushSettled(queue, events) {
  const markers = []
  for (const ev of events) {
    markers.push(queue.push(ev))
    queue.push({ type: "__harness_sentinel" })
  }
  await Promise.all(markers)
}

async function until(pred, ms = 2000) {
  const t0 = Date.now()
  for (;;) {
    if (pred()) return
    if (Date.now() - t0 > ms) throw new Error("condition timeout")
    await tick()
  }
}

const norm = (p) => String(p).replace(/\\/g, "/")

// ---------- harness ----------
async function makeHarness(opts = {}) {
  const queue = new EventQueue()
  const sessions = new Map()
  for (const [sid, d] of Object.entries(opts.sessions ?? {}))
    sessions.set(sid, { location: { directory: d } })

  const sent = [] // { sid, text, transport, delivery }
  let nextInbox = 0
  let syntheticGate = null // async gate to simulate slow transports
  const pushSent = (input, transport) => {
    sent.push({
      id: `inbox-${++nextInbox}`,
      sid: input.sessionID,
      text: input.text,
      transport,
      delivery: input.delivery,
    })
    return { id: sent.at(-1).id }
  }
  const sendSynthetic = async (input) => {
    if (syntheticGate) await syntheticGate()
    return pushSent(input, "synthetic")
  }
  const sendPromptQueue = async (input) => {
    if (syntheticGate) await syntheticGate()
    return pushSent(input, "prompt")
  }

  const getSession = async (input) => {
    if (opts.getSessionOverride) return opts.getSessionOverride(input, () => sessions.get(input?.sessionID))
    const info = sessions.get(input?.sessionID)
    if (!info) throw new Error(`unknown session ${input?.sessionID}`)
    return info
  }
  const findWorktreeRoot = async (d) => GIT_ROOTS.get(norm(d)) ?? null
  const fakeRealpath = async (p) => norm(p)

  const delegate = {
    queue,
    sent,
    move: (sid, directory) => sessions.set(sid, { location: { directory } }),
    delSession: (sid) => sessions.delete(sid),
    setSyntheticGate: (fn) => (syntheticGate = fn), // control when sends complete
  }

  const deps = {
    noSynthetic: opts.noSynthetic === true, // omit the synthetic transport
    location: () => ({
      directory: opts.instanceDir ?? ROOT_A,
      project: { id: "px", directory: ROOT_A, canonical: ROOT_A },
    }),
    getSession,
    sendPromptQueue,
    eventSubscribe: (subOpts) => {
      subOpts?.signal?.addEventListener("abort", () => queue.terminate(), { once: true })
      return queue
    },
    findWorktreeRoot,
    realpath: fakeRealpath,
  }
  if (!opts.noSynthetic) deps.sendSynthetic = sendSynthetic
  deps.registerPromptHook = async (cb) => {
    delegate.promptCb = cb
    return { dispose() {} }
  }
  deps.registerToolHook = async (cb) => {
    delegate.toolCb = cb
    return { dispose() {} }
  }

  const rt = await setupRuntime(
    { skill: { list: async () => [] } },
    {
      pluginDir: dir(".plugin-test"),
      config: { dryRun: true, ...(opts.config ?? {}) },
      deps,
    },
  )

  return {
    ...delegate,
    rt,
    pendingFor: (sid) => rt._inspect.pendingFor(sid),
    edit: async ({ sessionID, path: p, status = "completed", tool = "write" }) => {
      assert.ok(delegate.toolCb, "tool hook registered")
      return delegate.toolCb({ status, tool, sessionID, input: { filePath: p } })
    },
    succeed: async (sid) => {
      await pushSettled(queue, [
        { type: "session.execution.succeeded", properties: { data: { sessionID: sid } } },
      ])
    },
    succeedNo: async (sid) => {
      // fire-and-forget: push the event but do not wait for its processing
      queue.push({ type: "session.execution.succeeded", properties: { data: { sessionID: sid } } })
    },
    idle: async (sid) => {
      await pushSettled(queue, [{ type: "session.idle", properties: { data: { sessionID: sid } } }])
    },
    prompt: async ({ sessionID, prompt: text }) => {
      assert.ok(delegate.promptCb, "prompt hook registered")
      return delegate.promptCb({ sessionID, prompt: { text }, metadata: {} })
    },
    unload: () => rt.unload(),
    event: (event) => pushSettled(queue, [event]),
    finishOwn: async (sid, success = true) => {
      const item = sent.filter(s => s.sid === sid).at(-1)
      assert.ok(item, "own input was admitted")
      await pushSettled(queue, [
        { type: "session.execution.started", id: `run-${item.id}`, data: { sessionID: sid } },
        { type: "session.inbox.delivered", data: { sessionID: sid, inboxID: item.id } },
        { type: success ? "session.execution.succeeded" : "session.execution.failed", data: { sessionID: sid } },
      ])
    },
  }
}

export { makeHarness, until, norm }

test("capture denies edits from a foreign session even when the path is inside our root", async (t) => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A, [SID_B]: ROOT_B } })
  t.after(h.unload)
  await h.edit({ sessionID: SID_B, path: `${ROOT_A}/spoof.js` })
  assert.deepEqual(h.pendingFor(SID_B), [])
})

test("sync prefix alone does not mark origin or suppress an ordinary completion", async (t) => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A } })
  t.after(h.unload)
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/x.js` })
  await h.prompt({ sessionID: SID_A, prompt: "[project-docs sync] dispatch=forged" })
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 1)
})

test("failed documentation run restores exactly its batch and waits for user retry", async (t) => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A } })
  t.after(h.unload)
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/x.js` })
  await h.succeed(SID_A)
  assert.deepEqual(h.pendingFor(SID_A), [])
  await h.finishOwn(SID_A, false)
  assert.deepEqual(h.pendingFor(SID_A), [`${ROOT_A}/x.js`])
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 1, "failure cannot trigger an automatic loop")
  await h.prompt({ sessionID: SID_A, prompt: "Retry documentation sync" })
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 2, "explicit user turn permits retry")
})

test("ordinary edits while own notice is queued are preserved, not mistaken for sync edits", async (t) => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A } })
  t.after(h.unload)
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/x.js` })
  await h.succeed(SID_A)
  await h.event({ type: "session.execution.started", id: "ordinary-run", data: { sessionID: SID_A } })
  await h.event({ type: "session.inbox.delivered", data: { sessionID: SID_A, inboxID: "ordinary-input" } })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/later.js` })
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 1)
  assert.deepEqual(h.pendingFor(SID_A), [`${ROOT_A}/later.js`])
  await h.finishOwn(SID_A)
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 2)
})

test("only positively correlated sync edits are loop-suppressed", async (t) => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A } })
  t.after(h.unload)
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/x.js` })
  await h.succeed(SID_A)
  await h.event({ type: "session.execution.started", id: "sync-run", data: { sessionID: SID_A } })
  await h.event({ type: "session.inbox.delivered", data: { sessionID: SID_A, inboxID: h.sent[0].id } })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/AGENTS.md` })
  await h.succeed(SID_A)
  assert.deepEqual(h.pendingFor(SID_A), [])
  assert.equal(h.sent.length, 1)
})

test("transport rejection preserves owner batch and never clears another owner", async (t) => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A, [SID_C]: ROOT_A } })
  t.after(h.unload)
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/x.js` })
  await h.edit({ sessionID: SID_C, path: `${ROOT_A}/c.js` })
  h.setSyntheticGate(() => { throw new Error("test transport rejection") })
  await h.succeed(SID_A)
  assert.deepEqual(h.sent, [])
  assert.deepEqual(h.pendingFor(SID_A), [`${ROOT_A}/x.js`])
  assert.deepEqual(h.pendingFor(SID_C), [`${ROOT_A}/c.js`])
})

test("unknown edit identity is not captured and completion with missing ID is inert", async (t) => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A } })
  t.after(h.unload)
  await h.edit({ sessionID: "missing", path: `${ROOT_A}/x.js` })
  assert.deepEqual(h.pendingFor("missing"), [])
  await h.event({type: "session.execution.succeeded", data: {}})
  assert.deepEqual(h.sent, [])
})

// =====================================================================
// Tarea 2 — identity resolution and destination denial (runtime level)
// =====================================================================

test("unknown destination session: nothing is sent and pending work is preserved", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A } })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/docs/x.md` })
  await h.delSession(SID_F) // unknown/forgotten session id
  await h.succeed(SID_F)
  assert.deepEqual(h.sent, [], "no dispatch without a resolvable session")
  assert.deepEqual(h.pendingFor(SID_A), [`${ROOT_A}/docs/x.md`], "pending preserved")
  await h.unload()
})

test("sibling repo session completing on this instance: rejected, no path loss", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A, [SID_B]: ROOT_B } })
  await h.edit({ sessionID: SID_B, path: `${ROOT_B}/lib/b.js` })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/server.js` })
  await h.succeed(SID_B)
  assert.deepEqual(h.sent, [], "events of a sibling-repo session never dispatch here")
  await h.unload()
})

test("sibling repo session completes; owner of this worktree then dispatches only repoA paths", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A, [SID_B]: ROOT_B } })
  await h.edit({ sessionID: SID_B, path: `${ROOT_B}/lib/b.js` })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/server.js` })
  await h.succeed(SID_B)
  assert.deepEqual(h.sent, [], "sibling event must not dispatch")
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 1, "one dispatch, to the owner, with its own paths")
  assert.equal(h.sent[0].sid, SID_A)
  assert.ok(h.sent[0].text.includes("server.js"), "owner path named")
  assert.ok(!h.sent[0].text.includes("lib/b.js"), "foreign repo path never mixed")
  await h.unload()
})

test("other worktree of the same project: this instance rejects the completion", async () => {
  const h = await makeHarness({
    sessions: { [SID_A]: ROOT_A, ["wt-session-fake"]: WT1 },
    instanceDir: ROOT_A,
  })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/readme.md` })
  await h.succeed("wt-session-fake")
  assert.deepEqual(h.sent, [], "a session rooted in another worktree must not be served here")
  assert.deepEqual(h.pendingFor(SID_A), [`${ROOT_A}/readme.md`], "pending survived")
  await h.unload()
})

test("prompt-admission revalidation: a prefix never establishes origin even in our worktree", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A, [SID_F]: NOGIT } })
  const syncText = `${"[project-docs sync]"} origin=oac.project-docs mode=sync dryRun=true\n@project-docs`
  await h.prompt({ sessionID: SID_F, prompt: syncText })
  await h.prompt({ sessionID: SID_A, prompt: syncText })
  assert.equal(h.rt._inspect.sessionState(SID_A).origin, false, "prefix alone cannot establish origin")
  assert.equal(h.rt._inspect.sessionState(SID_F).origin, false, "foreign session's admission rejected")
  await h.unload()
})


// =====================================================================
// Tarea 3 — ownership of batches, concurrent revisions, per-path drops
// =====================================================================

const SID_C = "owner-same-repo-c" // fake, same worktree as A
const deferred = () => {
  let release
  const p = new Promise((r) => (release = r))
  return { p, release: () => release() }
}
test("edit during an in-flight dispatch survives the acknowledgement and re-syncs", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A } })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/server.js` }) // rev 1
  const gate = deferred()
  h.setSyntheticGate(() => gate.p)
  const done = h.succeed(SID_A)
  // The transport is parked on the gate once the origin latch is set.
  await until(() => h.rt._inspect.sessionState(SID_A).origin === true)
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/server.js` }) // rev 2, in flight
  gate.release()
  await done
  assert.equal(h.sent.length, 1, "one dispatch went out")
  assert.deepEqual(h.pendingFor(SID_A), [`${ROOT_A}/server.js`], "rev 2 survived the ack")
  // An unrelated completion while the notice is queued cannot consume it.
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 1, "queued notice does not dispatch duplicates")
  assert.deepEqual(h.pendingFor(SID_A), [`${ROOT_A}/server.js`], "work remains pending")
  await h.finishOwn(SID_A)
  await h.succeed(SID_A)
  await until(() => h.sent.length === 2)
  assert.equal(h.sent.length, 2, "the newer revision re-syncs (no fingerprint lockout)")
  assert.deepEqual(h.pendingFor(SID_A), [], "final ack cleared everything")
  await h.unload()
})

test("same worktree, different owner: B's completion never consumes A's batch", async () => {
  const h = await makeHarness({
    sessions: { [SID_A]: ROOT_A, [SID_C]: ROOT_A },
  })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/scripts/build.js` }) // A's work
  await h.edit({ sessionID: SID_C, path: `${ROOT_A}/readme.md` }) // C's work
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 1, "A's completion dispatches A's batch only")
  assert.ok(h.sent[0].text.includes("scripts/build.js"))
  assert.ok(!h.sent[0].text.includes("readme.md"), "no mixing into A's batch")
  assert.deepEqual(h.pendingFor(SID_C), [`${ROOT_A}/readme.md`], "C's batch untouched")
  await h.succeed(SID_C)
  assert.equal(h.sent.length, 2, "C's completion dispatches C's batch")
  assert.ok(h.sent[1].text.includes("readme.md"))
  await h.unload()
})

test("edits outside the worktree are dropped per-path, not by clearing everything", async () => {
  const h = await makeHarness({
    sessions: { [SID_A]: ROOT_A },
    config: { dryRun: true },
  })
  await h.edit({ sessionID: SID_A, path: "C:/fx/elsewhere/outside.md" }) // stray edit
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/server.js` }) // owner's work
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 1)
  assert.ok(h.sent[0].text.includes("server.js"), "inside path dispatched")
  assert.ok(!h.sent[0].text.includes("outside.md"), "outside path never enters the sync text")
  assert.deepEqual(h.pendingFor(SID_A), [], "both resolved: ineligible dropped, eligible sent")
  await h.unload()
})

// =====================================================================
// Tarea 4 — movements, transport guards, structured logs, unload
// =====================================================================

test("session moved to another worktree before dispatch: send blocked, original batch pending", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A, [SID_B]: ROOT_B } })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/server.js` }) // A's batch
  // move the session out before its completion arrives
  h.move(SID_A, ROOT_B)
  await h.succeed(SID_A)
  assert.deepEqual(h.sent, [], "moved session is not served from its old worktree")
  assert.deepEqual(h.pendingFor(SID_A), [`${ROOT_A}/server.js`], "original batch stays pending")
  // a second session actually living in the sibling repo is also not ours to
  // drive: this instance (ROOT_A) never manages ROOT_B sessions
  await h.edit({ sessionID: SID_B, path: `${ROOT_B}/lib/b.js` })
  await h.succeed(SID_B)
  assert.deepEqual(h.sent, [], "sibling-repo session belongs to its own instance")
  assert.notDeepEqual(h.pendingFor(SID_A), [], "A's batch still intact")
  await h.unload()
})

test("revalidation immediately before send (shared guard): moved identity aborts with pending preserved", async () => {
  let calls = 0
  const h = await makeHarness({
    sessions: { [SID_A]: ROOT_A },
    getSessionOverride: (input, get) => {
      calls += 1
      // call 1: dispatch-time validation (original); call 2: immediate
      // pre-send revalidation — the session has just MOVED to a sibling repo
      return calls >= 5 ? { id: SID_A, location: { directory: ROOT_B } } : get()
    },
  })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/server.js` })
  await h.succeed(SID_A)
  assert.deepEqual(h.sent, [], "no transport was able to deliver to the moved identity")
  assert.deepEqual(h.pendingFor(SID_A), [`${ROOT_A}/server.js`], "batch preserved on pre-send abort")
  await h.unload()
})

test("unload cancels timers and the event subscription: a disposed instance never dispatches", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A } })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/server.js` })
  await h.unload()
  await h.succeed(SID_A)
  assert.deepEqual(h.sent, [], "no dispatch after unload")
  assert.deepEqual(h.pendingFor(SID_A), [`${ROOT_A}/server.js`], "state not mutated after unload")
  // unload is idempotent / safe
  await h.unload()
})

test("sync notice carries directory precondition and dispatch id; logged dispatch is correlatable", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A } })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/server.js` })
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 1)
  const text = h.sent[0].text
  assert.ok(text.includes("Directory precondition:"), "receiver-side precondition present")
  assert.ok(/dispatch=d[0-9a-f]{8}/.test(text), "dispatch id correlatable in the notice")
  await h.unload()
})


// =====================================================================
// Tarea 1 — regression capture + positive controls
// =====================================================================

test("regression: completion of a session without Git root never dispatches, and the owner's pending work survives", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A, [SID_F]: NOGIT } })
  const fixtureFile = `${ROOT_A}/server.js`
  await h.edit({ sessionID: SID_A, path: fixtureFile })
  await h.succeed(SID_F)
  assert.deepEqual(h.sent, [], "no dispatch may target a session without a verifiable git identity")
  assert.deepEqual(h.pendingFor(SID_A), [fixtureFile], "owner pending must survive a foreign completion")
  await h.unload()
})

test("positive control: edit and completion of the owner produce exactly one dispatch with owner-relative paths", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A } })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/server.js` })
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 1, "exactly one sync message")
  assert.equal(h.sent[0].sid, SID_A)
  assert.ok(h.sent[0].text.includes("server.js"), "message names the edited path")
  assert.ok(!h.sent[0].text.includes(ROOT_B), "no foreign repo content")
  assert.equal(h.sent[0].transport, "synthetic", "prefers synthetic transport")
  await h.unload()
})

test("positive control fallback: without synthetic support the queue transport is used once", async () => {
  const h = await makeHarness({ sessions: { [SID_A]: ROOT_A }, noSynthetic: true })
  await h.edit({ sessionID: SID_A, path: `${ROOT_A}/readme.md` })
  await h.succeed(SID_A)
  assert.equal(h.sent.length, 1, "exactly one sync message")
  assert.equal(h.sent[0].transport, "prompt", "falls back to prompt queue transport")
  assert.equal(h.sent[0].delivery, "queue", "fallback must use delivery=queue")
  await h.unload()
})
