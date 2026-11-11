# Design decisions

Each rule here came from a failure I saw, and each one is held by a test. The tests state what a check protects, not what it does, so nobody later deletes them as decoration.

## The run lock never covers I/O

The global lock guards the in-memory run table and slot counts. It is never held across a subprocess, a git call or a file write. A tracked lock turns this into an assertion: in strict mode it raises when broken. The suite measures p99 `/health` latency under load, so a regression shows up as a number.

## Nothing auto-merges

A finished run leaves its work on its branch, and someone decides. The merge takes the branch's version of each declared path onto HEAD. It deliberately doesn't use `git merge`, which would bring along whatever the worker left outside its scope.

## A merge never loses anyone's work

Every run records the commit it started from. For each scoped file:

- If main hasn't touched it since then, the branch's version lands.
- If main changed it, Conductor merges three ways (base, main, branch).
- If that conflicts, the merge is refused, naming the file and the main commits that touched it.
- If the main checkout has uncommitted or staged edits to it, the merge is refused. It never overwrites them.

The new tree is built on a private index. The main checkout isn't touched until HEAD moves by compare-and-swap, and a receipt (`merge.json`: commit, base, branch tip, files) is written at that moment. Merging the same unchanged run twice is refused. Reverts and round-report commits are built the same way, so an operator's staged files never ride along.

## The manager cannot clear a human's gate

The MCP server has no approve tool and no reject tool, and the daemon enforces it. `approve`, `reject` and permission changes are accepted only with the human token, which lives outside the repository. The shared agent token, readable by the manager, the runner and every worker, gets a 403. A manager that could approve its own delegate's work would make every gate decorative.

## Write scopes are exclusive; read scopes are not

Two writers on overlapping paths lose an edit at merge, silently. A reader can share the files and is told who else holds them. A reviewer that can't read the code under review is useless exactly when it matters.

## A stream that stops is not an answer

A reviewer once returned "Let me look at the actual import lines in cli.py and verify the classification, then do the full edge", cut off mid-word, with exit code 0, and it was recorded as completed. Now an episode whose last step has no clean stop reason, or which ends on a tool call with no result, is `truncated` and retried. Both checks read structured records, so no text can trip them.

## A rate limit climbs; it does not park

Retrying the model that just refused spends the cap that refused it. A different provider has a different cap. The ladder therefore skips every rung on the refusing provider, because the allowance belongs to the account, not the model.

## Money is never spent automatically

A paid model is never chosen by the ladder. When the free rungs run out, the run parks and a person decides. A paid model also never retries on its own, because a retry starts from a cold cache and bills the whole prompt again. Measured on 29 August: an automatic second attempt on a paid model spent 51,781 full-price input tokens to produce 217 output tokens before it was stopped.

## A run outlives the daemon that started it

The run table is rebuilt from disk at start, newest first and bounded. A run whose owning process is still alive is skipped, because two schedulers driving one run would double-spend its budget. A gated run survives as gated and keeps its claim. Everything else in flight settles as `interrupted`.

## Never report an action you did not take

A command is receipted `queued` when it lands, `delivering` when it is handed over, and `applied` only when the agent echoes it back. A deletion names what it actually removed: git refuses to delete a branch checked out in a worktree and doesn't say so, and a cleanup that overclaims is worse than one that fails.

## Never delete the only way back

An unmerged branch is the only copy of its work. Housekeeping checks recoverability before age, so an old run holding unmerged work is kept. "Merged" is read from the merge receipt, not from git: a scoped merge builds a new commit, so the worker branch is never an ancestor of HEAD. A branch that has to be force-deleted is bundled to an archive first.

## The harness cannot be rebuilt by the workers it supervises

`conductor/`, `.conductor/`, `.git/` and `.ssh/` are permanently denied to workers, matched on every path component. Each refusal says why that prefix is protected, so the worker and the person reading its report learn the rule.

## Reviews are never round members

A curator that joined the round it reviews would close the next round by merging, start another curator, and loop forever.

## Measured, then not built

- **A disk cache for the repository map.** Building the map takes 0.77 s cold and 0.05 s warm. A cache would save about 0.7 s once per daemon start, in exchange for an invalidation problem and a git hook.

## Small rules that cost an incident each

- **Port guard.** On macOS, `SO_REUSEADDR` lets a second server share a live port, so a stray daemon started from a worktree once shadowed the real dashboard. `serve` now probes without that flag first, and fails loudly with the `lsof` command to find the holder.
- **No ports from workers.** That stray daemon came from a reviewer told to "check the web page works". Every prompt now carries a standing rule against binding ports.
- **Read-only at the source.** Roles that only report run on opencode's built-in read-only agent, chosen from the role rather than the model, so a retargeted run keeps it.
