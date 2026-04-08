---
name: setup-superpowers
description: Install or update Agency Superpowers skills globally from a repo URL. Use when someone says "set up superpowers", "install skills", or "update my superpowers".
---

# Setup Superpowers

This skill installs or updates the Agency Superpowers skill collection from a team repository into `~/.copilot/skills/` so they are available globally — in every Copilot CLI session, regardless of which repo the user is working in.

## When to Use

- A user says "set up superpowers", "install skills", "update my superpowers"
- A user provides a repo URL and wants skills installed
- A user asks how to get the team's Copilot skills

## Process

### Step 1: Get the Repository URL

If the user hasn't provided a repo URL, ask for it using the `ask_user` tool:

```
"What is the URL of the repository containing the Agency Superpowers skills? This is the team repo where the skills are published in `.github/skills/`."
```

The URL will typically be an Azure DevOps or GitHub repo URL, for example:
- `https://dev.azure.com/org/project/_git/repo-name`
- `https://github.com/org/repo-name`

### Step 2: Clone the Repository

Clone the repo to a temporary directory. Use a shallow clone to minimize download time:

```powershell
# Windows
$tempDir = Join-Path $env:TEMP "superpowers-install-$(Get-Random)"
git clone --depth 1 --single-branch "<REPO_URL>" $tempDir
```

```bash
# macOS/Linux
tempDir=$(mktemp -d)
git clone --depth 1 --single-branch "<REPO_URL>" "$tempDir"
```

### Step 3: Verify Skills Exist

Check that the cloned repo has `.github/skills/` with skill folders inside:

```powershell
$skillsSource = Join-Path $tempDir ".github" "skills"
if (-not (Test-Path $skillsSource)) {
    Write-Host "ERROR: No .github/skills/ directory found in this repo."
    # Clean up and inform the user
}
```

List what's available and confirm with the user before copying.

### Step 4: Copy Skills to Global Location

Copy each skill folder to `~/.copilot/skills/`, overwriting existing versions:

```powershell
# Windows
$dest = Join-Path $env:USERPROFILE ".copilot" "skills"
if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest -Force }

$skillFolders = Get-ChildItem $skillsSource -Directory
foreach ($folder in $skillFolders) {
    $targetPath = Join-Path $dest $folder.Name
    if (Test-Path $targetPath) {
        Remove-Item $targetPath -Recurse -Force
    }
    Copy-Item $folder.FullName -Destination $targetPath -Recurse
    Write-Host "  Installed: $($folder.Name)"
}
```

```bash
# macOS/Linux
dest="$HOME/.copilot/skills"
mkdir -p "$dest"
for folder in "$skillsSource"/*/; do
    name=$(basename "$folder")
    rm -rf "$dest/$name"
    cp -r "$folder" "$dest/$name"
    echo "  Installed: $name"
done
```

### Step 5: Clean Up

Remove the temporary clone:

```powershell
# Windows
Remove-Item $tempDir -Recurse -Force
```

```bash
# macOS/Linux
rm -rf "$tempDir"
```

### Step 6: Confirm and Guide

After installation, tell the user:

1. **How many skills were installed** — list them
2. **They need to start a new session** — skills load at session start, so current session won't see new skills
3. **How to update later** — just say "update my superpowers" with the same repo URL
4. **Where skills are stored** — `~/.copilot/skills/` on their machine

Use this summary format:

```
✅ Installed X skills to ~/.copilot/skills/

Skills installed:
  - agency-superpowers
  - brainstorming
  - ...

To use them: Start a new Copilot CLI session. Skills activate automatically.
To update later: Say "update my superpowers from <repo-url>"
To learn more: Open ~/.copilot/skills/README.md
```

## Important Notes

- **Existing personal skills are preserved.** Only skill folders that match names from the repo are overwritten. Other skills in `~/.copilot/skills/` are untouched.
- **This skill must already be installed** for a user to invoke it. For first-time setup, either:
  - The user copies just this one skill folder manually, then uses it to install the rest
  - Someone shares the `setup-superpowers` folder directly
  - The user runs the git clone + copy commands from the README manually
- **Credentials**: The `git clone` command uses whatever git credentials the user has configured. If they can't clone the repo, they need to set up access first.

## Error Handling

| Error | Response |
|-------|----------|
| `git clone` fails | Check the URL is correct and the user has access. Suggest checking git credentials. |
| No `.github/skills/` in repo | The repo may not have skills published yet. Confirm the correct repo was provided. |
| Permission denied on copy | Check that `~/.copilot/skills/` is writable. On Windows, run as the current user (not admin). |
| Skill folders are empty | Warn the user — a valid skill needs at least a `SKILL.md` file. |
