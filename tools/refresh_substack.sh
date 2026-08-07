#!/usr/bin/env bash
# Refresh the Substack posts and publish them.
#
#   ./tools/refresh_substack.sh
#
# Fetches the feed, and if anything changed, commits and pushes — GitHub Pages
# rebuilds automatically. Safe to run any time; does nothing if there are no
# new posts. Run this from your own machine: Substack blocks GitHub's servers,
# so the scheduled Action can't always do it (see README).

set -euo pipefail

cd "$(dirname "$0")/.."

python3 tools/fetch_substack.py
code=$?

if [ "$code" -eq 2 ]; then
  echo "Substack refused the request (403). Try again later."
  exit 1
fi

if [ -z "$(git status --porcelain _substack)" ]; then
  echo "Nothing new to publish."
  exit 0
fi

git add _substack
git commit -m "Refresh Substack posts"
git push
echo "Published — the site will update in about a minute."
