---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace, or before executing implementation plans. Creates isolated git worktrees.
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Directory Selection Process

Follow this priority order:

### 1. Check Existing Directories

```powershell
# Check in priority order
Test-Path .worktrees    # Preferred (hidden-style)
Test-Path worktrees     # Alternative
```

**If found:** Use that directory. If both exist, `.worktrees` wins.

### 2. Check Project Configuration

Look for worktree preferences in project config files (README, contributing docs, etc.).

### 3. Ask User

If no directory exists and no preference found:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden-style)
2. ~/worktrees/<project-name>/ (global location)

Which would you prefer?
```

## Safety Verification

### For Project-Local Directories (.worktrees or worktrees)

**MUST verify directory is ignored before creating worktree:**

```powershell
# Check if directory is ignored
git check-ignore -q .worktrees 2>$null
# Check exit code: 0 = ignored (safe), 1 = not ignored (needs fix)
```

**If NOT ignored:**
1. Add appropriate line to .gitignore
2. Commit the change
3. Proceed with worktree creation

**Why critical:** Prevents accidentally committing worktree contents to repository.

### For Global Directory (~/worktrees)

No .gitignore verification needed - outside project entirely.

## Creation Steps

### 1. Detect Project Name

```powershell
$project = Split-Path (git rev-parse --show-toplevel) -Leaf
```

### 2. Create Worktree

```powershell
# Determine full path based on location choice
$path = ".worktrees\$BRANCH_NAME"  # or global path

# Create worktree with new branch
git worktree add $path -b $BRANCH_NAME
Set-Location $path
```

### 3. Run Project Setup

Auto-detect and run appropriate setup:

```powershell
# Node.js
if (Test-Path package.json) { npm install }

# .NET
if (Test-Path *.sln) { dotnet restore }
if (Test-Path *.csproj) { dotnet restore }

# Python
if (Test-Path requirements.txt) { pip install -r requirements.txt }
if (Test-Path pyproject.toml) { pip install -e . }

# Rust
if (Test-Path Cargo.toml) { cargo build }

# Go
if (Test-Path go.mod) { go mod download }
```

### 4. Verify Clean Baseline

Run tests to ensure worktree starts clean:

```powershell
# Use project-appropriate command
npm test          # Node.js
dotnet test       # .NET
pytest            # Python
cargo test        # Rust
go test ./...     # Go
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### 5. Report Location

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check project config → Ask user |
| Directory not ignored | Add to .gitignore + commit |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |

## Common Mistakes

### Skipping ignore verification

- **Problem:** Worktree contents get tracked, pollute git status
- **Fix:** Always use `git check-ignore` before creating project-local worktree

### Assuming directory location

- **Problem:** Creates inconsistency, violates project conventions
- **Fix:** Follow priority: existing > project config > ask

### Proceeding with failing tests

- **Problem:** Can't distinguish new bugs from pre-existing issues
- **Fix:** Report failures, get explicit permission to proceed

### Hardcoding setup commands

- **Problem:** Breaks on projects using different tools
- **Fix:** Auto-detect from project files (package.json, *.csproj, etc.)

## Example Workflow

```
You: I'm using the using-git-worktrees skill to set up an isolated workspace.

[Check .worktrees/ - exists]
[Verify ignored - git check-ignore confirms .worktrees/ is ignored]
[Create worktree: git worktree add .worktrees\auth -b feature/auth]
[Run npm install]
[Run npm test - 47 passing]

Worktree ready at C:\Users\me\myproject\.worktrees\auth
Tests passing (47 tests, 0 failures)
Ready to implement auth feature
```

## Red Flags

**Never:**
- Create worktree without verifying it's ignored (project-local)
- Skip baseline test verification
- Proceed with failing tests without asking
- Assume directory location when ambiguous
- Skip project config check

**Always:**
- Follow directory priority: existing > config > ask
- Verify directory is ignored for project-local
- Auto-detect and run project setup
- Verify clean test baseline

## Integration

**Called by:**
- **brainstorming** - When design is approved and implementation follows
- **subagent-driven-development** - Before executing any tasks
- **executing-plans** - Before executing any tasks
- Any skill needing isolated workspace

**Pairs with:**
- **finishing-a-development-branch** - For cleanup after work complete
