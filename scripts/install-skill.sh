#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
#
# Install presidio-hardened-repo as a personal Claude Code skill by symlinking
# this repository into ~/.claude/skills/. Claude Code discovers the skill from
# ~/.claude/skills/<name>/SKILL.md; the symlink keeps it versioned in git and
# updated by `git pull` — no copy step. Matches the family convention used by
# vstantch-code and vstantch-prose.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_NAME="presidio-hardened-repo"
DEST="${HOME}/.claude/skills/${SKILL_NAME}"

mkdir -p "${HOME}/.claude/skills"

if [[ -L "${DEST}" ]]; then
  echo "already linked: ${DEST} -> $(readlink "${DEST}")"
elif [[ -e "${DEST}" ]]; then
  echo "ERROR: ${DEST} exists and is not a symlink; move it aside first." >&2
  exit 1
else
  ln -s "${REPO_ROOT}" "${DEST}"
  echo "linked ${DEST} -> ${REPO_ROOT}"
fi

echo "Restart Claude Code (or start a new session) to pick up the skill."
