# Task Organization Patterns

Common patterns for structuring tasks in Hanary for different types of work.

## Feature Development Pattern

Best for implementing new functionality:

```
Feature: User Authentication
├── Research & Design
│   ├── Analyze auth requirements
│   ├── Choose auth strategy (JWT, session, OAuth)
│   └── Design database schema
├── Backend Implementation
│   ├── Set up auth middleware
│   ├── Implement login endpoint
│   ├── Implement registration endpoint
│   └── Add password reset flow
├── Frontend Implementation
│   ├── Create login form component
│   ├── Create registration form
│   └── Add auth state management
├── Testing
│   ├── Write unit tests for auth logic
│   ├── Write integration tests
│   └── Manual testing checklist
└── Documentation
    ├── Update API docs
    └── Write user guide
```

**Key principles:**
- Group by phase (research → implement → test → document)
- Each leaf task should be 1-4 hours
- Complete phases sequentially when dependencies exist

## Bug Fix Pattern

Best for investigating and fixing issues:

```
Bug: Login fails on mobile devices
├── Reproduce & Document
│   ├── Reproduce on iOS Safari
│   ├── Reproduce on Android Chrome
│   └── Document exact steps and errors
├── Investigate
│   ├── Check network requests
│   ├── Review mobile-specific CSS
│   └── Check auth cookie settings
├── Implement Fix
│   ├── Fix identified issue
│   └── Add regression test
└── Verify
    ├── Test on all affected devices
    └── Get QA sign-off
```

**Key principles:**
- Always reproduce first
- Document findings before fixing
- Add tests to prevent regression

## Sprint/Weekly Planning Pattern

Organize work for a time period:

```
Sprint 23 (Jan 20-31)
├── High Priority
│   ├── [Critical Bug] Payment processing timeout
│   ├── [Feature] Add export to CSV
│   └── [Tech Debt] Upgrade React to v19
├── Medium Priority
│   ├── [Feature] Dashboard charts
│   └── [Bug] Avatar upload on slow connections
└── If Time Permits
    ├── [Enhancement] Dark mode toggle
    └── [Documentation] API versioning guide
```

**Key principles:**
- Group by priority, not type
- Set realistic capacity based on `get_weekly_stats`
- Leave buffer for unexpected work (20-30%)

## Research/Learning Pattern

For exploration and learning tasks:

```
Learn: GraphQL Integration
├── Fundamentals
│   ├── Read official GraphQL docs
│   ├── Complete tutorial project
│   └── Understand schema design
├── Evaluate for Our Use Case
│   ├── Identify current API pain points
│   ├── Design sample schema
│   └── Prototype query/mutation
├── Proof of Concept
│   ├── Set up GraphQL server
│   ├── Migrate one endpoint
│   └── Performance benchmark
└── Decision & Documentation
    ├── Write pros/cons analysis
    └── Present recommendation
```

**Key principles:**
- Time-box research (don't let it expand indefinitely)
- End with concrete output (decision, documentation)
- Break into verifiable milestones

## Refactoring Pattern

For improving existing code:

```
Refactor: Extract payment processing module
├── Preparation
│   ├── Map current payment code locations
│   ├── Write characterization tests
│   └── Define module interface
├── Extraction
│   ├── Create PaymentProcessor class
│   ├── Move logic to new module
│   ├── Update all call sites
│   └── Remove old code
├── Verification
│   ├── Run all tests
│   ├── Manual smoke test
│   └── Performance comparison
└── Cleanup
    ├── Update documentation
    └── Remove feature flags
```

**Key principles:**
- Always add tests before refactoring
- Make changes incrementally
- Keep the system working at each step

## Daily Task Pattern

For recurring daily work:

```
Daily Operations (Jan 21)
├── Morning
│   ├── Review overnight alerts
│   ├── Check deployment status
│   └── Team standup
├── Core Work
│   └── [Linked to sprint tasks]
├── End of Day
│   ├── Update task status
│   ├── Review time sessions
│   └── Plan tomorrow's priorities
```

**Key principles:**
- Separate routine from project work
- Use time tracking for both
- Review and adjust patterns weekly

## Using with Hanary Tools

### Creating hierarchical tasks

```python
# Create parent
parent = create_task(title="Feature: User Auth")

# Create subtasks
create_task(title="Research requirements", parent_id=parent.id)
create_task(title="Implement backend", parent_id=parent.id)
create_task(title="Implement frontend", parent_id=parent.id)
```

### Organizing priority

```python
# Move critical task to top
reorder_task(task_id=critical_task.id, new_rank=0)

# Move lower priority down
reorder_task(task_id=nice_to_have.id, new_rank=5)
```

### Template tasks

For recurring patterns, create tasks with detailed descriptions that can be copied or used as templates for similar future work.
