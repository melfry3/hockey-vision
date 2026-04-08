# Agency Superpowers — Copilot CLI Skills

A complete software development workflow for GitHub Copilot CLI, adapted from [obra/superpowers](https://github.com/obra/superpowers).

## What It Does

From the moment you start working, these skills guide you through a disciplined workflow:

1. **Brainstorm** — Refine ideas through questions before writing code
2. **Plan** — Break work into bite-sized TDD tasks with exact file paths and code
3. **Execute** — Sub-agents implement each task with two-stage review
4. **Verify** — Evidence-based completion, never "should work now"
5. **Finish** — Merge, PR, or cleanup with structured options

The skills trigger automatically based on what you're doing. No special commands needed.

## Skills Catalog

### Core Workflow
| Skill | Purpose |
|-------|---------|
| `agency-superpowers` | Master skill — establishes how all skills work |
| `brainstorming` | Design refinement before coding |
| `writing-plans` | Detailed implementation plans |
| `executing-plans` | Plan execution with checkpoints |
| `subagent-driven-development` | Sub-agent per task with review gates |
| `finishing-a-development-branch` | Merge/PR/discard workflow |

### Development Discipline
| Skill | Purpose |
|-------|---------|
| `test-driven-development` | RED-GREEN-REFACTOR cycle |
| `systematic-debugging` | Root cause investigation process |
| `verification-before-completion` | Evidence before claims |

### Collaboration
| Skill | Purpose |
|-------|---------|
| `requesting-code-review` | Dispatch code review agents |
| `receiving-code-review` | Handle feedback with technical rigor |

### Infrastructure
| Skill | Purpose |
|-------|---------|
| `using-git-worktrees` | Isolated workspaces for feature work |
| `dispatching-parallel-agents` | Concurrent agent workflows |

### Meta
| Skill | Purpose |
|-------|---------|
| `writing-skills` | Create new Copilot CLI skills |

## Installation

### Per-User (global)

Copy all skill folders to `~/.copilot/skills/`:

```powershell
# Windows
$source = "path\to\agency-superpowers\skills"
$dest = "$env:USERPROFILE\.copilot\skills"
Get-ChildItem $source -Directory | ForEach-Object {
    Copy-Item $_.FullName -Destination "$dest\$($_.Name)" -Recurse -Force
}
```

```bash
# macOS/Linux
cp -r path/to/agency-superpowers/skills/* ~/.copilot/skills/
```

### Per-Repository (team sharing)

Copy skill folders to `.github/skills/` in your repo:

```
your-repo/
└── .github/
    └── skills/
        ├── agency-superpowers/
        ├── brainstorming/
        ├── test-driven-development/
        └── ...
```

Skills placed here are auto-discovered for anyone using Copilot CLI in that repo.

## Verify Installation

Start a new Copilot CLI session and try:
- "Help me plan a new feature" → should trigger `brainstorming`
- "Fix this failing test" → should trigger `systematic-debugging`
- "Let's implement the plan" → should trigger `subagent-driven-development`

## Philosophy

- **Test-Driven Development** — Write tests first, always
- **Systematic over ad-hoc** — Process over guessing
- **Complexity reduction** — Simplicity as primary goal
- **Evidence over claims** — Verify before declaring success

## Credits

Adapted from [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent. Original licensed under MIT.
