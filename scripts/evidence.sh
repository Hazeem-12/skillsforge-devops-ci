#!/usr/bin/env bash
# Creates the evidence on GitHub: one green run and three deliberately failing PRs.
# Usage: gh auth login; ./scripts/evidence.sh   (run from the repo root, after pushing main)
set -euo pipefail
base=$(git rev-parse --abbrev-ref HEAD)

mk_pr() {  # name, file edit command, commit message
  git checkout -q main && git checkout -q -b "$1"
  eval "$2"
  git commit -qam "$3" && git push -q -u origin "$1"
  gh pr create --base main --head "$1" --title "$3" --body "Fails on purpose to show fail-fast behaviour."
  git checkout -q main
}

mk_pr fail-lint  "echo 'import os' >> app/main.py" "Fail on purpose: lint error"
mk_pr fail-test  "sed -i 's/return a + b/return a - b/' app/main.py" "Fail on purpose: failing test"
mk_pr fail-build "sed -i 's/^name = .*/name = /' pyproject.toml" "Fail on purpose: broken build"

echo "Cold/warm: re-run the latest main run with: gh run rerun <run-id>  (same commit => cache hit)"
gh run list --limit 10
