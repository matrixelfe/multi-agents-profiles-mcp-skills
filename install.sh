#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLING_HOME="${HOME}/.agents/tooling"
SKILLS_HOME="${HOME}/.agents/skills"
CATALOG_HOME="${HOME}/.agents/catalog/skills"

echo "=== Installing agent-tooling v3 ==="
mkdir -p "${TOOLING_HOME}" "${SKILLS_HOME}" "${CATALOG_HOME}"

if [ -d "${REPO_ROOT}/skills" ]; then
  for skill_dir in "${REPO_ROOT}/skills"/*; do
    [ -d "${skill_dir}" ] || continue
    skill_name="$(basename "${skill_dir}")"
    if [ ! -d "${SKILLS_HOME}/${skill_name}" ]; then
      cp -r "${skill_dir}" "${SKILLS_HOME}/${skill_name}"
      echo "Installed bundled skill: ${skill_name} -> ${SKILLS_HOME}/${skill_name}"
    fi
  done
fi

cp -r "${REPO_ROOT}/profiles" "${TOOLING_HOME}/"
cp -r "${REPO_ROOT}/clients" "${TOOLING_HOME}/"
if [ -d "${REPO_ROOT}/plugins" ]; then
  cp -r "${REPO_ROOT}/plugins" "${TOOLING_HOME}/"
fi
cp "${REPO_ROOT}/policy.yaml" "${TOOLING_HOME}/policy.yaml"

if [ ! -f "${TOOLING_HOME}/registry.yaml" ]; then
  cp "${REPO_ROOT}/registry.example.yaml" "${TOOLING_HOME}/registry.yaml"
  echo "Created starter registry at ${TOOLING_HOME}/registry.yaml"
fi

GLOBAL_AGENTS="${HOME}/.agents/AGENTS.md"
if [ -f "${REPO_ROOT}/templates/AGENTS.global.md" ] && [ ! -f "${GLOBAL_AGENTS}" ]; then
  cp "${REPO_ROOT}/templates/AGENTS.global.md" "${GLOBAL_AGENTS}"
  echo "Created starter global AGENTS.md at ${GLOBAL_AGENTS}"
fi

python3 -m pip install --quiet --upgrade PyYAML
python3 -m pip install --quiet -e "${REPO_ROOT}"

python3 -m agent_tooling scan
python3 -m agent_tooling doctor

echo "Done! Use 'agent-tooling scan|status|doctor|backup'."
