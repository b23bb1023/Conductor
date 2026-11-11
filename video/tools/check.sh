#!/bin/sh
# tools/check.sh <project-dir> : run `hyperframes check` and print every finding, one per line
export HYPERFRAMES_BROWSER_PATH=$(ls -d ~/.cache/ms-playwright/chromium_headless_shell-1243/*/chrome-headless-shell)
cd "$(dirname "$0")/.." && mkdir -p .tmp && timeout 300 npx hyperframes check "$1" --json --no-cache > .tmp/check.json 2>/dev/null
python3 - <<'PY'
import json
d = json.load(open(".tmp/check.json"))
out = []
def walk(o):
    if isinstance(o, dict):
        if "severity" in o and ("code" in o or "rule" in o): out.append(o)
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(d)
print("ok:", d.get("ok"), {k: d[k].get("ok") for k in ("lint", "runtime", "layout", "motion", "contrast", "craft", "audio") if isinstance(d.get(k), dict)})
for o in out:
    print(f'{o["severity"]:7s} {o.get("code") or o.get("rule"):28s} t={o.get("time", "")!s:8} {o.get("message", "")[:190]}')
PY
