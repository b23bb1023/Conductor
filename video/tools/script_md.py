"""Write out/SCRIPT.md from the scripts, the measured voice timing and the shot notes below."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOTS = {
 "open": "Title question, underlined. A sticky note \"not a demo\" and a \"merged code\" pill. A card counts tasks up to 592, six model pills pop in with their route logos (opencode, OpenRouter, Gemini), an arrow leads to a card that counts commits up to 404. The Conductor banner lands with \"1 Opus manager\", \"up to 8 workers\" and the repo name.",
 "why": "An Opus usage bar fills and takes a LIMIT stamp. Nine free opencode models pop in, Space Bunny ringed, with a note naming the two stealth models. Three cards build, one per failure. Two agents and one file with an edit struck out and an EDIT LOST stamp. A real reply cut mid-sentence with \"exit code 0\", \"graded: completed\" and a NOT DONE stamp. Provider A with a 429 stamp, B and C idle, the queue stalled.",
 "setup": "Left to right. The Conductor box (1 Python process, standard library only, 0 dependencies). The Opus manager box (in a sandbox, plans, briefs, reviews diffs). An MCP arrow between them. The spawn_agent signature types out and role, task and files get underlined as they are named, while the real dashboard form plays beside it. Then run 1 with its worktree, branch, file list and a write-lock stamp, run 2 with \"no overlapping paths\", runs 3 to 8, and a large \"8 runs at once\".",
 "wait": "The manager box reads \"stopped. waiting.\" The command types into a terminal card. Pills for the long-poll and the exit, with what \"settled\" means. A card shows 0 turns and 0 context spent on polling. The real JSON result appears when the command exits, and state, role, model and attempts are highlighted as they are named.",
 "saving": "A long bar grows for the workers while the number counts to 4.58 B input tokens. Under it the manager's row shows a sliver and \"0 of those tokens\", with usage and context ticked. Three small code cards show what the manager sees instead (run_status, run_diff with stat_only, spawn_agent with sources), and \"pasting 18,000 characters by hand\" is struck out.",
 "roles": "Seven role cards pop in a grid, each with Conductor's own one-line description. Writers get \"writes, up to 40 files\", the three reporting roles get \"reports, never edits\", the last two get \"at round close\". An eighth dashed card shows the folder with role.toml and prompt.md and a \"no code\" note.",
 "rules": "Four numbered cards. 1 shows the real Merge, Revert and Delete buttons under \"ready to merge\". 2 shows the real \"Every change is inside the declared scope.\" banner and a branch to \"3-way merge\" or \"refuse + name the commits\". 3 shows the manager's tools with approve and reject struck out, the human-token pill and a 403 stamp. 4 shows free, subscription and a locked paid rung.",
 "steer": "A session drawn as three blocks on a time axis. A yellow marker at 8.0 s where the message is sent, a green marker at 9.5 s where it is picked up, then \"1.5 s from send to pickup\" and pills for the tool boundary and the same session.",
 "results": "A card counts runs to 592. A stacked bar splits them into 461 finished, 13 failed, 112 cancelled and 2 at a gate. 97.3% counts up beside \"461 of 474\". Three cards count 404 commits, 92 rounds and 197 agent hours. A share bar shows free 83%, subscription 9%, paid 5%, unknown 2%.",
 "models": "Ten rows of models, each with a \"?\" placeholder that turns into a success-rate bar. The five narrated rows are underlined and fill on their numbers, coloured by tier. Gemini takes an OFF THE LADDER stamp. The real datasheet entry for Space Bunny sits under the chart from the moment it is named. The other five rows fill when the datasheet is named.",
 "ladder": "A stacked bar of 481 first attempts, with timeout, rate limited and provider error popping in as named, and a large 59. A card shows the truncated reply, \"exit code 0\" struck out and a TRUNCATED stamp. Three ladder rungs with arrows. A card shows provider A with a 429 stamp and the jump to provider B. \"21 of the 59 still finished\" counts up.",
 "cache": "The real trajectory header from the dashboard, with \"cache read 3175171 (94% hit)\" ringed. \"5.2 M input tokens\". A prompt drawn as stacked blocks, three stable ones above a dashed line and the volatile ones below. A bar for 4.47 B cached against a sliver for 0.11 B uncached, and 97.6% counting up.",
 "rounds": "A flow from \"the queue drains\" to \"closes the round\" to \"commits a round report\", then out to the notes curator and the drift sentinel, which points at GOAL.md. Two real crops of the rounds panel and \"92 rounds closed\". Below, the daemon restarts and the run table is rebuilt from disk, with two pills on what happens to interrupted and gated runs.",
 "dash": "The real dashboard fills the frame. The live trajectory recording plays, then the real Scope and Diff tabs replace it as they are named, with hand-drawn rings on the tabs and a box around Merge and Revert.",
 "recap": "The title question again. A four-row matrix (isolation, scoped merges, the ladder, cache-first prompts) whose result column fills cell by cell from \"?\". 404 counts up. Pills for lines of Python, checks and dependencies, a credits line, and the repo card. Holds 2.4 s.",
 "s-hook": "\"Conductor\" title, a \"runs on any codebase\" pill with three repo pills, and a note: numbers below come from one private codebase. Three cards count up: 592 coding tasks, 197 agent hours, 404 commits on main.",
 "s-team": "Opus manager -> MCP -> Conductor -> eight opencode agent boxes. Model pills, two marked stealth. \"0 Opus usage on grunt work\". The seven role chips. One worker card with its own git worktree, files=[...] and a write-lock stamp.",
 "s-wait": "\"Opus waits\" beside the wait command typing into a terminal, then an excerpt of its real JSON output. Pills: 0 turns spent polling, context stays clean.",
 "s-cache": "~20 B tokens and 45,000+ tool calls count up, both marked as estimates calibrated to OpenRouter billing, with \"0 spent on Opus\". A prompt drawn as stacked blocks, stable above the cache boundary, task-specific below. 95.5% counts up; a cached vs uncached bar; a ringed crop of a real run's \"94% hit\" header.",
 "s-human": "A line from \"vibe coding, hands off\" to \"spoon-feeding, hands on\", both crossed out, with Conductor in the middle: autonomous until it needs me. Gate, paid model and stuck task pills flow into \"waits for me\". A real trajectory crop with \"instruct a running worker\" and \"measured: lands in 1.5 s\".",
 "s-end": "Rate limits: provider A takes a 429, the arrow skips to provider B. The real Merge and Revert buttons under \"nothing merges by itself\". Pills for Python, standard library only, 0 dependencies, 1,311 checks. The Conductor banner with the repo address.",
}
TITLE = {"long": "Detailed video, `conductor.mp4`", "short": "README video, `conductor-short.mp4`"}
ts = lambda t: f"{int(t // 60)}:{t % 60:04.1f}"
out = ["# Script and shot list", "",
       "Both videos use the Kokoro voice `af_heart` at speed 1.3. The times are the measured start of each line in the finished file. "
       "The short video was written as its own piece and shares no footage with the long one.", "",
       "Where the spoken form differs from the written one (numbers, `opencode`, `MCP`, `TOML`, `IDs`), the voice was given a phonetic spelling. The written form is shown here.", ""]
for vid in ("long", "short"):
    t = json.loads((ROOT / f"script/{vid}.timing.json").read_text())
    words = sum(len(l["text"].split()) for s in t["scenes"] for l in s["lines"])
    out += [f"## {TITLE[vid]}", "", f"Length {ts(t['total'])}. {words} words.", ""]
    for s in t["scenes"]:
        out += [f"### {ts(s['start'])} `{s['id']}`", "", "On screen. " + SHOTS[s["id"]], ""]
        out += [f"- `{ts(l['start'])}` {l['text']}" for l in s["lines"]] + [""]
(ROOT / "out/SCRIPT.md").write_text("\n".join(out))
print("wrote out/SCRIPT.md", len(out), "lines")
