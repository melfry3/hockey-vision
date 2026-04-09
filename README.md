# Hockey Vision

Ice hockey video analysis tool for tracking player performance from rink-level game footage and skills sessions. Built-in AI coaching copilot provides actionable feedback and tracks improvement over time.

## Two Analysis Modes

### Game Analysis
Track yourself by jersey number through a full game. Outputs:
- Position heatmap
- Shift detection and duration chart
- Ice time, distance, speed estimates
- Annotated video highlighting your position
- AI coaching feedback on positioning and effort

### Skills Analysis
Analyze skating form from skills class or practice footage. Outputs:
- Pose estimation with skeleton overlay
- Knee bend angles (target: 90-120 degrees for good hockey stance)
- Forward lean measurement
- Stride width tracking
- Annotated video with real-time form metrics
- AI coaching feedback on form and improvement areas

## AI Copilot

Every analysis automatically saves to your session history. The AI coach (powered by Claude) can:
- **Review** your latest session with specific feedback
- **Compare** sessions to show what improved or regressed
- **Plan** a multi-week improvement program from your full history
- **Answer** open-ended hockey questions with your data as context

## Setup

### Prerequisites
- **Python 3.12+** — [Download](https://www.python.org/downloads/) (check "Add to PATH" during install)
- **NVIDIA GPU** (optional but recommended) — CUDA 12.8+ for GPU acceleration

### Install

**PowerShell (Windows):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
```

**Bash (Linux/Mac/WSL):**
```bash
python -m venv venv
source venv/bin/activate
pip install torch torchvision
pip install -r requirements.txt
```

> **Troubleshooting venv:** If `.\venv\Scripts\Activate.ps1` fails, you may need to set the execution policy first:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> If the venv folder wasn't created at all, check that Python is properly installed (`python --version` should show output).

YOLO model weights download automatically on first run.

Set your API key for AI coaching:
```powershell
$env:ANTHROPIC_API_KEY = "your-key-here"   # PowerShell
```
```bash
export ANTHROPIC_API_KEY=your-key-here     # Bash
```

## Usage

**PowerShell** — use backtick `` ` `` for line continuation:
```powershell
# Analyze a game — track jersey #17
python main.py game "C:\path\to\game.mp4" -j 17

# Multi-period game with options
python main.py game `
  "C:\path\to\period1.mp4" `
  "C:\path\to\period2.mp4" `
  "C:\path\to\period3.mp4" `
  -j 83 --color white --skip-warmup 600 `
  --label "2026-04-03-ice-ranch-league" --no-coach

# Analyze a skills session
python main.py skills "C:\path\to\skills.mp4" --label "2026-04-07-skills-class"
```

**Bash:**
```bash
# Analyze a game — track jersey #17
python main.py game path/to/game.mp4 --jersey 17

# Analyze a game with a label for tracking
python main.py game path/to/game.mp4 -j 17 --label "2026-04-07-league"

# Analyze a skills session
python main.py skills path/to/skills.mp4 --label "2026-04-07-skills-class"
```

**Common commands (both shells):**
```bash

# Ask your AI coach anything
python main.py ask "How can I improve my first stride?"
python main.py ask -m skills "Why is my knee bend so shallow?"

# Get a coaching review comparing your latest to previous
python main.py review -m skills
python main.py review -m game

# Generate an improvement plan from all sessions
python main.py plan -m skills

# View session history
python main.py sessions
python main.py sessions -m game

# Track a metric over time
python main.py trend -m skills summary.knee_bend.mean

# Calibrate rink homography (optional — improves position accuracy)
python main.py calibrate path/to/game.mp4
```

## Output

Results go to `output/` by default:
- `game_stats.json` — shift times, ice time, distance
- `heatmap.png` — where you spent time on the ice
- `shifts.png` — shift duration bar chart
- `skills_stats.json` — form metrics summary
- `skills_annotated.mp4` — video with pose overlay

Session history is saved to `sessions/` for cross-session comparison.

## Configuration

Edit `config.yaml` to adjust detection confidence, sampling rate, and analysis parameters.

## Tech Stack

- **Detection**: YOLOv11 (ultralytics)
- **Tracking**: ByteTrack
- **Pose estimation**: YOLOv11-pose
- **Jersey OCR**: PaddleOCR
- **Homography**: OpenCV
- **AI Coaching**: Claude (Anthropic API)
