---
name: executing-plans
description: Use when you have a written implementation plan to execute in the current session with review checkpoints.
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** If sub-agents are available (via the `task` tool), consider using the `subagent-driven-development` skill instead — it produces higher quality results through fresh-context sub-agents and two-stage review.

## The Process

### Step 1: Load and Review Plan
1. Read plan file using `view` tool
2. Review critically — identify any questions or concerns about the plan
3. If concerns: Raise them with the user before starting
4. If no concerns: Register tasks in SQL and proceed

```sql
INSERT INTO todos (id, title, description, status) VALUES
  ('task-1', 'Task 1: Component Name', 'Full description...', 'pending'),
  ('task-2', 'Task 2: Next Component', 'Full description...', 'pending');
```

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress: `UPDATE todos SET status = 'in_progress' WHERE id = 'task-N'`
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as done: `UPDATE todos SET status = 'done' WHERE id = 'task-N'`

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- Use the `finishing-a-development-branch` skill
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification using `ask_user` rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- User updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** — stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- **using-git-worktrees** — Set up isolated workspace before starting
- **writing-plans** — Creates the plan this skill executes
- **finishing-a-development-branch** — Complete development after all tasks
