---
name: dispatching-parallel-agents
description: Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies.
---

# Dispatching Parallel Agents

## Overview

When you have multiple unrelated problems (different test files, different subsystems, different bugs), investigating them sequentially wastes time. Each investigation is independent and can happen in parallel.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

**Use when:**
- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood without context from others
- No shared state between investigations

**Don't use when:**
- Failures are related (fix one might fix others)
- Need to understand full system state
- Agents would interfere with each other (editing same files)

## The Pattern

### 1. Identify Independent Domains

Group failures by what's broken:
- File A tests: Tool approval flow
- File B tests: Batch completion behavior
- File C tests: Abort functionality

Each domain is independent — fixing one doesn't affect the others.

### 2. Create Focused Agent Tasks

Each agent gets:
- **Specific scope:** One test file or subsystem
- **Clear goal:** Make these tests pass
- **Constraints:** Don't change other code
- **Expected output:** Summary of findings and fixes

### 3. Dispatch in Parallel

Use the `task` tool with `mode: "background"` for parallel dispatch:

```
task(
  agent_type: "task",
  name: "fix-abort-tests",
  mode: "background",
  prompt: "Fix the 3 failing tests in agent-tool-abort.test.ts: ..."
)

task(
  agent_type: "task",
  name: "fix-batch-tests",
  mode: "background",
  prompt: "Fix the 2 failing tests in batch-completion.test.ts: ..."
)

task(
  agent_type: "task",
  name: "fix-race-tests",
  mode: "background",
  prompt: "Fix the 1 failing test in tool-approval-races.test.ts: ..."
)
```

All three run concurrently. You'll be notified when each completes.

### 4. Review and Integrate

When agents return (use `read_agent` to get results):
- Read each summary
- Verify fixes don't conflict
- Run full test suite
- Integrate all changes

## Agent Prompt Structure

Good agent prompts are:
1. **Focused** — One clear problem domain
2. **Self-contained** — All context needed to understand the problem
3. **Specific about output** — What should the agent return?

**Example:**
```markdown
Fix the 3 failing tests in src/agents/agent-tool-abort.test.ts:

1. "should abort tool with partial output capture" — expects 'interrupted at' in message
2. "should handle mixed completed and aborted tools" — fast tool aborted instead of completed
3. "should properly track pendingToolCount" — expects 3 results but gets 0

These are timing/race condition issues. Your task:

1. Read the test file and understand what each test verifies
2. Identify root cause — timing issues or actual bugs?
3. Fix by replacing arbitrary timeouts with event-based waiting
4. Do NOT just increase timeouts — find the real issue

Return: Summary of what you found and what you fixed.
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| **Too broad:** "Fix all the tests" | **Specific:** "Fix agent-tool-abort.test.ts" |
| **No context:** "Fix the race condition" | **Context:** Paste error messages and test names |
| **No constraints:** Agent might refactor everything | **Constraints:** "Fix tests only, don't change prod code" |
| **Vague output:** "Fix it" | **Specific:** "Return summary of root cause and changes" |

## When NOT to Use

- **Related failures:** Fix one might fix others — investigate together first
- **Need full context:** Understanding requires seeing entire system
- **Exploratory debugging:** You don't know what's broken yet
- **Shared state:** Agents would interfere (editing same files, using same resources)

## Verification

After agents return:
1. **Review each summary** — Understand what changed
2. **Check for conflicts** — Did agents edit same code?
3. **Run full suite** — Verify all fixes work together
4. **Spot check** — Agents can make systematic errors

## Key Benefits

1. **Parallelization** — Multiple investigations simultaneously
2. **Focus** — Each agent has narrow scope
3. **Independence** — Agents don't interfere
4. **Speed** — N problems solved in time of 1
