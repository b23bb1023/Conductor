# How the numbers were counted

All figures come from one project, from 20 August to 6 October 2026. Conductor has been used on other repositories too, but they aren't counted here.

## The cleanup, and what survived it

At some point the run store held more than 300 runs and was taking up a lot of space, so a cleanup pruned their records. Three other records survived it, and the run count is rebuilt from them:

| Source | What it holds | Runs |
|---|---|---|
| Round reports, committed to git | A table of every run in each of 92 rounds, with role, model and final state | 519 |
| The episode ledger | One line per episode, kept through prunes on purpose, from 30 August on | 481 |
| Leftover run branches | One branch per run that still has one | 33 |
| **Union of the three** | | **592** |

Runs that appear in none of the three are not counted, so 592 is a lower bound.

## Figures

| Figure | Value | How |
|---|---|---|
| Runs | 592 | Distinct run IDs across the three sources |
| Final states | 461 completed, 112 cancelled, 13 failed, 2 awaiting a gate | The round report's state where there is one, else the ledger's last outcome. 4 branch-only runs have no recorded state. |
| Finished, of runs not cancelled | 97.3% | 461 ÷ (461 + 13). Runs I cancelled are left out, because cancelling says nothing about the worker. |
| Commits on main by workers | 404 | Commits whose subject starts `worker[...]`: 365 from implementers, 39 from the notes curator |
| Rounds | 92 | Committed round reports |
| Episodes | 598 | Ledger lines. One run can take several episodes through retries. |
| Agent hours | 197 | Sum of episode wall-clock time in the ledger. It starts on 30 August, so the first ten days are missing. |
| Input tokens read from cache | 97.6% | Cached input tokens ÷ (cached + uncached input tokens), over all ledger episodes: 4.47 billion cached, 108 million uncached |
| Median per-episode cache hit | 96.6% | The ledger's per-episode ratio |
| Episodes on free-tier models | 83% | Each episode's model, looked up in the registry's tier field. 9% ran on subscriptions, 5% on paid models, 2% unknown. |
| Median finished episode | 13 minutes (p90 43) | Episodes with outcome `ok` |
| Roles used | implementer 481, notes curator 68, researcher 30, reviewer 8, auditor 1 | Round reports, plus the ledger for runs not in a report |

## The system itself, today

| | |
|---|---|
| Python, excluding vendored code and tests | about 14,100 lines, standard library only |
| Dashboard | about 2,100 lines of JavaScript, CSS and HTML, no build step |
| Tests | about 5,900 lines; 1,311 checks across 18 modules, all passing (the browser module skips without Playwright) |
| Registry | 7 roles, 6 harnesses, 33 models |

## Tokens, tool calls and cache, every codebase

The short video and the README also give figures across every codebase Conductor has run on, not just the one above.

| Figure | Value | How |
|---|---|---|
| Tokens recorded by opencode | 6.91 B | `opencode stats --all`: 742 sessions, 43,191 steps, 0.31 B uncached input, 6.57 B cached input, 18 M output, 11 M reasoning. This counts every opencode session on the machine, including runs whose Conductor records were pruned. |
| Ledger undercount | about 2.9× | For the same OpenRouter-billed models, Conductor's ledger recorded 303 M tokens and OpenRouter billed 873 M. Calls the ledger never sees, such as opencode's own background requests and retries, are the likely gap. |
| Tokens processed by workers | about 20 B | 6.91 B × 2.9. An estimate, marked with an asterisk wherever it appears. |
| Tool calls | 45,000+ | 43,191 measured steps at 1.16 tool calls per step, measured on surviving transcripts. An estimate, marked with an asterisk. |
| Cache hit per session | median 96.7%, best 99.97% | Ledger episodes with at least 200,000 input tokens: 502 sessions, 63% of them at or above 95%. The best was a Space Bunny session. Across all of opencode's lifetime stats, 95.5% of input was read from cache. |
| Thinking tokens | about 3× visible output | Measured on surviving transcripts (Space Bunny 2.9×, GLM 5.3 Flash 4.1×, DeepSeek V4.1 Flash 5.2×). Small next to input: about 43 M across the ledgers. |

None of this counts the Opus manager's own tokens, which Claude Code keeps for only 30 days.
