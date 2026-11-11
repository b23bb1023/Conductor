# Script and shot list

The video uses the Kokoro voice `af_heart` at speed 1.3. The times are the measured start of each line in the finished file.

Where the spoken form differs from the written one (numbers, `opencode`, `MCP`, `TOML`, `IDs`), the voice was given a phonetic spelling. The written form is shown here.

## README video, `conductor-short.mp4`

Length 1:09.2. 205 words.

### 0:00.0 `s-hook`

On screen. "Conductor" title, a "runs on any codebase" pill with three repo pills, and a note: numbers below come from one private codebase. Three cards count up: 592 coding tasks, 197 agent hours, 404 commits on main.

- `0:00.2` Conductor runs a team of coding agents on any codebase. On one of mine: 592 tasks, 197 agent hours, and 404 commits on main.

### 0:10.3 `s-team`

On screen. Opus manager -> MCP -> Conductor -> eight opencode agent boxes. Model pills, two marked stealth. "0 Opus usage on grunt work". The seven role chips. One worker card with its own git worktree, files=[...] and a write-lock stamp.

- `0:10.4` Opus stays the manager. Over MCP it spawns up to eight opencode agents on free models like Space Bunny and GLM, so the grunt work never spends Opus usage.
- `0:20.2` Each one gets a role, its own git worktree, and a locked list of files.

### 0:24.7 `s-wait`

On screen. "Opus waits" beside the wait command typing into a terminal, then an excerpt of its real JSON output. Pills: 0 turns spent polling, context stays clean.

- `0:24.8` Then Opus waits on one shell command that returns the moment they finish, so its context stays clean.

### 0:30.9 `s-cache`

On screen. ~20 B tokens and 45,000+ tool calls count up, both marked as estimates calibrated to OpenRouter billing, with "0 spent on Opus". A prompt drawn as stacked blocks, stable above the cache boundary, task-specific below. 95.5% counts up; a cached vs uncached bar; a ringed crop of a real run's "94% hit" header.

- `0:31.0` Those agents went through about 20 billion tokens and over 45,000 tool calls, none of it spent on Opus.
- `0:37.0` Every prompt puts its stable part first: the role, the skills and the repo map. So 95 to 99.97 percent of input came straight from cache.

### 0:47.0 `s-human`

On screen. A line from "vibe coding, hands off" to "spoon-feeding, hands on", both crossed out, with Conductor in the middle: autonomous until it needs me. Gate, paid model and stuck task pills flow into "waits for me". A real trajectory crop with "instruct a running worker" and "measured: lands in 1.5 s".

- `0:47.1` It's a deliberate balance, tuned for security and speed: most work runs on its own, between Claude and Conductor.
- `0:52.8` I step in only for a gate, a paid model or a stuck task, and I can stop or steer any run at any time.

### 0:58.7 `s-end`

On screen. Rate limits: provider A takes a 429, the arrow skips to provider B. The real Merge and Revert buttons under "nothing merges by itself". Pills for Python, standard library only, 0 dependencies, 1,311 checks. The Conductor banner with the repo address.

- `0:58.8` When a run finishes, Claude checks and verifies it, then merges it or flags it for me.
- `1:03.3` Rate limits skip to the next provider, and it's all one Python process.
