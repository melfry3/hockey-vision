---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements and coding standards.
---

# Requesting Code Review

Dispatch a code review agent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation — never your session's history. This keeps the reviewer focused on the work product.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```powershell
$BASE_SHA = git rev-parse HEAD~1   # or origin/main
$HEAD_SHA = git rev-parse HEAD
```

**2. Dispatch code-review agent:**

Use the `task` tool with `agent_type: "code-review"`:

```
task(
  agent_type: "code-review",
  name: "review-<feature>",
  prompt: "Review the changes between $BASE_SHA and $HEAD_SHA.
    What was implemented: <description>
    Requirements: <plan or spec reference>
    Focus areas: <specific concerns>"
)
```

The built-in `code-review` agent analyzes staged/unstaged changes and branch diffs. It only surfaces issues that genuinely matter — bugs, security vulnerabilities, logic errors. It will NOT modify code.

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

[Get commit range]
git --no-pager log --oneline -5

[Dispatch code-review agent via task tool]
task(
  agent_type: "code-review",
  name: "review-verification",
  prompt: "Review changes for Task 2 (verification functions).
    Base: a7981ec  Head: 3df7661
    Implemented: verifyIndex() and repairIndex() with 4 issue types
    Spec: docs/specs/deployment-plan.md Task 2"
)

[Agent returns]:
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed after fixing Important items

You: [Fix progress indicators, then continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification
