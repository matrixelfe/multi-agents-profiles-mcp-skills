#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLING_HOME="${HOME}/.agents/tooling"
CATALOG_HOME="${HOME}/.agents/catalog/skills"

echo "=== Installing agent-tooling v3 ==="
mkdir -p "${TOOLING_HOME}" "${CATALOG_HOME}"

cp -r "${REPO_ROOT}/profiles" "${TOOLING_HOME}/"
cp -r "${REPO_ROOT}/clients" "${TOOLING_HOME}/"
cp "${REPO_ROOT}/policy.yaml" "${TOOLING_HOME}/policy.yaml"

if [ ! -f "${TOOLING_HOME}/registry.yaml" ]; then
  cp "${REPO_ROOT}/registry.example.yaml" "${TOOLING_HOME}/registry.yaml"
  echo "Created starter registry at ${TOOLING_HOME}/registry.yaml"
fi

python3 -m pip install --quiet --upgrade PyYAML
python3 -m pip install --quiet -e "${REPO_ROOT}"

python3 -m agent_tooling scan
python3 -m agent_tooling doctor

echo "Done! Use 'agent-tooling scan|status|doctor|backup'."
