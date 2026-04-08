# Hockey Vision

Ice hockey video analysis tool for tracking player performance from rink-level game footage and skills sessions.

## Two Modes

### Game Analysis
Track yourself by jersey number through a full game. Outputs:
- Position heatmap
- Shift detection and duration chart
- Ice time, distance, speed estimates
- Annotated video highlighting your position

### Skills Analysis
Analyze skating form from skills class or practice footage. Outputs:
- Pose estimation with skeleton overlay
- Knee bend angles (target: 90-120 degrees for good hockey stance)
- Forward lean measurement
- Stride width tracking
- Session-over-session improvement comparison
- Annotated video with real-time form metrics

## Setup

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

YOLO model weights download automatically on first run.

## Usage

```bash
# Analyze a game — track jersey #17
python main.py game path/to/game.mp4 --jersey 17

# Analyze a skills session
python main.py skills path/to/skills.mp4

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

## Configuration

Edit `config.yaml` to adjust detection confidence, sampling rate, and analysis parameters.

## Tech Stack

- **Detection**: YOLOv11 (ultralytics)
- **Tracking**: ByteTrack
- **Pose estimation**: YOLOv11-pose
- **Jersey OCR**: PaddleOCR
- **Homography**: OpenCV
