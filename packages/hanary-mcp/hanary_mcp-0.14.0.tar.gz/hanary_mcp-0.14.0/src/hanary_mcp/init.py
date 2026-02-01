"""Hanary MCP initialization for new projects."""

import os
from pathlib import Path

# Command templates
COMMAND_STATUS = """---
description: Show current Hanary task status, top priority task, and pending reviews
---

# Hanary Status Overview

Retrieve and display the current task status from Hanary:

## Steps

1. **Get Top Priority Task**
   - Call `get_top_task` to find the highest priority incomplete task
   - Note if `is_llm_boundary=true` (means all LLM-assignable tasks are completed)

2. **List Active Tasks**
   - Call `list_tasks` with `include_completed=false` to get pending tasks
   - Organize by hierarchy (parent tasks with their subtasks)

3. **Check Sessions Needing Review**
   - Call `list_sessions_needing_review` to find auto-stopped sessions

4. **Check Workload Signals**
   - Call `detect_overload` to check for burnout signals
   - Call `detect_underload` to check capacity

## Output Format

Present a clear, scannable summary:

```
## Current Focus
[Top priority task title] (ID: xxx)
  > Parent: [parent task if exists]
  > Status: [time tracking active/inactive]

## Pending Tasks (N total)
- [ ] Task 1
  - [ ] Subtask 1.1
- [ ] Task 2

## Attention Needed
- [Sessions needing review count]
- [Overload/underload signals if any]
```

If `is_llm_boundary=true` on top task, report: "All LLM-assignable tasks completed. Waiting for human input."
"""

COMMAND_START = """---
description: Start working on a Hanary task with time tracking
---

# Start Hanary Task

Begin time tracking for a task in Hanary.

## Arguments

User input: $ARGUMENTS

## Process

### If task ID provided (numeric or UUID format):
1. Call `start_task` with the provided task_id
2. Confirm task started

### If search term provided:
1. Call `list_tasks` to find matching tasks
2. Find the best match by title
3. Call `start_task` with the matched task_id
4. Confirm task started

### If no argument provided:
1. Call `get_top_task` to get the highest priority task
2. If `is_llm_boundary=true`, report that all tasks are done
3. Otherwise, call `start_task` with that task_id
4. Confirm task started

## Output

```
Started: [Task Title]
ID: [task_id]
Parent: [parent task title if subtask]

Time tracking is now active.
```

## Error Handling

- If task not found: List similar tasks and ask for clarification
- If task already has active session: Report current session info
- If no tasks available: Suggest creating a new task
"""

COMMAND_DONE = """---
description: Complete current task, stop time tracking, and show next priority
---

# Complete Hanary Task

Mark a task as completed and stop time tracking.

## Arguments

User input: $ARGUMENTS

## Process

### If task ID provided:
1. Call `stop_task` to end time tracking (if active)
2. Call `complete_task` with the provided task_id
3. Call `get_top_task` to find next priority

### If no argument provided:
1. Call `get_top_task` to identify current focus task
2. Call `stop_task` on that task
3. Call `complete_task` on that task
4. Call `get_top_task` again to find next priority

## Output

```
Completed: [Task Title]
Time spent: [duration from session if available]

## Next Priority
[Next task title] (ID: xxx)
Parent: [parent if exists]

Start next task? Use /hanary-start or /hanary-start [task-id]
```

### If all tasks completed:
```
Completed: [Task Title]

All tasks completed! 

To add more work:
- Create tasks in Hanary
- Or describe what you want to work on
```
"""

# OpenCode command templates (slightly different frontmatter)
OPENCODE_COMMAND_STATUS = """---
name: hanary-status
description: Show current Hanary task status, top priority task, and pending reviews
---
""" + COMMAND_STATUS.split("---", 2)[2]

OPENCODE_COMMAND_START = """---
name: hanary-start
description: Start working on a Hanary task with time tracking
---
""" + COMMAND_START.split("---", 2)[2]

OPENCODE_COMMAND_DONE = """---
name: hanary-done
description: Complete current task, stop time tracking, and show next priority
---
""" + COMMAND_DONE.split("---", 2)[2]

# Skill template
SKILL_WORKFLOW = """---
name: hanary-workflow
description: Task management skill for Hanary. Use when user asks to create tasks, manage tasks, track time, complete work, start working, or mentions hanary, squad tasks, time tracking, estimation, or work organization.
---

# Hanary Task Management Workflow

## Overview

Hanary is a hierarchical task management system with time tracking, squad collaboration, and self-calibration features.

## Core Concepts

### Task Hierarchy
- Tasks can have subtasks via `parent_id`
- `get_top_task` returns the deepest uncompleted task in the priority chain
- When `is_llm_boundary=true`, all LLM-assignable tasks are done

### Time Tracking
- `start_task`: Begin a time session for focused work
- `stop_task`: End the current session
- Sessions running 8+ hours auto-stop and require review

### Self-Calibration System

| Tool | Purpose |
|------|---------|
| `get_weekly_stats` | 4-week completion averages |
| `get_estimation_accuracy` | Ratio of actual vs estimated time |
| `suggest_duration` | ML-based time estimate |
| `detect_overload` | Burnout signals |
| `detect_underload` | Capacity check |

## Standard Workflows

### Starting Work Session

```
1. get_top_task          -> Find priority work
2. start_task [id]       -> Begin time tracking
3. [Do the work]
4. complete_task [id]    -> Mark done
5. get_top_task          -> Find next priority
```

### Creating Task Structure

```
1. create_task(title="Main Feature")           -> Get parent_id
2. create_task(title="Subtask 1", parent_id=X) -> First subtask
3. reorder_task(task_id, new_rank)             -> Prioritize
```

## Tool Quick Reference

### Task Management
| Tool | Purpose |
|------|---------|
| `list_tasks` | List all tasks |
| `create_task` | Create new task |
| `update_task` | Modify title or description |
| `complete_task` | Mark as done |
| `get_top_task` | Get highest priority task |
| `reorder_task` | Change priority position |

### Time Tracking
| Tool | Purpose |
|------|---------|
| `start_task` | Begin time session |
| `stop_task` | End time session |
"""

# Agent template (Claude Code format)
AGENT_TASK_PLANNER_CLAUDE = """---
name: task-planner
description: Use this agent to break down complex tasks into subtasks, create task hierarchies in Hanary, and estimate task durations.
model: default
tools: [mcp_hanary_*, Read, Grep, Glob]
---

You are a task planning specialist integrated with Hanary.

## Core Responsibilities

1. **Decompose complex work** into actionable subtasks
2. **Create hierarchical task structures** in Hanary
3. **Estimate realistic durations** using calibration data

## Process

### Step 1: Understand the Goal
- Clarify the overall objective
- Identify success criteria

### Step 2: Check Context
- Call `list_tasks` to see existing related tasks
- Call `get_weekly_stats` to understand capacity

### Step 3: Decompose Work
Break down into tasks that are:
- **Specific**: Clear what needs to be done
- **Achievable**: Completable in 1-4 hours

### Step 4: Create Structure
```
Parent Task (overall goal)
|- Phase 1
|  |- Subtask 1.1
|  |- Subtask 1.2
|- Phase 2
   |- Subtask 2.1
```

## Output Format

```markdown
## Task Breakdown: [Goal]

### Overview
- Total estimated time: X hours
- Number of tasks: N

### Task Hierarchy
1. **[Parent Task]** - [estimate]
   1.1 [Subtask] - [estimate]

### Priority Order
1. [Most important first]
2. [Then this]
```

Then offer: "Would you like me to create these tasks in Hanary?"
"""

AGENT_TASK_PLANNER_OPENCODE = """---
name: task-planner
description: Use this agent to break down complex tasks into subtasks, create task hierarchies in Hanary, and estimate task durations.
---

You are a task planning specialist integrated with Hanary.

## Core Responsibilities

1. **Decompose complex work** into actionable subtasks
2. **Create hierarchical task structures** in Hanary
3. **Estimate realistic durations** using calibration data

## Process

### Step 1: Understand the Goal
- Clarify the overall objective
- Identify success criteria

### Step 2: Check Context
- Call `list_tasks` to see existing related tasks
- Call `get_weekly_stats` to understand capacity

### Step 3: Decompose Work
Break down into tasks that are:
- **Specific**: Clear what needs to be done
- **Achievable**: Completable in 1-4 hours

### Step 4: Create Structure
```
Parent Task (overall goal)
|- Phase 1
|  |- Subtask 1.1
|  |- Subtask 1.2
|- Phase 2
   |- Subtask 2.1
```

## Output Format

```markdown
## Task Breakdown: [Goal]

### Overview
- Total estimated time: X hours
- Number of tasks: N

### Task Hierarchy
1. **[Parent Task]** - [estimate]
   1.1 [Subtask] - [estimate]

### Priority Order
1. [Most important first]
2. [Then this]
```

Then offer: "Would you like me to create these tasks in Hanary?"
"""


def get_mcp_json(squad: str | None = None) -> str:
    """Generate .mcp.json content."""
    if squad:
        return f'''{{
  "mcpServers": {{
    "hanary": {{
      "command": "uvx",
      "args": ["hanary-mcp", "--squad", "{squad}"]
    }}
  }}
}}
'''
    return """{
  "mcpServers": {
    "hanary": {
      "command": "uvx",
      "args": ["hanary-mcp"]
    }
  }
}
"""


def get_opencode_json(squad: str | None = None) -> str:
    """Generate opencode.json content."""
    if squad:
        return f'''{{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {{
    "hanary": {{
      "type": "local",
      "command": ["uvx", "hanary-mcp", "--squad", "{squad}"]
    }}
  }}
}}
'''
    return """{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "hanary": {
      "type": "local",
      "command": ["uvx", "hanary-mcp"]
    }
  }
}
"""


def get_codex_toml(squad: str | None = None) -> str:
    """Generate .codex/config.toml content for OpenAI Codex."""
    if squad:
        return f'''# Hanary MCP Server configuration for OpenAI Codex
# See: https://developers.openai.com/codex/mcp/

[mcp_servers.hanary]
command = "uvx"
args = ["hanary-mcp", "--squad", "{squad}"]

[mcp_servers.hanary.env]
# Keep uv cache within the project so Codex sandbox can write to it
UV_CACHE_DIR = ".codex/uv-cache"

# Uncomment and set your API token, or use environment variable
# HANARY_API_TOKEN = "your-token-here"
'''
    return """# Hanary MCP Server configuration for OpenAI Codex
# See: https://developers.openai.com/codex/mcp/

[mcp_servers.hanary]
command = "uvx"
args = ["hanary-mcp"]

[mcp_servers.hanary.env]
# Keep uv cache within the project so Codex sandbox can write to it
UV_CACHE_DIR = ".codex/uv-cache"

# Uncomment and set your API token, or use environment variable
# HANARY_API_TOKEN = "your-token-here"
"""


# Codex skill templates (uses Skills system with SKILL.md in skill directories)
# Skills are invoked with $skill-name or triggered implicitly by description matching
CODEX_SKILL_STATUS = """---
name: hanary-status
description: Show current Hanary task status, top priority task, and pending reviews. Use when user asks about tasks, current work, what to do next, or task overview.
---

# Hanary Status Overview

Retrieve and display the current task status from Hanary.

## Steps

1. **Get Top Priority Task**
   - Call `hanary_get_top_task` to find the highest priority incomplete task
   - Note if `is_llm_boundary=true` (means all LLM-assignable tasks are completed)

2. **List Active Tasks**
   - Call `hanary_list_tasks` with `include_completed=false` to get pending tasks
   - Organize by hierarchy (parent tasks with their subtasks)

3. **Check Sessions Needing Review**
   - Call `hanary_list_sessions_needing_review` to find auto-stopped sessions

4. **Check Workload Signals**
   - Call `hanary_detect_overload` to check for burnout signals
   - Call `hanary_detect_underload` to check capacity

## Output Format

Present a clear, scannable summary:

```
## Current Focus
[Top priority task title] (ID: xxx)
  > Parent: [parent task if exists]
  > Status: [time tracking active/inactive]

## Pending Tasks (N total)
- [ ] Task 1
  - [ ] Subtask 1.1
- [ ] Task 2

## Attention Needed
- [Sessions needing review count]
- [Overload/underload signals if any]
```

If `is_llm_boundary=true` on top task, report: "All LLM-assignable tasks completed. Waiting for human input."
"""

CODEX_SKILL_START = """---
name: hanary-start
description: Start working on a Hanary task with time tracking. Use when user wants to begin work, start a task, or track time on something.
---

# Start Hanary Task

Begin time tracking for a task in Hanary.

## Arguments

User input: $ARGUMENTS

## Process

### If task ID provided (numeric or UUID format):
1. Call `hanary_start_task` with the provided task_id
2. Confirm task started

### If search term provided:
1. Call `hanary_list_tasks` to find matching tasks
2. Find the best match by title
3. Call `hanary_start_task` with the matched task_id
4. Confirm task started

### If no argument provided:
1. Call `hanary_get_top_task` to get the highest priority task
2. If `is_llm_boundary=true`, report that all tasks are done
3. Otherwise, call `hanary_start_task` with that task_id
4. Confirm task started

## Output

```
Started: [Task Title]
ID: [task_id]
Parent: [parent task title if subtask]

Time tracking is now active.
```

## Error Handling

- If task not found: List similar tasks and ask for clarification
- If task already has active session: Report current session info
- If no tasks available: Suggest creating a new task
"""

CODEX_SKILL_DONE = """---
name: hanary-done
description: Complete current task, stop time tracking, and show next priority. Use when user finishes work, completes a task, or is done with something.
---

# Complete Hanary Task

Mark a task as completed and stop time tracking.

## Arguments

User input: $ARGUMENTS

## Process

### If task ID provided:
1. Call `hanary_stop_task` to end time tracking (if active)
2. Call `hanary_complete_task` with the provided task_id
3. Call `hanary_get_top_task` to find next priority

### If no argument provided:
1. Call `hanary_get_top_task` to identify current focus task
2. Call `hanary_stop_task` on that task
3. Call `hanary_complete_task` on that task
4. Call `hanary_get_top_task` again to find next priority

## Output

```
Completed: [Task Title]
Time spent: [duration from session if available]

## Next Priority
[Next task title] (ID: xxx)
Parent: [parent if exists]

Start next task? Use $hanary-start or $hanary-start [task-id]
```

### If all tasks completed:
```
Completed: [Task Title]

All tasks completed! 

To add more work:
- Create tasks in Hanary
- Or describe what you want to work on
```
"""

CODEX_SKILL_WORKFLOW = """---
name: hanary-workflow
description: Task management skill for Hanary. Use when user asks to create tasks, manage tasks, track time, complete work, start working, or mentions hanary, squad tasks, time tracking, estimation, or work organization.
---

# Hanary Task Management Workflow

## Overview

Hanary is a hierarchical task management system with time tracking, squad collaboration, and self-calibration features.

## Core Concepts

### Task Hierarchy
- Tasks can have subtasks via `parent_id`
- `hanary_get_top_task` returns the deepest uncompleted task in the priority chain
- When `is_llm_boundary=true`, all LLM-assignable tasks are done

### Time Tracking
- `hanary_start_task`: Begin a time session for focused work
- `hanary_stop_task`: End the current session
- Sessions running 8+ hours auto-stop and require review

### Self-Calibration System

| Tool | Purpose |
|------|---------|
| `hanary_get_weekly_stats` | 4-week completion averages |
| `hanary_get_estimation_accuracy` | Ratio of actual vs estimated time |
| `hanary_suggest_duration` | ML-based time estimate |
| `hanary_detect_overload` | Burnout signals |
| `hanary_detect_underload` | Capacity check |

## Standard Workflows

### Starting Work Session

```
1. hanary_get_top_task       -> Find priority work
2. hanary_start_task [id]    -> Begin time tracking
3. [Do the work]
4. hanary_complete_task [id] -> Mark done
5. hanary_get_top_task       -> Find next priority
```

### Creating Task Structure

```
1. hanary_create_task(title="Main Feature")           -> Get parent_id
2. hanary_create_task(title="Subtask 1", parent_id=X) -> First subtask
3. hanary_reorder_task(task_id, new_rank)             -> Prioritize
```

## Tool Quick Reference

### Task Management
| Tool | Purpose |
|------|---------|
| `hanary_list_tasks` | List all tasks |
| `hanary_create_task` | Create new task |
| `hanary_update_task` | Modify title or description |
| `hanary_complete_task` | Mark as done |
| `hanary_get_top_task` | Get highest priority task |
| `hanary_reorder_task` | Change priority position |

### Time Tracking
| Tool | Purpose |
|------|---------|
| `hanary_start_task` | Begin time session |
| `hanary_stop_task` | End time session |
"""


def init_project(
    target_dir: str = ".", force: bool = False, squad: str | None = None
) -> None:
    """Initialize Hanary integration in a project directory."""
    target = Path(target_dir).resolve()

    mode_str = f"squad '{squad}'" if squad else "personal tasks"
    print(f"Initializing Hanary integration in {target}")
    print(f"Mode: {mode_str}")

    files = {
        ".claude/commands/hanary-status.md": COMMAND_STATUS,
        ".claude/commands/hanary-start.md": COMMAND_START,
        ".claude/commands/hanary-done.md": COMMAND_DONE,
        ".claude/skills/hanary-workflow/SKILL.md": SKILL_WORKFLOW,
        ".claude/agents/task-planner.md": AGENT_TASK_PLANNER_CLAUDE,
        ".mcp.json": get_mcp_json(squad),
        ".opencode/commands/hanary-status.md": OPENCODE_COMMAND_STATUS,
        ".opencode/commands/hanary-start.md": OPENCODE_COMMAND_START,
        ".opencode/commands/hanary-done.md": OPENCODE_COMMAND_DONE,
        ".opencode/agents/task-planner.md": AGENT_TASK_PLANNER_OPENCODE,
        "opencode.json": get_opencode_json(squad),
        ".codex/skills/hanary-status/SKILL.md": CODEX_SKILL_STATUS,
        ".codex/skills/hanary-start/SKILL.md": CODEX_SKILL_START,
        ".codex/skills/hanary-done/SKILL.md": CODEX_SKILL_DONE,
        ".codex/skills/hanary-workflow/SKILL.md": CODEX_SKILL_WORKFLOW,
        ".codex/config.toml": get_codex_toml(squad),
    }

    created = []
    skipped = []

    for rel_path, content in files.items():
        file_path = target / rel_path

        if file_path.exists() and not force:
            skipped.append(rel_path)
            continue

        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        file_path.write_text(content)
        created.append(rel_path)

    # Ensure Codex cache directory exists for sandboxed uvx runs
    codex_cache_dir = target / ".codex" / "uv-cache"
    if not codex_cache_dir.exists():
        codex_cache_dir.mkdir(parents=True, exist_ok=True)

    # Print summary
    if created:
        print(f"\nCreated {len(created)} files:")
        for f in created:
            print(f"  + {f}")

    if skipped:
        print(f"\nSkipped {len(skipped)} existing files (use --force to overwrite):")
        for f in skipped:
            print(f"  - {f}")

    print("\n" + "=" * 50)
    print(f"Setup complete! ({mode_str})")
    print("\nSupported platforms:")
    print("  - Claude Code (.claude/, .mcp.json)")
    print("  - OpenCode (.opencode/, opencode.json)")
    print("  - OpenAI Codex (.codex/skills/, .codex/config.toml)")
    print("\nNext steps:")
    print("1. Set your API token (if not already set):")
    print("   export HANARY_API_TOKEN='your-token-here'")
    print("\n2. Restart your AI coding assistant to load the configuration")
    print("\n3. Test with:")
    print("   - Claude/OpenCode: /hanary-status")
    print("   - Codex: $hanary-status (or just ask about tasks)")
    print("=" * 50)
