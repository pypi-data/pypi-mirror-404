---
description: Show current Hanary task status, top priority task, and pending reviews
allowed-tools: [Read, mcp]
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
  - [ ] Subtask 1.2
- [ ] Task 2

## Attention Needed
- [Sessions needing review count]
- [Overload/underload signals if any]
```

If `is_llm_boundary=true` on top task, report: "All LLM-assignable tasks completed. Waiting for human input."
