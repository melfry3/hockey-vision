---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks. Dispatches fresh sub-agent per task with two-stage review.
---

# Subagent-Driven Development

Execute plan by dispatching a fresh sub-agent per task, with two-stage review after each: spec compliance review first, then code quality review.

**Why sub-agents:** You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions, you ensure they stay focused. They should never inherit your session's context — you construct exactly what they need. This preserves your own context for coordination work.

**Core principle:** Fresh sub-agent per task + two-stage review (spec then quality) = high quality, fast iteration

## When to Use

- Have a written implementation plan
- Tasks are mostly independent
- Want to stay in this session (vs. separate session)

**vs. Executing Plans:**
- Same session (no context switch)
- Fresh sub-agent per task (no context pollution)
- Two-stage review after each task
- Faster iteration (no human-in-loop between tasks)

## The Process

```
1. Read plan, extract all tasks with full text, note context
2. Register all tasks in SQL todos table
3. For each task:
   a. Dispatch implementer sub-agent (see references/implementer-prompt.md)
   b. Handle implementer status (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED)
   c. Dispatch spec reviewer sub-agent (see references/spec-reviewer-prompt.md)
   d. If spec issues → implementer fixes → re-review
   e. Dispatch code quality reviewer (see references/code-quality-reviewer-prompt.md)
   f. If quality issues → implementer fixes → re-review
   g. Mark task complete in SQL
4. After all tasks → dispatch final code review
5. Use finishing-a-development-branch skill
```

## Model Selection

Use the `task` tool's agent types strategically:

| Task Type | Agent Type | When |
|-----------|------------|------|
| Mechanical implementation | `task` (fast agent) | Isolated functions, clear specs, 1-2 files |
| Integration work | `general-purpose` | Multi-file coordination, pattern matching |
| Code review | `code-review` | Built-in review agent, high signal |
| Architecture/design | `general-purpose` | Broad codebase understanding needed |
| Quick investigation | `explore` | Finding files, understanding patterns |

## Handling Implementer Status

**DONE:** Proceed to spec compliance review.

**DONE_WITH_CONCERNS:** Read concerns first. If about correctness or scope, address before review. If observations, note and proceed.

**NEEDS_CONTEXT:** Provide missing context and re-dispatch.

**BLOCKED:** Assess the blocker:
1. Context problem → provide more context and re-dispatch
2. Needs more reasoning → re-dispatch with `general-purpose` agent
3. Task too large → break into smaller pieces
4. Plan itself is wrong → escalate to user

**Never** ignore an escalation or force retry without changes.

## Dispatching Sub-Agents

### Implementer
```
task(
  agent_type: "general-purpose",
  name: "implement-task-N",
  prompt: "<use template from references/implementer-prompt.md>"
)
```

### Spec Reviewer
```
task(
  agent_type: "general-purpose",
  name: "spec-review-task-N",
  prompt: "<use template from references/spec-reviewer-prompt.md>"
)
```

### Code Quality Reviewer
```
task(
  agent_type: "code-review",
  name: "quality-review-task-N",
  prompt: "Review changes between <BASE_SHA> and <HEAD_SHA>.
    What was implemented: <description>
    Requirements: <task spec>"
)
```

## Example Workflow

```
You: I'm using Subagent-Driven Development to execute this plan.

[Read plan file: docs/plans/feature-plan.md]
[Extract all 5 tasks with full text and context]
[Register in SQL todos table]

Task 1: Hook installation script

[Dispatch implementer sub-agent with full task text + context]

Implementer: "Before I begin — should the hook be user or system level?"

You: "User level (~/.config/hooks/)"

Implementer: [implements, tests, commits, self-reviews]
  Status: DONE

[Dispatch spec reviewer]
Spec reviewer: ✅ Spec compliant

[Dispatch code quality reviewer]
Code reviewer: ✅ Approved

[Mark Task 1 done in SQL]

Task 2: Recovery modes
[Continue pattern...]

[After all tasks]
[Dispatch final code-review agent]
[Use finishing-a-development-branch skill]
```

## Task Tracking

Register tasks in SQL when starting:
```sql
INSERT INTO todos (id, title, description, status) VALUES
  ('sdd-task-1', 'Task 1: Hook installation', 'Full task text...', 'pending');
```

Update as work progresses:
```sql
UPDATE todos SET status = 'in_progress' WHERE id = 'sdd-task-1';
UPDATE todos SET status = 'done' WHERE id = 'sdd-task-1';
```

## Red Flags

**Never:**
- Start implementation on main/master without explicit user consent
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed issues
- Dispatch multiple implementation sub-agents in parallel (conflicts)
- Make sub-agent read plan file (provide full text instead)
- Skip scene-setting context
- Ignore sub-agent questions
- Accept "close enough" on spec compliance
- Skip review loops
- **Start code quality review before spec compliance is ✅**
- Move to next task while either review has open issues

**If sub-agent asks questions:**
- Answer clearly and completely
- Provide additional context if needed

**If reviewer finds issues:**
- Implementer (same sub-agent) fixes them
- Reviewer reviews again
- Repeat until approved

**If sub-agent fails task:**
- Dispatch fix sub-agent with specific instructions
- Don't try to fix manually (context pollution)

## Integration

**Required workflow skills:**
- **using-git-worktrees** — Set up isolated workspace before starting
- **writing-plans** — Creates the plan this skill executes
- **requesting-code-review** — Code review template for reviewer sub-agents
- **finishing-a-development-branch** — Complete development after all tasks

**Sub-agents should follow:**
- **test-driven-development** — TDD for each task

**Alternative workflow:**
- **executing-plans** — Use for simpler inline execution instead
