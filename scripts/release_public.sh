#!/bin/bash
# Publish the current tree as a public repository with a single commit (no history). Tracked files only, so
# runs/ and modal/url.txt (the unauthenticated endpoint URL, git-ignored since 8 Nov) are never included.
# The private repository keeps the full history; PROTOCOL.md lists the freeze and amendment commits.
# Needs gh. Usage: scripts/release_public.sh [public-repo-name]
set -euo pipefail
NAME=${1:-gemma4-compaction-audit}
SRC=$(cd "$(dirname "$0")/.." && pwd)
DEST=$(mktemp -d)/$NAME
mkdir -p "$DEST"
git -C "$SRC" archive HEAD | tar -x -C "$DEST"
HOST="coglix-labs"; HOST="${HOST}--"          # assembled so this file does not contain the literal
if grep -rq "$HOST" "$DEST"; then echo "endpoint host found in tree, aborting"; exit 1; fi
cd "$DEST"
git init -q -b main
git add -A
git commit -qm "Freshness tags on stale test evidence at compaction: code, protocol, results and action logs"
gh repo create "heilcheng/$NAME" --public --source . --remote origin --push \
  --description "Audit harness and results: freshness tags on stale test evidence at compaction, Gemma 4 12B on SWE-bench Verified"
git tag -a v1.0 -m "Paper submission version"
git push -q origin v1.0
echo "published https://github.com/heilcheng/$NAME at $(git rev-parse --short HEAD), tag v1.0; working copy $DEST"
