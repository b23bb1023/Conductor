# Lineage

Conductor started from other people's work and says so. This page records what came from where, and what was left behind on purpose.

## LongHorizon-Harness

[LongHorizon-Harness](https://github.com/AMAP-ML/LongHorizon-Harness) (MIT) is a loop-engineering system for computer-use agents. It argues that the loop around an agent matters as much as the model inside it, and backs that with benchmarks that hold the model fixed and change only the harness. That argument is why Conductor exists.

Its tree is vendored at a pinned commit, so the source can be read and diffed against upstream. The harvest:

| Upstream | Became |
|---|---|
| `adapters/cli_agent.py`, `adapters/opencode.py` | the CLI adapters |
| `trajectory_artifacts.py`, `agent_logs.py` | trajectory normalisation |
| `supervisor/control_bus.py` | the control bus |
| `provider_errors.py` | provider-error signals |
| `model_catalog.py` | the model registry |
| `webapi/events.py` | the event stream |
| `role_prompts.py`, `prompt_texts.py` | role prompt files |
| `utils/process_group.py` | process-group handling |

**Not taken:** upstream's fixed manager, executor and auditor loop. In Conductor the manager is a live Claude Code session, roles are data rather than a fixed set, and each task gets the roles it needs. The upstream loop is kept as an optional backend for subtasks that really need repeated verify-and-replan.

## Traycer

From [Traycer](https://traycer.ai)'s protocol:

- **Claims.** An agent claims a role over a scope. Write claims exclude each other; read and advisory claims overlap and are told who else is there.
- **Permission modes.** Supervised, auto-accept edits and full access, kept verbatim. Supervised is the default for anything that writes.
- **The formatter contract.** Formatters render success shapes only, and errors are typed with stable codes. One formatter renders the CLI, the MCP results and the dashboard, so a person and the manager never see different facts.
- **The skill lock.** Each skill is pinned by content hash, so "the workers have skill X" can be checked.

## Aider

[Aider](https://github.com/Aider-AI/aider)'s repository map is the established answer to "what does a model need to see of a codebase it hasn't read". Conductor builds the same kind of map with Python's own `ast` instead of tree-sitter, ranks files with PageRank over the import graph, and biases the ranking toward the task's files.

## Anthropic

- **Progressive disclosure for skills.** The prompt carries an index of skills, about a line each, not the skills themselves. An agent that sees a match opens the file. That also keeps the cacheable prefix small.
- **Dashboard performance.** Anthropic's write-up on making claude.ai faster shaped an audit of the dashboard. The first fixes shipped on 6 October.

## T3 Code

[T3 Code](https://github.com/pingdotgg/t3code)'s public source was the second reference for that audit, mainly for bounding how much of a long thread loads at once.

## opencode and Claude Code

[opencode](https://github.com/anomalyco/opencode) runs most workers. Its session resume (`-s <session-id>` restores the conversation and the tool results) is what makes steering and soft retries cheap.

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) is the manager, and the sandboxed worker. Its stream-JSON input mode accepts new user messages while it works, which is what live steering is built on.

## Conductor's own

The scheduler, the claims registry, scope-bounded merges with receipts, the escalation ladder and its provider rule, truncation detection, human-only gates, rounds and the drift sentinel, recoverability-first housekeeping, the context packer, the sandbox runner, the model datasheet and the dashboard.
