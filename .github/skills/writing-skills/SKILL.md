---
name: writing-skills
description: Use when creating new Copilot CLI skills, editing existing skills, or verifying skills work. Guides the skill creation process.
---

# Writing Skills

## Overview

Create well-structured Copilot CLI skills that follow best practices for progressive disclosure, token efficiency, and reliable triggering.

## Skill Installation Location

All skills live at: `~/.copilot/skills/{skill-name}/`
(Resolves to `$env:USERPROFILE\.copilot\skills\{skill-name}\` on Windows)

For team sharing, skills can also be placed at `.github/skills/{skill-name}/` in any repository.

## Skill Folder Structure

```
{skill-name}/
├── SKILL.md          # Required — core instructions
├── scripts/          # Optional — executable code (Python, PowerShell, etc.)
├── references/       # Optional — heavy reference docs, prompt templates
└── assets/           # Optional — templates, config files, sample data
```

## Three-Level Progressive Disclosure

### Level 1: YAML Frontmatter (always loaded — keep TINY)

```yaml
---
name: {kebab-case-name}
description: {One sentence: what it does + when to trigger. Max 200 chars.}
---
```

**Frontmatter rules:**
- `name`: kebab-case, descriptive, 2-4 words
- `description`: Must answer "what does this do?" AND "when should it activate?"
- Include natural trigger phrases (e.g., "Use when encountering any bug or test failure")
- This is loaded for EVERY conversation — every extra word costs tokens

### Level 2: SKILL.md Body (loaded when skill activates)

Structure the body in this order:

1. **# Skill Name** — H1 title
2. **Overview** — What this skill does and why (2-3 sentences)
3. **When to Use** — Clear trigger conditions
4. **The Process / Checklist** — Step-by-step instructions
5. **Key Principles** — Important rules and anti-patterns
6. **Integration** — How this skill connects to others
7. **Red Flags** — Warning signs of misuse

**Body rules:**
- Be specific and actionable — write instructions the AI can follow without ambiguity
- Use numbered steps for workflows
- Specify exact tool names (`view`, `edit`, `grep`, `task`, `ask_user`, `sql`)
- Include default values inline
- Show example formats where helpful
- Reference Copilot CLI tools by their actual names:

| Purpose | Tool |
|---------|------|
| Read files | `view` |
| Edit files | `edit` |
| Create files | `create` |
| Search file names | `glob` |
| Search file contents | `grep` |
| Run commands | `powershell` |
| Ask user questions | `ask_user` |
| Sub-agent dispatch | `task` (explore, task, general-purpose, code-review) |
| Task tracking | `sql` (todos table) |
| Invoke other skills | `skill` |
| Web requests | `web_fetch` |

### Level 3: references/ (loaded only when explicitly needed)

Put heavy content here to save tokens:
- Prompt templates for sub-agents
- API specifications
- Exhaustive troubleshooting guides
- Detailed schemas or data dictionaries
- Code examples

Reference from SKILL.md: "See `references/api-spec.md` for full details."

## Creating a New Skill

1. **Clarify the purpose** — Ask what the skill should do if not obvious
2. **Choose a name** — kebab-case, 2-4 words (e.g., `sprint-reporter`, `code-reviewer`)
3. **Scaffold the folder:**
   ```powershell
   $name = "my-new-skill"
   $base = "$env:USERPROFILE\.copilot\skills\$name"
   New-Item -ItemType Directory -Path $base -Force
   New-Item -ItemType Directory -Path "$base\references" -Force
   ```
4. **Generate SKILL.md** following the three-level model
5. **Add references** if there's heavy documentation
6. **Add scripts** if the skill needs executable code
7. **Verify** — Read back SKILL.md and confirm with user
8. **Test** — Tell user to start a new session and try a trigger phrase

## Writing Effective Skills

### DO:
- **Be opinionated** — Tell the AI what to do, not what it could do
- **Use checklists** — Numbered steps prevent skipping
- **Include anti-patterns** — Show what NOT to do with examples
- **Add rationalization tables** — Map common excuses to correct behavior
- **Reference other skills** — Build on existing workflow (e.g., "use `test-driven-development` skill")
- **Show exact tool usage** — `use the task tool with agent_type: "code-review"`

### DON'T:
- **Long frontmatter** — Wastes tokens on every conversation
- **Vague triggers** — "Use this for various tasks" → will never fire
- **API specs in body** — Put in `references/`
- **Missing steps** — "Handle X" without explaining how
- **Overwriting files** — Read with `view` first, then `edit`

## Quality Checklist

Before finishing, verify:
- [ ] Frontmatter description under 200 chars with trigger phrases
- [ ] Body follows structure: Overview → When to Use → Process → Principles → Integration
- [ ] Each capability has clear trigger + numbered steps
- [ ] Tool usage is explicit (which tools for what)
- [ ] Default values specified inline
- [ ] Heavy reference material in `references/`, not in body
- [ ] No redundant content between frontmatter and body
- [ ] Inter-skill references use correct names

## Testing Skills

The best way to test a skill is to start a new Copilot CLI session and use a trigger phrase that should activate it. Verify:

1. **Triggering** — Does the skill activate when expected?
2. **Process** — Does the AI follow the steps correctly?
3. **Anti-patterns** — Does the AI resist rationalizing away discipline?
4. **Integration** — Do references to other skills work?

If a skill doesn't trigger, check the `description` field — it may need better trigger phrases.
