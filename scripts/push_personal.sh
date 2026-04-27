#!/usr/bin/env bash
# Push to your personal GitHub when the default credentials are the company account.
#
# 1) Create a token: https://github.com/settings/tokens  (classic: tick "repo")
# 2) From the repo root:
#      export GH_TOKEN=ghp_xxxxxxxx
#      bash scripts/push_personal.sh
#
# The token is only in your shell environment — it is not saved to disk by this script.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${GH_TOKEN:-}" && -z "${GITHUB_TOKEN:-}" ]]; then
  echo "Set GH_TOKEN (or GITHUB_TOKEN) to a personal GitHub PAT with 'repo' scope, then re-run."
  echo "Create token: https://github.com/settings/tokens"
  exit 1
fi

TK="${GH_TOKEN:-${GITHUB_TOKEN}}"
# Token used only for this one HTTPS push; not written to .git/config.
git push "https://HiranMadhu:${TK}@github.com/HiranMadhu/visclick.git" main
