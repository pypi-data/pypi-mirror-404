---
name: hanary-done
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

## Error Handling

- If task not found: List recent tasks and ask for clarification
- If no active task: Ask which task to complete
- If task already completed: Report status and suggest next task
