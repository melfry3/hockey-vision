# Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality reviewer sub-agent.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes.**

```
task(
  agent_type: "code-review",
  name: "quality-review-task-N",
  prompt: |
    Review the changes between [BASE_SHA] and [HEAD_SHA].

    What was implemented: [from implementer's report]
    Requirements: Task N from [plan-file]
    Summary: [task summary]

    In addition to standard code quality concerns, check:
    - Does each file have one clear responsibility?
    - Are units decomposed so they can be understood independently?
    - Is the implementation following the file structure from the plan?
    - Did this change create overly large files?
)
```

**Code reviewer returns:** Issues categorized as Critical/Important/Minor, plus assessment.
