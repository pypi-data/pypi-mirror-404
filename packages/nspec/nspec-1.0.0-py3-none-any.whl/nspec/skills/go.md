---
description: Start working on a spec - initialize session and show context
argument-hint: [spec-id (optional)]
---

Start a work session on a spec.

1. Determine spec ID:
   - If "$1" is provided, use that spec directly
   - Otherwise, check for active epic context:
     a. Use `get_epic` MCP tool to get the active epic ID
     b. If epic set: Use `next_spec` MCP tool to get next workable spec
     c. If no epic set: Use `epics` to analyze the backlog, then suggest:
        - The highest priority epic that has workable specs
        - Offer to set it as active: `/backlog:epic set <id>`
2. Use `session_start` MCP tool with the spec_id to initialize session context
3. Show the task breakdown and where work left off
4. Check for any blockers or conflicts with `blocked_specs` MCP tool
5. Suggest the first action to take

Note: Task progress is shown in the Claude Code status line (reads directly from IMPL). No TodoWrite needed.

If the spec needs activation, use `/backlog:activate <id>` first.

If no spec can be determined (no argument, no epic with workable specs):
- Show the epic analysis from `/backlog`
- Recommend setting an active epic: `/backlog:epic set <id>`
- Or provide a spec ID directly: `/go 415`

Related commands:
- `/backlog` - View dashboard (THE COMPASS)
- `/backlog:show <id>` - Show spec details
- `/backlog:activate <id>` - Start work on a spec
- `/backlog:task <id> <pattern>` - Mark task complete
- `/backlog:criteria <id> <AC-XX>` - Mark criterion complete

Begin working immediately after showing the context - don't wait for confirmation.
