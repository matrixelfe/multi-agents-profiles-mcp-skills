/**
 * scope.mjs — session/worktree identity resolution and path authorization
 * for oac.project-docs.
 *
 * Isolation contract (from the 2026-11-09 incident plan):
 * - A session's CURRENT location is the authority; `ctx.location` NEVER
 *   completes the identity of an unknown session — it only scopes what this
 *   plugin instance may manage.
 * - The git worktree root is resolved through canonical git identity, so two
 *   worktrees of the same repository stay separate while subdirectories of
 *   one worktree share its identity.
 * - Unresolvable identity (unknown session, failed lookup, no git root)
 *   produces `null` — never a fallback.
 * - Path containment uses canonicalized paths with `path.relative`; a text
 *   prefix comparison never decides containment.
 */
import { isAbsolute, join, normalize, relative, dirname, basename } from "node:path"

/** Canonicalize a filesystem path.
 * Existing paths are real-pathed; edited paths that no longer exist are
 * canonicalized against their nearest existing ancestor (the path is first
 * lexically normalized so `..` segments never change scope silently).
 * The canonical form is uniform: absolute, forward slashes. Throws when the
 * path cannot be canonicalized — callers treat that as "unauthorized",
 * never as a fallback.
 */
export async function canonicalizePath(p, { realpath } = {}) {
  if (typeof p !== "string" || !p.trim() || !isAbsolute(p)) throw new Error("cannot canonicalize: absolute path required")
  const fs = (x) => String(x).replace(/\\/g, "/")
  const nat = normalize(String(p))
  try {
    return fs(await realpath(nat))
  } catch (error) {
    if (error?.code && error.code !== "ENOENT" && error.code !== "ENOTDIR") throw error
    // no exact realpath: walk up to the nearest existing ancestor
    let cand = nat
    const suffix = []
    for (let i = 0; i < 64; i++) {
      const parent = dirname(cand)
      if (parent === cand) break // reached the root (or drive root on win32)
      suffix.unshift(basename(cand))
      try {
        const rp = fs(await realpath(parent))
        return fs(join(rp, ...suffix))
      } catch (error) {
        if (error?.code && error.code !== "ENOENT" && error.code !== "ENOTDIR") throw error
      }
      cand = parent
    }
    throw new Error(`cannot canonicalize: ${p}`)
  }
}

/**
 * Resolve the identity scope of a session:
 *   Promise<{ sessionID, directory, worktreeRoot } | null>
 * `null` means identity unknown: never authorized, never redirected.
 */
export async function resolveSessionScope(sessionID, { getSession, findWorktreeRoot, realpath }) {
  const sid = typeof sessionID === "string" ? sessionID.trim() : ""
  if (!sid) return null
  let info = null
  try {
    info = await getSession({ sessionID: sid })
  } catch {
    return null // failed lookup: unknown identity
  }
  if (!info || typeof info !== "object") return null
  // Session.Info.location is the documented session location
  // (`Location.PublicRef { directory }`); do not trust other shapes.
  const rawDir = info?.location?.directory
  if (typeof rawDir !== "string" || !rawDir) return null
  let directory = null
  try {
    directory = await canonicalizePath(rawDir, { realpath })
  } catch {
    return null
  }
  let root = null
  try {
    root = await findWorktreeRoot(directory)
  } catch {
    root = null
  }
  if (!root || typeof root !== "string") return null // no git identity
  let worktreeRoot = null
  try {
    worktreeRoot = await canonicalizePath(root, { realpath })
  } catch {
    return null
  }
  return { sessionID: sid, directory, worktreeRoot }
}

/** Compare two already-verified, canonicalized scopes for worktree identity.
 * Canonical inputs are `path.realpath`-normalized, so case/link drift has
 * been resolved on both sides; comparisons of raw user paths are invalid. */
export function sameWorktree(leftScope, rightScope) {
  return Boolean(
    leftScope?.worktreeRoot &&
      rightScope?.worktreeRoot &&
      leftScope.worktreeRoot === rightScope.worktreeRoot,
  )
}

/** True only for canonicalized paths strictly inside the
 *  canonicalized worktree root). Windows case-insensitivity is respected
 *  for the comparison; the canonical path itself is returned unchanged. */
export function containsPath(worktreeRoot, canonicalPath) {
  if (!worktreeRoot || typeof canonicalPath !== "string" || !canonicalPath) return false
  if (canonicalPath === worktreeRoot) return false // the root itself is not an editable path
  const verdict = (a, b) => {
    try {
      const rel = relative(a, b)
      return rel !== "" && !isAbsolute(rel) && !rel.startsWith("..")
    } catch {
      return false
    }
  }
  const strict = verdict(worktreeRoot, canonicalPath)
  if (strict) return true
  // Realpath resolves existing aliases. A deleted suffix can differ in case;
  // use the native Windows path comparison policy on win32 only.
  if (process.platform === "win32") {
    return verdict(String(worktreeRoot).toLowerCase(), String(canonicalPath).toLowerCase())
  }
  return false
}
