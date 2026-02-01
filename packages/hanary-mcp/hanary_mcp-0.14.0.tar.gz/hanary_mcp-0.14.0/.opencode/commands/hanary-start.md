---
name: hanary-start
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
