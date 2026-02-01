---
name: hanary-workflow
description: Task management skill for Hanary. Use when user asks to create tasks, manage tasks, track time, complete work, start working, or mentions hanary, squad tasks, time tracking, estimation, or work organization.
---

# Hanary Task Management Workflow

## Overview

Hanary is a hierarchical task management system with time tracking, squad collaboration, and self-calibration features. This skill provides guidance on effective Hanary usage patterns integrated with Claude Code.

## Core Concepts

### Task Hierarchy
- Tasks can have subtasks via `parent_id`
- `get_top_task` returns the deepest uncompleted task in the priority chain
- When `is_llm_boundary=true`, all LLM-assignable tasks are done - stop working and wait for human input

### Time Tracking
- `start_task`: Begin a time session for focused work
- `stop_task`: End the current session
- Sessions running 8+ hours auto-stop and require review
- Time data feeds into calibration for better estimates

### Self-Calibration System
Use calibration tools to improve task estimation:

| Tool | Purpose |
|------|---------|
| `get_weekly_stats` | 4-week completion averages and time spent |
| `get_estimation_accuracy` | Ratio of actual vs estimated time (>1.0 = underestimating) |
| `suggest_duration` | ML-based time estimate for similar tasks |
| `detect_overload` | Signals: tasks 2x longer, stale 7+ days, low completion |
| `detect_underload` | Tasks completing in <50% estimated time |

### Squad Features (when squad specified)
- `get_squad` / `list_squad_members`: Team context
- `list_messages` / `create_message`: Squad communication

## Standard Workflows

### Starting Work Session

```
1. get_top_task          → Find priority work
2. start_task [id]       → Begin time tracking
3. [Do the work]
4. complete_task [id]    → Mark done
5. get_top_task          → Find next priority
```

### Creating Task Structure

```
1. create_task(title="Main Feature")           → Get parent_id
2. create_task(title="Subtask 1", parent_id=X) → First subtask
3. create_task(title="Subtask 2", parent_id=X) → Second subtask
4. reorder_task(task_id, new_rank)             → Prioritize
```

### End-of-Day Review

```
1. list_sessions_needing_review  → Find auto-stopped sessions
2. review_session / approve_session → Correct or approve times
3. detect_overload               → Check burnout signals
4. get_weekly_stats              → Review productivity trends
```

### Breaking Down Complex Work

When given a large task:
1. Create parent task with overall goal
2. Analyze and decompose into 1-4 hour subtasks
3. Use `suggest_duration` for time estimates
4. Organize with `reorder_task` by priority/dependency
5. Work through subtasks sequentially

## Tool Quick Reference

### Task Management
| Tool | Purpose |
|------|---------|
| `list_tasks` | List all tasks (use `include_completed` for history) |
| `create_task` | Create new task (set `parent_id` for subtask) |
| `update_task` | Modify title or description |
| `complete_task` | Mark as done |
| `uncomplete_task` | Reopen completed task |
| `delete_task` | Soft delete |
| `get_top_task` | Get highest priority incomplete task |
| `reorder_task` | Change priority position |

### Time Tracking
| Tool | Purpose |
|------|---------|
| `start_task` | Begin time session |
| `stop_task` | End time session |

### Session Review
| Tool | Purpose |
|------|---------|
| `list_sessions_needing_review` | Find 8h+ auto-stopped sessions |
| `approve_session` | Accept recorded time |
| `review_session` | Correct end time |
| `delete_session` | Remove session |

## Best Practices

### Task Titles
- Use action verbs: "Implement", "Fix", "Add", "Update"
- Be specific: "Add user authentication" not "Auth stuff"
- Include context: "Fix login redirect on mobile"

### Time Estimation
- Check `suggest_duration` for similar task data
- Review `get_estimation_accuracy` to calibrate
- Break tasks >4 hours into subtasks
- Account for interruptions (add 20-30%)

### Handling `is_llm_boundary`
When `get_top_task` returns a task with `is_llm_boundary=true`:
- All LLM-assignable work is complete
- Stop working and report status to user
- Wait for human to add more tasks or change scope

## Additional Resources

### Reference Files
- **`references/task-patterns.md`** - Common task organization patterns and hierarchies
- **`references/estimation-guide.md`** - Detailed guide for accurate time estimation
