/**
 * sync-state tests — ownership, revisions and acknowledgement semantics.
 * Executed with: node --test tests/sync-state.test.mjs
 */
import { test } from "node:test"
import assert from "node:assert/strict"
import { createSyncState } from "../sync-state.mjs"

const A = { sessionID: "owner-a", worktreeRoot: "C:/fx/repoA" }
const B = { sessionID: "owner-b", worktreeRoot: "C:/fx/repoB" }
const P1 = "C:/fx/repoA/server.js"
const P2 = "C:/fx/repoA/readme.md"
const Q = "C:/fx/repoB/other.js" // different worktree

test("completing B never processes or clears A's pending work", () => {
  const s = createSyncState()
  s.mark(A, P1)
  s.mark(B, Q)
  const snapB = s.snapshot(B)
  assert.ok(snapB)
  assert.deepEqual(snapB.paths.map((p) => p.path), [Q])
  assert.equal(s.acknowledge(snapB), 1, "B's confirmed revision removed")
  assert.deepEqual(s.snapshot(B), null)
  assert.deepEqual(s.pending(A), [P1], "A's pending intact after B completed and acked")
})

test("snapshot acknowledges superseded-confirmed revisions: concurrent edits survive", () => {
  const s = createSyncState()
  s.mark(A, P1) // rev 1
  const batch = s.snapshot(A)
  assert.equal(batch.paths[0].revision, 1)
  s.mark(A, P1) // rev 2 while dispatch is in flight
  assert.equal(s.acknowledge(batch), 0, "superseded revision cannot erase anything")
  assert.deepEqual(s.pending(A), [P1], "new revision survives the old acknowledgement")
  const batch2 = s.snapshot(A)
  assert.equal(batch2.paths[0].revision, 2, "second snapshot carries the newer revision")
  assert.equal(s.acknowledge(batch2), 1)
  assert.deepEqual(s.snapshot(A), null)
})

test("two separate executions of the same path both stay eligible (no fingerprint lockout)", () => {
  const s = createSyncState()
  const r1 = s.mark(A, P1)
  const b1 = s.snapshot(A)
  assert.equal(s.acknowledge(b1), 1)
  const r2 = s.mark(A, P1)
  assert.notEqual(r1, r2, "each edit revision is distinct and checkable")
  const b2 = s.snapshot(A)
  assert.ok(b2, "path eligible again after a new revision")
  assert.notDeepEqual(b1.id, b2.id, "batch ids differ so repeats are distinguishable")
})

test("two worktrees and two owners: zero mixing of batches", () => {
  const s = createSyncState()
  s.mark(A, P1)
  s.mark(A, P2)
  s.mark(B, Q)
  const bA = s.snapshot(A)
  const bB = s.snapshot(B)
  assert.deepEqual(bA.paths.map((p) => p.path).sort(), [P1, P2].sort())
  assert.deepEqual(bB.paths.map((p) => p.path), [Q])
  assert.equal(bA.owner, A.sessionID)
  assert.equal(bB.owner, B.sessionID)
  assert.equal(s.acknowledge(bB), 1)
  assert.deepEqual(s.pending(A).sort(), [P1, P2].sort(), "A unaffected by B's ack")
})

test("wrong-owner acknowledgement cannot erase another owner's revisions", () => {
  const s = createSyncState()
  s.mark(A, P1)
  const forged = { owner: B, paths: [{ path: P1, revision: 1 }] }
  assert.equal(s.acknowledge(forged), 0, "B's ack cannot remove A's record")
  assert.deepEqual(s.pending(A), [P1])
  // a real ack of A's snapshot still works afterwards
  assert.equal(s.acknowledge(s.snapshot(A)), 1)
  assert.deepEqual(s.pending(A), [])
})

test("null/empty handling is noop-safe", () => {
  const s = createSyncState()
  assert.equal(s.mark(null, P1), null)
  assert.equal(s.mark({ sessionID: null }, P1), null)
  assert.equal(s.mark(A, ""), null)
  assert.equal(s.snapshot(null), null)
  assert.deepEqual(s.pending(null), [])
  assert.deepEqual(s.pending("unknown-sid"), [])
  assert.deepEqual(s.snapshot(A), null, "no batch without marks")
  assert.equal(s.acknowledge(null), 0)
  assert.equal(s.acknowledge({ owner: "ghost", paths: [{ path: "x", revision: 1 }] }), 0)
})

test("same session in two worktrees never shares or acknowledges batches", () => {
  const s = createSyncState()
  const a = { sessionID: A.sessionID, worktreeRoot: "C:/fx/repoA" }
  const b = { sessionID: A.sessionID, worktreeRoot: "C:/fx/repoB" }
  s.mark(a, P1)
  s.mark(b, Q)
  const batch = s.snapshot(a)
  assert.equal(batch.worktreeRoot, a.worktreeRoot)
  s.acknowledge(batch)
  assert.deepEqual(s.pending(a), [])
  assert.deepEqual(s.pending(b), [Q])
})

test("restoring a failed generation does not overwrite a newer revision", () => {
  const s = createSyncState()
  const a = { sessionID: A.sessionID, worktreeRoot: "C:/fx/repoA" }
  s.mark(a, P1)
  s.mark(a, P2)
  const batch = s.snapshot(a)
  s.acknowledge(batch)
  const newer = s.mark(a, P1)
  s.restore(batch)
  assert.deepEqual(s.pending(a), [P2, P1].sort())
  assert.equal(s.snapshot(a).paths.find(p => p.path === P1).revision, newer)
})
