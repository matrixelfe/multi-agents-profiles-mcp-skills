/** Pending edits are owned by the complete (canonical worktree, session) key.
 * Snapshots are immutable capabilities: acknowledgements/restores accept only
 * objects issued by this store. New edits never lose to an older snapshot.
 */
export function createSyncState() {
  const owners = new Map()
  const issued = new WeakSet()
  let revision = 0
  let batchID = 0
  function key(scope) {
    return typeof scope?.sessionID === "string" && scope.sessionID &&
      typeof scope?.worktreeRoot === "string" && scope.worktreeRoot
      ? JSON.stringify([scope.worktreeRoot, scope.sessionID]) : null
  }
  function entries(scope, create = false) {
    const id = key(scope)
    if (!id) return null
    if (create && !owners.has(id)) owners.set(id, new Map())
    return owners.get(id) ?? null
  }
  function snapshotScope(batch) {
    return { sessionID: batch.owner, worktreeRoot: batch.worktreeRoot }
  }
  return {
    mark(scope, path) {
      if (typeof path !== "string" || !path) return null
      const pending = entries(scope, true)
      if (!pending) return null
      pending.set(path, ++revision)
      return revision
    },
    snapshot(scope) {
      const pending = entries(scope)
      if (!pending?.size) return null
      const paths = [...pending].sort(([a], [b]) => a.localeCompare(b))
        .map(([path, revision]) => Object.freeze({ path, revision }))
      const batch = Object.freeze({ id: ++batchID, owner: scope.sessionID,
        worktreeRoot: scope.worktreeRoot, paths: Object.freeze(paths) })
      issued.add(batch)
      return batch
    },
    acknowledge(batch) {
      if (!batch || !issued.has(batch)) return 0
      const pending = entries(snapshotScope(batch))
      if (!pending) return 0
      let removed = 0
      for (const { path, revision } of batch.paths) {
        if (pending.get(path) === revision) { pending.delete(path); removed++ }
      }
      return removed
    },
    restore(batch) {
      if (!batch || !issued.has(batch)) return 0
      const pending = entries(snapshotScope(batch), true)
      let restored = 0
      for (const { path, revision } of batch.paths) {
        if ((pending.get(path) ?? 0) < revision) {
          pending.set(path, revision)
          restored++
        }
      }
      return restored
    },
    pending(scope) { return [...(entries(scope)?.keys() ?? [])].sort() },
  }
}
