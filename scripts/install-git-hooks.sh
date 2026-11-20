#!/usr/bin/env bash
# Installs the cross-agent .agent-docs pre-commit hook into a target Git repository.
# Usage: ./scripts/install-git-hooks.sh <repo-path> [--apply]
set -euo pipefail

REPO_PATH="${1:-}"
APPLY="${2:-}"

if [ -z "${REPO_PATH}" ]; then
  echo "Usage: $0 <repo-path> [--apply]" >&2
  exit 1
fi

if [ ! -d "${REPO_PATH}/.git" ]; then
  echo "Error: Target path is not a Git repository (missing .git): ${REPO_PATH}" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_HOOK="${SCRIPT_DIR}/hooks/pre-commit"
DST_HOOK="${REPO_PATH}/.git/hooks/pre-commit"

if [ "${APPLY}" != "--apply" ]; then
  echo "[DRY-RUN] Would install pre-commit hook: ${SRC_HOOK} -> ${DST_HOOK}"
  echo "Re-run with --apply to install."
  exit 0
fi

mkdir -p "${REPO_PATH}/.git/hooks"
cp "${SRC_HOOK}" "${DST_HOOK}"
chmod +x "${DST_HOOK}"
echo "Installed .agent-docs pre-commit hook at ${DST_HOOK}"
