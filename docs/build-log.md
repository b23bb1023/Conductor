# Build log

Dates are 2026, taken from the private repository's history.

## Before Conductor

**7 August.** The project starts with a simpler harness: one manager session handing tasks to workers.

**12 August.** That harness gains a second backend, a ChatGPT web worker.

## Conductor's first day

**20 August.** Conductor lands in one day, in this order:

1. The LongHorizon-Harness tree, vendored so the sandbox can read it
2. Roles as data, and models chosen per call
3. The episode engine
4. The control bus, the event stream and the run store
5. Scope claims, worktrees, budgets and the ladder
6. The applier, rounds and housekeeping
7. The scheduler
8. The daemon and the MCP tools
9. The dashboard
10. The repository map, context packs, skills and worker wiring

The same evening: run history survives a restart, a dropped turn stops counting as an answer, a live episode can be steered, a command is acknowledged when it lands, deletions report what they removed, and a rate limit climbs the ladder instead of ending the run. The first round report is committed at 20:42.

The predecessor harness kept running through all of this, and its workers built parts of Conductor, such as the dashboard rebuild.

## Standing alone

**29–31 August.**

- Each model gets its own episode clock, sized to its measured pace.
- Every dependency on the predecessor is cut (30 August).
- A model datasheet joins what each model is with what it actually did here: success rate, p50 and p90 duration, tokens per second, cost per success, cache hit rate.
- A reported cost stops being treated as money spent on free endpoints.
- A merge can no longer carry an unrelated path, or claim to have landed when it didn't.

## September

- Skills for choosing a worker model, and a fourth recorded failure mode: a worker escaping its worktree.
- A fix for the git index shared with the sandbox, which Conductor had been tearing.
- Eight runs at once (25 September).
- Carried results are cut to fit instead of being dropped whole.

**29 September**, the largest hardening day:

- Merges never lose work: a three-way merge on a stale base, refusal on dirty paths, receipts, a repository-wide git lock.
- `conductor wait` blocks until runs settle, so the manager stops polling.
- Pause and instruct reach a running opencode worker, and a soft retry resumes the same session.
- One daemon per repository, with `conductor.toml` and `conductor init`.
- Only the human token can approve, reject or change a run's permission.
- Housekeeping reads merge receipts, and the episode ledger keeps the datasheet's history through prunes.

## October

**5–6 October.**

- A model hierarchy for the subscription models on the ladder.
- A dashboard performance pass: a run you left can no longer repaint the one you're on, typing survives live updates, the run board is cached, hovering preloads a run.
- Cancelling a run that never started settles it at once, and cancelling a gated run is refused.

**26 October.** An architecture map of Conductor is generated. It is the diagram in this repository.
