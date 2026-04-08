---
name: agency-superpowers
description: Master skill — establishes how to find and use all superpowers skills. Invoke at session start or when unsure which skill applies.
---

# Agency Superpowers

You have superpowers — a complete set of software development workflow skills that make you dramatically more effective.

## IMPORTANT

If you think there is even a 1% chance a skill might apply to what you are doing, you MUST invoke it. This is not optional. You cannot rationalize your way out of this.

## Instruction Priority

Superpowers skills override default behavior, but **user instructions always take precedence**:

1. **User's explicit instructions** (direct requests, project config) — highest priority
2. **Superpowers skills** — override default behavior where they conflict
3. **Default system prompt** — lowest priority

## How to Access Skills

Use the `skill` tool to invoke any skill by name. When you invoke a skill, its content is loaded — follow it directly.

## The Rule

**Invoke relevant skills BEFORE any response or action.** Even a 1% chance a skill might apply means invoke it to check. If the invoked skill turns out to be wrong for the situation, you don't need to use it.

## Available Skills

### Core Workflow (in order)
| Skill | When to Use |
|-------|-------------|
| `brainstorming` | Before any creative work — features, components, design |
| `writing-plans` | After design approval, before coding |
| `subagent-driven-development` | Executing plans with sub-agents (recommended) |
| `executing-plans` | Executing plans inline in current session |
| `finishing-a-development-branch` | When implementation is complete |

### Development Discipline
| Skill | When to Use |
|-------|-------------|
| `test-driven-development` | Before writing ANY implementation code |
| `systematic-debugging` | When encountering ANY bug or test failure |
| `verification-before-completion` | Before claiming work is done |

### Collaboration
| Skill | When to Use |
|-------|-------------|
| `requesting-code-review` | After completing tasks or before merging |
| `receiving-code-review` | When handling review feedback |

### Infrastructure
| Skill | When to Use |
|-------|-------------|
| `using-git-worktrees` | Starting feature work needing isolation |
| `dispatching-parallel-agents` | 2+ independent tasks to run concurrently |
| `setup-superpowers` | Installing or updating skills from a repo URL |

## Red Flags

These thoughts mean STOP — you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Skill Priority

When multiple skills could apply, use this order:

1. **Process skills first** (brainstorming, debugging) — these determine HOW to approach the task
2. **Implementation skills second** — these guide execution

"Let's build X" → brainstorming first, then implementation skills.
"Fix this bug" → systematic-debugging first, then domain-specific skills.

## Skill Types

**Rigid** (TDD, debugging, verification): Follow exactly. Don't adapt away discipline.

**Flexible** (brainstorming, patterns): Adapt principles to context.

The skill itself tells you which.

## User Instructions

Instructions say WHAT, not HOW. "Add X" or "Fix Y" doesn't mean skip workflows.
