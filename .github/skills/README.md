# Agency Superpowers — Copilot CLI Skills

A complete software development workflow for [GitHub Copilot CLI](https://docs.github.com/en/copilot), adapted from [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent.

---

## What Is This?

Agency Superpowers is a collection of **skills** for GitHub Copilot CLI. Skills are structured instructions that teach Copilot CLI how to approach specific tasks — brainstorming, planning, test-driven development, debugging, code review, and more.

Instead of relying on Copilot's default behavior, these skills enforce a disciplined engineering workflow. They activate automatically based on what you're doing. No special commands needed — just work normally and the right skill engages.

### The Workflow

```
  Brainstorm ──▶ Plan ──▶ Implement ──▶ Verify ──▶ Finish
     │             │          │            │          │
 Refine ideas   Break into   TDD with    Evidence   Merge/PR
 via questions  bite-sized   sub-agents   before     or discard
                tasks                     claiming
                                          "done"
```

---

## How Skills Work

### What Is a Skill?

A skill is a folder containing a `SKILL.md` file. This file has two parts:

1. **YAML frontmatter** — a `name` and `description` that Copilot CLI uses to decide when to activate the skill
2. **Markdown body** — the instructions Copilot follows when the skill is invoked

Example structure:

```
brainstorming/
├── SKILL.md              # Main instructions (required)
├── references/           # Supporting docs, loaded on demand (optional)
│   └── design-patterns.md
└── scripts/              # Helper scripts (optional)
    └── scaffold.sh
```

### How Does Copilot CLI Find Skills?

Copilot CLI looks for skills in two locations:

| Location | Scope | Best For |
|----------|-------|----------|
| `~/.copilot/skills/` | **Global** — available in every session, everywhere | Individual engineers, PMs, anyone who wants skills regardless of what repo they're in |
| `.github/skills/` (in a repo) | **Repository** — available to anyone working in that specific repo | Teams who want shared skills tied to a codebase |

Both locations work the same way. Copilot CLI scans them at session start and loads every `SKILL.md` it finds.

### How Do Skills Activate?

Each skill's `description` field contains trigger phrases. When your message matches, Copilot CLI loads the skill and follows its instructions. For example:

- You say *"help me think through the auth design"* → matches `brainstorming` skill
- You say *"this test is failing"* → matches `systematic-debugging` skill
- You say *"let's implement the plan"* → matches `subagent-driven-development` skill

You can also invoke any skill explicitly by name. Skills can reference other skills — for example, `subagent-driven-development` automatically invokes `test-driven-development` during implementation.

---

## Skills Catalog

### Core Workflow (in order)
| Skill | What It Does | Triggers When You… |
|-------|--------------|--------------------|
| **brainstorming** | Structured design exploration — asks questions before code | Say "help me think through…" or start a new feature |
| **writing-plans** | Creates detailed implementation plans with SQL task tracking | Say "let's plan…" or need to break down work |
| **executing-plans** | Follows a plan step-by-step with review checkpoints | Start working through a plan inline |
| **subagent-driven-development** | Dispatches a fresh sub-agent per task with two-stage review | Implement a plan using parallel agents |
| **finishing-a-development-branch** | Merge, PR, or discard workflows | Complete implementation, ready to ship |

### Development Discipline
| Skill | What It Does | Triggers When You… |
|-------|--------------|--------------------|
| **test-driven-development** | Enforces RED → GREEN → REFACTOR cycle | Write any implementation code |
| **systematic-debugging** | 4-phase root cause investigation process | Hit a bug, test failure, or unexpected behavior |
| **verification-before-completion** | Requires evidence before declaring "done" | Claim work is complete or fixed |

### Collaboration
| Skill | What It Does | Triggers When You… |
|-------|--------------|--------------------|
| **requesting-code-review** | Dispatches code review agents for feedback | Want code reviewed before merging |
| **receiving-code-review** | Handles review feedback with technical rigor | Receive code review comments to address |

### Infrastructure
| Skill | What It Does | Triggers When You… |
|-------|--------------|--------------------|
| **using-git-worktrees** | Creates isolated git workspaces per feature | Start feature work needing isolation |
| **dispatching-parallel-agents** | Runs 2+ independent agents concurrently | Have independent tasks to parallelize |

### Meta
| Skill | What It Does | Triggers When You… |
|-------|--------------|--------------------|
| **agency-superpowers** | Master index — connects all skills together | Start a session or ask "what skills do I have?" |
| **writing-skills** | Guide for creating new Copilot CLI skills | Want to build a new skill |
| **setup-superpowers** | Installs skills globally from a repo URL | Need skills outside the team repo |

---

## Two Ways to Get Skills

### Use Case 1: Engineers Working in the Team Repo

**How it works:** Skills live in the repo's `.github/skills/` directory. When an engineer clones the repo and opens Copilot CLI inside it, all skills are automatically available. No setup required.

```
team-repo/
├── .github/
│   └── skills/
│       ├── agency-superpowers/
│       │   └── SKILL.md
│       ├── brainstorming/
│       │   └── SKILL.md
│       ├── test-driven-development/
│       │   ├── SKILL.md
│       │   └── references/
│       │       └── testing-anti-patterns.md
│       └── ... (all skill folders)
├── src/
└── README.md
```

**What this means for engineers:**
- `git clone` the repo → skills are there
- `git pull` → skills update automatically
- No per-user configuration needed
- Skills are version-controlled and PR-reviewable like any other code
- Everyone on the team gets the same skills, same versions

**Limitation:** Skills only activate when Copilot CLI is running inside this repo's directory. If the engineer opens Copilot CLI somewhere else, these skills won't be loaded.

### Use Case 2: Team Members Not Working in the Repo

Some team members — PMs, designers, managers, or engineers working across many repos — may want these skills available everywhere, not just inside one specific repo.

**How it works:** The `setup-superpowers` skill clones the team repo, copies all skill folders to `~/.copilot/skills/` (the global location), and cleans up. After that, skills are available in every Copilot CLI session regardless of which directory or repo the user is in.

**To set up:**

1. Open Copilot CLI from anywhere
2. Say: *"Set up agency superpowers from https://dev.azure.com/org/project/_git/repo"*
3. The `setup-superpowers` skill handles the rest — clones the repo, copies skills, cleans up

**What this means for non-repo users:**
- One-time setup, skills work everywhere after that
- To update: just say *"Update my superpowers"* and run the setup again
- Skills are stored locally at `~/.copilot/skills/` — no ongoing repo dependency
- Works for anyone with access to the team repo URL

### Which Should I Use?

| Situation | Recommended Approach |
|-----------|---------------------|
| Engineer working primarily in the team repo | **Repo-based** — automatic, zero setup |
| Engineer working across multiple repos | **Global install** via `setup-superpowers` |
| PM, designer, or manager | **Global install** via `setup-superpowers` |
| Trying it out before team rollout | **Global install** to `~/.copilot/skills/` |

Both approaches can coexist. If someone has skills in both locations, Copilot CLI loads both sets.

---

## Key Principles

- **Test-Driven Development** — Write tests before implementation, always
- **Systematic over ad-hoc** — Follow a process instead of guessing
- **Complexity reduction** — Simplest solution that works
- **Evidence over claims** — Demonstrate it works before saying it does
- **User instructions are king** — Skills guide *how* to do things; your instructions determine *what* to do

---

## Quick Test

After installation, open a new Copilot CLI session and try:

| Say This | Expected Skill |
|----------|---------------|
| "Help me brainstorm a caching layer" | `brainstorming` |
| "Plan out the auth module" | `writing-plans` |
| "This test is failing, help me debug" | `systematic-debugging` |
| "Let's implement the plan" | `subagent-driven-development` |
| "Review my changes before I merge" | `requesting-code-review` |

---

## Customizing

- **Edit any SKILL.md** to adjust behavior for your workflow
- **Add new skills** using the `writing-skills` skill as a guide
- **Disable a skill** by renaming its folder (e.g., `brainstorming` → `_brainstorming`)

---

## Credits

Adapted from [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent (MIT licensed). Ported to GitHub Copilot CLI skill format with tool mapping, Windows/PowerShell support, and ADO integration.
