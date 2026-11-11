#!/bin/sh
# tools/snap.sh <project-dir> <comma-separated seconds> : stills into .tmp/snap, plus a contact sheet
export HYPERFRAMES_BROWSER_PATH=$(ls -d ~/.cache/ms-playwright/chromium_headless_shell-1243/*/chrome-headless-shell)
cd "$(dirname "$0")/.." && rm -rf .tmp/snap && timeout 170 npx hyperframes snapshot "$1" --at "$2" --no-end -o "$PWD/.tmp/snap" 2>&1 | grep -iE "error|warn|fail" | head -5
ls .tmp/snap | wc -l
