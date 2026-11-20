/**
 * scope tests — session/worktree identity resolution and path authorization.
 *
 * Negative contract cases come first: unknown session, failed lookup,
 * session without git root, empty id, sibling repo, other worktree of the
 * same project family. Executed with: node --test tests/scope.test.mjs
 */
import { test, after } from "node:test"
import assert from "node:assert/strict"
import { mkdtempSync, mkdirSync, rmSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import {
  canonicalizePath,
  resolveSessionScope,
  sameWorktree,
  containsPath,
} from "../scope.mjs"

const BASE = mkdtempSync(join(tmpdir(), "opencode-pd-scope-"))
const dir = (...p) => join(BASE, ...p)
for (const name of ["repoA", "repoB", "wt1", "wt2"]) mkdirSync(dir(name, ".git"), { recursive: true })
mkdirSync(dir("repoA", "sub", "deep"), { recursive: true })
after(() => {
  try {
    rmSync(BASE, { recursive: true, force: true })
  } catch {}
})

const ROOT_A = dir("repoA").replace(/\\/g, "/")
const SUB_A = dir("repoA", "sub").replace(/\\/g, "/")
const DEEP_A = dir("repoA", "sub", "deep").replace(/\\/g, "/")
const ROOT_B = dir("repoB").replace(/\\/g, "/")
const WT1 = dir("wt1").replace(/\\/g, "/")
const WT2 = dir("wt2").replace(/\\/g, "/")

const GIT_ROOTS = new Map([
  [ROOT_A, ROOT_A],
  [SUB_A, ROOT_A],
  [DEEP_A, ROOT_A],
  [ROOT_B, ROOT_B],
  [WT1, WT1],
  [WT2, WT2],
])
const findWorktreeRoot = async (d) => GIT_ROOTS.get(String(d).replace(/\\/g, "/")) ?? null
const fakeRealpath = async (p) => String(p).replace(/\\/g, "/")
const realpathThrows = async () => {
  throw new Error("ENOENT")
}

const deps = { findWorktreeRoot, realpath: fakeRealpath }

// ---------- negative identity cases (must null, never fall back) ----------

test("no session id -> null", async () => {
  assert.equal(await resolveSessionScope("", deps), null)
  assert.equal(await resolveSessionScope(undefined, deps), null)
  assert.equal(await resolveSessionScope("   ", deps), null)
})

test("nonexistent session (getSession throws) -> null", async () => {
  const failing = async () => {
    throw new Error("404 no such session")
  }
  assert.equal(await resolveSessionScope("ses_missing", { ...deps, getSession: failing }), null)
})

test("session object without location.directory -> null", async () => {
  const s = async () => ({ id: "x" })
  assert.equal(await resolveSessionScope("sess-x", { ...deps, getSession: s }), null)
})

test("getSession returns null -> null", async () => {
  assert.equal(await resolveSessionScope("sess-null", { ...deps, getSession: async () => null }), null)
})

test("session without git root -> null (never inherits another instance's repo)", async () => {
  const plain = dir("plain").replace(/\\/g, "/")
  const s = async () => ({ id: "sess-plain", location: { directory: plain } })
  assert.equal(await resolveSessionScope("sess-plain", { ...deps, getSession: s }), null)
})

test("findWorktreeRoot throwing -> null (identity unknown, never fallback)", async () => {
  const s = async () => ({ id: "sess-x", location: { directory: ROOT_A } })
  const boom = async () => {
    throw new Error("git exploded")
  }
  assert.equal(await resolveSessionScope("sess-x", { ...deps, getSession: s, findWorktreeRoot: boom }), null)
})

test("sibling repo resolves to its own root, not to another instance's root", async () => {
  const s = async () => ({ id: "sess-b", location: { directory: ROOT_B } })
  assert.deepEqual(
    await resolveSessionScope("sess-b", { ...deps, getSession: s }),
    { sessionID: "sess-b", directory: ROOT_B, worktreeRoot: ROOT_B },
  )
})

// ---------- worktree identities stay separate; subdirectories join ----------

test("two worktrees of the same project family have different identities", async () => {
  const s1 = async () => ({ id: "w1", location: { directory: WT1 } })
  const s2 = async () => ({ id: "w2", location: { directory: WT2 } })
  const sc1 = await resolveSessionScope("w1", { ...deps, getSession: s1 })
  const sc2 = await resolveSessionScope("w2", { ...deps, getSession: s2 })
  assert.equal(sc1.worktreeRoot, WT1)
  assert.equal(sc2.worktreeRoot, WT2)
  assert.equal(sameWorktree(sc1, sc2), false)
})

test("subdirectory of a worktree shares its git identity", async () => {
  const s = async () => ({ id: "sub", location: { directory: SUB_A } })
  const sc = await resolveSessionScope("sub", { ...deps, getSession: s })
  assert.equal(sc.worktreeRoot, ROOT_A)
  const sRoot = async () => ({ id: "root-sess", location: { directory: ROOT_A } })
  const rootScope = await resolveSessionScope("root-sess", { ...deps, getSession: sRoot })
  assert.equal(sameWorktree(sc, rootScope), true)
})

test("sameWorktree on null/incomplete scopes is false", () => {
  assert.equal(sameWorktree(null, null), false)
  assert.equal(sameWorktree({ worktreeRoot: ROOT_A }, null), false)
  assert.equal(sameWorktree(null, { worktreeRoot: ROOT_A }), false)
})

// ---------- canonicalization ----------

test("canonicalize existing and derived-nonexistent paths", async () => {
  assert.equal(await canonicalizePath(`${ROOT_A}/a/b/c.txt`, deps), `${ROOT_A}/a/b/c.txt`)
  // missing everything under root -> canonical root prefix, later sections
  assert.equal(await canonicalizePath(SUB_A, deps), SUB_A)
})

test("lexical .. cannot escape the resolved ancestor scope", async () => {
  // x = root/ok/../outside.txt resolves lexically -> root/outside.txt
  const p = `${ROOT_A}/ok/../outside.txt`
  const canonical = await canonicalizePath(p, deps)
  assert.equal(canonical, `${ROOT_A}/outside.txt`)
  assert.equal(containsPath(ROOT_A, canonical), true, "stays inside the worktree")
  // escape across the root: lexical normalization yields the sibling repo,
  // which must NOT be contained in ROOT_A
  const escCanonical = await canonicalizePath(`${ROOT_A}/../repoB/secret.txt`, deps)
  assert.equal(escCanonical, `${BASE.replace(/\\/g, "/")}/repoB/secret.txt`)
  assert.equal(containsPath(ROOT_A, escCanonical), false)
})

test("canonicalization failure -> throw (never permissive)", async () => {
  // no realpath at all and no existing ancestor -> must throw
  await assert.rejects(() => canonicalizePath(`Z:/nowhere/else.txt`, { realpath: realpathThrows }))
})

test("empty/weird path input -> throw", async () => {
  await assert.rejects(() => canonicalizePath("", deps))
  await assert.rejects(() => canonicalizePath("   ", deps))
})

// ---------- containment by path.relative, not text prefixes ----------

test("prefix-text attacks are rejected", () => {
  assert.equal(containsPath(ROOT_A, `${ROOT_A}-evil/file.txt`), false)
  assert.equal(containsPath(ROOT_A, `${ROOT_A}/../repoB/x`), false)
  assert.equal(containsPath(ROOT_A, ROOT_A), false, "root itself is not a path")
  assert.equal(containsPath(ROOT_A, `${ROOT_A}/server.js`), true)
  assert.equal(containsPath(ROOT_A, `${SUB_A}/deep/x.md`), true)
  assert.equal(containsPath("", `${ROOT_A}/x`), false)
  assert.equal(containsPath(ROOT_A, ""), false)
})
