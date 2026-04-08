---
name: finishing-a-development-branch
description: Use when implementation is complete and all tests pass. Guides branch completion — merge, PR, or cleanup.
---

# Finishing a Development Branch

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Verify tests → Present options → Execute choice → Clean up.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

## The Process

### Step 1: Verify Tests

**Before presenting options, verify tests pass:**

```powershell
# Run project's test suite (auto-detect)
npm test        # Node.js
dotnet test     # .NET
pytest          # Python
cargo test      # Rust
go test ./...   # Go
```

**If tests fail:**
```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Don't proceed to Step 2.

**If tests pass:** Continue to Step 2.

### Step 2: Determine Base Branch

```powershell
# Determine the base branch name (not just the merge-base commit)
$baseBranch = $null
foreach ($candidate in @('main', 'master', 'develop')) {
    if (git rev-parse --verify "origin/$candidate" 2>$null) {
        $baseBranch = $candidate
        break
    }
}
```

If no common base branch is found, ask: "Which branch should this merge into?"

Otherwise confirm: "This branch split from `<base-branch>` — is that correct?"

### Step 3: Present Options

Present exactly these options:

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request (GitHub)
3. Push and create a Pull Request (Azure DevOps)
4. Keep the branch as-is (I'll handle it later)
5. Discard this work

Which option?
```

### Step 4: Execute Choice

#### Option 1: Merge Locally

```powershell
git checkout <base-branch>
git pull
git merge <feature-branch>
# Verify tests on merged result
<test command>
# If tests pass
git branch -d <feature-branch>
```

Then: Cleanup worktree (Step 5)

#### Option 2: GitHub PR

```powershell
git push -u origin <feature-branch>

# Create PR via gh CLI
gh pr create --title "<title>" --body @"
## Summary
- <2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
"@
```

Then: Cleanup worktree (Step 5)

#### Option 3: Azure DevOps PR

Use the `ado-repo_create_pull_request` tool:

```
ado-repo_create_pull_request(
  repositoryId: "<repo-name>",
  project: "<project-name>",
  sourceRefName: "refs/heads/<feature-branch>",
  targetRefName: "refs/heads/<base-branch>",
  title: "<PR title>",
  description: "## Summary\n- <what changed>"
)
```

Then: Cleanup worktree (Step 5)

#### Option 4: Keep As-Is

Report: "Keeping branch `<name>`. Worktree preserved at `<path>`."

**Don't cleanup worktree.**

#### Option 5: Discard

**Confirm first using `ask_user`:**
```
This will permanently delete:
- Branch <name>
- Worktree at <path> (if applicable)

Commits remain recoverable via reflog for ~30 days.

Are you sure?
```

Wait for explicit confirmation.

If confirmed:
```powershell
git checkout <base-branch>
git branch -D <feature-branch>
```

Then: Cleanup worktree (Step 5)

### Step 5: Cleanup Worktree

**For Options 1, 2, 3, 5:**

Check if in worktree:
```powershell
$currentBranch = git branch --show-current
if ($currentBranch) {
    $worktreeEntry = git worktree list | Select-String $currentBranch
    if ($worktreeEntry) {
        # Extract worktree path (first field of the matching line)
        $worktreePath = ($worktreeEntry -split '\s+')[0]
        git checkout <base-branch>
        git worktree remove $worktreePath
    }
}
```

**For Option 4:** Keep worktree.

## Quick Reference

| Option | Merge | Push | Keep Worktree | Cleanup Branch |
|--------|-------|------|---------------|----------------|
| 1. Merge locally | ✓ | - | - | ✓ |
| 2. GitHub PR | - | ✓ | - | - |
| 3. Azure DevOps PR | - | ✓ | - | - |
| 4. Keep as-is | - | - | ✓ | - |
| 5. Discard | - | - | - | ✓ (force) |

## Common Mistakes

**Skipping test verification**
- **Problem:** Merge broken code, create failing PR
- **Fix:** Always verify tests before offering options

**Open-ended questions**
- **Problem:** "What should I do next?" → ambiguous
- **Fix:** Present structured options using `ask_user` with `choices`

**No confirmation for discard**
- **Problem:** Accidentally delete work
- **Fix:** Require explicit confirmation via `ask_user`

## Red Flags

**Never:**
- Proceed with failing tests
- Merge without verifying tests on result
- Delete work without confirmation
- Force-push without explicit request

**Always:**
- Verify tests before offering options
- Present structured options
- Get explicit confirmation for discard
- Clean up worktree for merge and discard options

## Integration

**Called by:**
- **subagent-driven-development** — After all tasks complete
- **executing-plans** — After all batches complete

**Pairs with:**
- **using-git-worktrees** — Cleans up worktree created by that skill
