# Task Time Estimation Guide

Improve estimation accuracy using Hanary's calibration tools and proven techniques.

## Understanding Your Estimation Accuracy

### Using get_estimation_accuracy

The `get_estimation_accuracy` tool returns a ratio of actual time vs estimated time:

| Ratio | Meaning | Action |
|-------|---------|--------|
| < 0.7 | Significant overestimation | Reduce estimates by 30-50% |
| 0.7 - 0.9 | Slight overestimation | Reduce estimates by 10-20% |
| 0.9 - 1.1 | Good accuracy | Keep current approach |
| 1.1 - 1.5 | Slight underestimation | Increase estimates by 10-30% |
| > 1.5 | Significant underestimation | Increase estimates by 50%+, break down tasks more |

### Using suggest_duration

The `suggest_duration` tool analyzes your completed tasks to suggest time for similar work:

```
suggest_duration(task_id="new-task-123")

Returns:
- suggested_minutes: Based on similar completed tasks
- confidence: How many similar tasks found
- basis: What tasks were used for comparison
```

**When to trust suggestions:**
- High confidence (5+ similar tasks): Very reliable
- Medium confidence (2-4 tasks): Useful guideline
- Low confidence (0-1 tasks): Use as rough estimate only

## Estimation Techniques

### 1. Break Down Until Estimable

A task is "estimable" when you can visualize completing it in one sitting.

**Too vague:**
- "Implement authentication" (could be 2 hours or 2 weeks)

**Better breakdown:**
- "Set up Passport.js middleware" (2 hours)
- "Create user model with password hashing" (1.5 hours)
- "Implement login endpoint" (2 hours)
- "Add JWT token generation" (1 hour)

**Rule of thumb:** If estimate > 4 hours, break it down further.

### 2. Use Reference Tasks

Compare new tasks to similar completed work:

```
New task: "Add CSV export for reports"

Similar completed tasks:
- "Add PDF export for invoices" - took 3.5 hours
- "Add JSON export for analytics" - took 2 hours

Estimate: 2.5-3 hours (CSV is simpler than PDF, similar to JSON)
```

### 3. Account for Task Complexity

Apply multipliers based on complexity factors:

| Factor | Multiplier | Examples |
|--------|------------|----------|
| Familiar technology | 1.0x | Using tools you know well |
| New library/API | 1.3x | First time using a library |
| New language/framework | 1.5x | Learning while building |
| Complex integration | 1.4x | Multiple systems interacting |
| Legacy code | 1.3x | Understanding existing code first |
| Critical path | 1.2x | Extra care needed, more testing |

**Example:**
- Base estimate: 2 hours
- New API (1.3x) + Legacy code (1.3x)
- Adjusted estimate: 2 × 1.3 × 1.3 = 3.4 hours

### 4. Include Hidden Time

Common overlooked activities:

| Activity | Typical Time |
|----------|--------------|
| Reading documentation | 15-30 min |
| Setting up test data | 20-45 min |
| Code review iterations | 30-60 min |
| Debugging edge cases | 30-90 min |
| Writing tests | 50-100% of implementation time |
| Documentation | 15-30 min |

**Add buffer:** 20-30% for interruptions and context switching.

### 5. Use Planning Poker Anchors

When uncertain, use these common task sizes:

| Size | Time | Task Examples |
|------|------|---------------|
| XS | 30 min | Fix typo, update config, minor CSS |
| S | 1-2 hours | Add simple endpoint, write tests for existing code |
| M | 2-4 hours | New feature component, moderate refactor |
| L | 4-8 hours | Complex feature, significant refactor |
| XL | 8+ hours | **Break down further** |

## Using Calibration Data

### Weekly Stats Analysis

`get_weekly_stats` provides 4-week rolling averages:

```
Week 1: 25 hours actual work
Week 2: 28 hours actual work
Week 3: 22 hours actual work (holiday)
Week 4: 26 hours actual work

Average: 25 hours/week of focused work
```

**Use for capacity planning:**
- Don't commit to more than your average
- Account for meetings, reviews, etc.
- Leave 20% buffer for unexpected work

### Overload Detection

`detect_overload` signals indicate estimation problems:

| Signal | Meaning | Response |
|--------|---------|----------|
| Tasks taking 2x+ estimate | Systematic underestimation | Review and adjust multipliers |
| Stale tasks (7+ days) | Tasks too large or blocked | Break down or reassess |
| Low completion rate | Overcommitment | Reduce WIP, focus on fewer tasks |

### Underload Detection

`detect_underload` signals:

| Signal | Meaning | Response |
|--------|---------|----------|
| Tasks < 50% estimate | Overestimating | Reduce buffers |
| Consistently early | Good efficiency | Take on more or harder tasks |

## Common Estimation Mistakes

### 1. Optimism Bias
**Problem:** Estimating for the best case
**Fix:** Estimate for the realistic case, add 20% buffer

### 2. Anchoring
**Problem:** First number heard becomes the anchor
**Fix:** Estimate independently before discussing

### 3. Planning Fallacy
**Problem:** Ignoring past experience
**Fix:** Always check `suggest_duration` and similar tasks

### 4. Scope Creep Blindness
**Problem:** Not accounting for "just one more thing"
**Fix:** Define done criteria upfront, add buffer for unknowns

### 5. Forgetting Setup/Teardown
**Problem:** Only estimating the "real work"
**Fix:** Include reading, setup, testing, documentation time

## Estimation Checklist

Before finalizing an estimate:

- [ ] Task is broken down to <4 hours
- [ ] Checked `suggest_duration` for similar tasks
- [ ] Reviewed `get_estimation_accuracy` ratio
- [ ] Applied complexity multipliers
- [ ] Added time for setup, testing, documentation
- [ ] Added 20-30% buffer for unknowns
- [ ] Compared to weekly capacity (`get_weekly_stats`)
- [ ] Verified with past experience on similar work

## Continuous Improvement

1. **Track actuals:** Always use time tracking
2. **Review weekly:** Compare estimates vs actuals
3. **Adjust multipliers:** Update based on patterns
4. **Note surprises:** What took longer/shorter than expected?
5. **Share learnings:** Help team calibrate together
