---
description: Autonomous loop through the backlog - pick, execute, complete, repeat
argument-hint: [--epic <id>] [--max-specs <n>] [--dry-run] [--no-refine]
---

Drive an agent through the nspec backlog autonomously. Pick specs in priority order, execute tasks, handle failures, and loop until the backlog is clear or limits are reached.

**All backlog state is managed through nspec MCP tools — zero direct file I/O.**

## Argument Parsing

Parse `$ARGUMENTS` for:
- `--epic <id>` → filter to a specific epic
- `--max-specs <n>` → stop after N spec completions (default: unlimited)
- `--dry-run` → show next pick and exit without executing
- `--no-refine` → skip backlog refinement after each completion

Initialize counters: `completed = 0`, `blocked_list = []`.

## Loop Protocol

### Phase 1: Pick

1. Call `get_epic` to resolve epic scope. If `--epic` was provided, use that ID; otherwise use the active epic.
2. Call `next_spec` (pass `epic_id` if set) to get the highest-priority unblocked spec.
3. If `next_spec` returns no candidate:
   - Print a summary: specs completed this run, blocked specs list.
   - **EXIT** — backlog is clear (or fully blocked).

### Phase 2: Dry-Run Check

If `--dry-run` is active:
- Call `show` with the picked spec ID to display full details.
- Print: "Dry run — would pick spec {id}: {title}"
- **EXIT**.

### Phase 3: Start

1. Call `activate` with the spec ID → sets spec to Active, writes state.json.
2. Call `session_start` with the spec ID → loads tasks and resume point.
3. Review the task list and identify pending tasks.

### Phase 4: Execute

For each pending task in order:

1. **Do the work.** Read the task description, make code changes, write tests — whatever the task requires.
2. Call `task_complete` with the spec ID and task ID. This gates on `make test-quick`.
3. **If the task or test gate fails:**
   - Retry the fix once.
   - If it fails again, call `task_block` with the spec ID, task ID, and a reason describing what went wrong.
   - Call `session_save` with the spec ID and current task ID to checkpoint.
   - Call `park` with the spec ID to pause the spec.
   - Append the spec ID to `blocked_list`.
   - **GOTO Phase 1** (pick next spec).
4. Call `session_save` with the spec ID and current task ID to checkpoint progress after each completed task.

### Phase 5: Verify

For each acceptance criterion listed in the FR:
- Call `criteria_complete` with the spec ID and criterion ID (e.g., `AC-F1`).
- If a criterion cannot be satisfied, treat it like a task failure: `task_block` the relevant task, `park` the spec, and move on.

### Phase 6: Complete

1. Call `advance` with the spec ID to move through Testing → Ready.
2. Call `complete` with the spec ID to archive to completed/done.
3. Call `session_clear` to clean up session state.
4. Increment `completed` counter.

### Phase 7: Refine

Skip this phase if `--no-refine` is set.

After completing a spec, assess whether the backlog ordering still makes sense:

1. Call `epics` to review overall epic progress.
2. Call `blocked_specs` to check if anything is newly unblocked or still stuck.
3. Call `next_spec` (peek only — do not activate) to see what would be picked next.
4. Consider:
   - Did completing this spec unblock other specs? If so, are their priorities correct?
   - Did you learn something during execution that changes priorities?
     (e.g., discovered a dependency that isn't tracked, found that a P2 is actually blocking a P0)
   - Is there new work to capture? (missing specs, missing tasks on existing specs)
5. Take action using MCP tools:
   - `add_dep` / `remove_dep` to fix the dependency graph
   - `set_priority` to adjust priorities based on new knowledge
   - `create_spec` to capture newly discovered work
   - `task_unblock` to release tasks that were waiting on the completed spec
6. Print a brief refinement summary:
   - Dependencies changed (if any)
   - Priorities adjusted (if any)
   - New specs created (if any)
   - "No refinement needed" if nothing changed

### Phase 8: Progress Report

Print after each spec completion:
- Specs completed this run: `{completed}`
- Specs remaining in epic (estimate from backlog)
- Specs blocked this run: `{blocked_list}`

If `--max-specs` was set and `completed >= max_specs`:
- Print full session summary.
- **EXIT**.

### GOTO Phase 1

Loop back to pick the next spec (Phase 7: Refine will reassess priorities before the next pick).

## Exit Summary

On any exit, print:
- Total specs completed this run
- Total specs blocked (with IDs and reasons)
- Blocked list for follow-up

## Required MCP Tools

This skill uses these nspec MCP tools (and no direct file I/O):

| Tool | Phase |
|------|-------|
| `get_epic` | Pick — resolve epic scope |
| `next_spec` | Pick — select highest-priority unblocked spec |
| `show` | Dry-run — display spec details |
| `activate` | Start — set spec Active |
| `session_start` | Start — load tasks and resume point |
| `task_complete` | Execute — mark task done (gates on tests) |
| `task_block` | Execute — record failure reason |
| `park` | Execute — pause blocked spec |
| `session_save` | Execute — checkpoint after each task and before parking |
| `criteria_complete` | Verify — mark acceptance criteria met |
| `advance` | Complete — move spec through statuses |
| `complete` | Complete — archive to done |
| `session_clear` | Complete — clean up session state |
| `epics` | Refine — review epic progress |
| `blocked_specs` | Refine — check for newly unblocked work |
| `set_priority` | Refine — adjust priorities based on new knowledge |
| `add_dep` | Refine — add discovered dependencies |
| `remove_dep` | Refine — remove outdated dependencies |
| `create_spec` | Refine — capture newly discovered work |
| `task_unblock` | Refine — release tasks waiting on completed spec |
