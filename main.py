"""Hockey Vision CLI — analyze your hockey game and skills footage."""

import click
import yaml
import os
import json


def load_config(config_path="config.yaml"):
    if os.path.exists(config_path):
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


@click.group()
def cli():
    """Hockey Vision — ice hockey video analysis."""
    pass


# ---------------------------------------------------------------------------
# Core analysis commands
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("videos", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--jersey", "-j", type=int, required=True, help="Your jersey number")
@click.option("--color", type=click.Choice(["white", "dark"]), default=None,
              help="Your team's jersey color (helps with detection)")
@click.option("--skip-warmup", type=int, default=0,
              help="Seconds to skip at the start of the first clip (warmup)")
@click.option("--identify-at", type=int, default=None,
              help="Seconds into first clip to open player identification browser")
@click.option("--output", "-o", default="output", help="Output directory")
@click.option("--config", "-c", default="config.yaml", help="Config file path")
@click.option("--label", "-l", default=None, help="Session label (e.g. '2026-04-04-league')")
@click.option("--coach/--no-coach", default=True, help="Get AI coaching feedback after analysis")
def game(videos, jersey, color, skip_warmup, identify_at, output, config, label, coach):
    """Analyze game video(s). Supports multiple clips for one game.

    Examples:
        python main.py game clip1.mp4 -j 83 --color white
        python main.py game clip1.mp4 clip2.mp4 clip3.mp4 -j 83 --color white --skip-warmup 480
        python main.py game clip1.mp4 -j 83 --color white --identify-at 720
    """
    cfg = load_config(config)

    from src.pipeline import analyze_game
    from src.compare import SessionStore

    video_list = list(videos)
    stats = analyze_game(
        video_list, jersey, output_dir=output, config=cfg.get("analysis", {}),
        skip_warmup_seconds=skip_warmup, team_color=color, identify_at=identify_at,
    )

    if stats:
        store = SessionStore()
        store.save(stats, "game", label=label)

        if coach:
            _run_coach("game", stats, store)


@cli.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("--output", "-o", default="output", help="Output directory")
@click.option("--config", "-c", default="config.yaml", help="Config file path")
@click.option("--label", "-l", default=None, help="Session label (e.g. '2026-04-07-skills')")
@click.option("--coach/--no-coach", default=True, help="Get AI coaching feedback after analysis")
def skills(video, output, config, label, coach):
    """Analyze a skills session. Focuses on skating form and body mechanics."""
    cfg = load_config(config)

    from src.pipeline import analyze_skills
    from src.compare import SessionStore

    stats = analyze_skills(video, output_dir=output, config=cfg.get("analysis", {}))

    if stats:
        store = SessionStore()
        store.save(stats, "skills", label=label)

        if coach:
            _run_coach("skills", stats, store)


# ---------------------------------------------------------------------------
# AI Copilot commands
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("question", nargs=-1, required=True)
@click.option("--mode", "-m", type=click.Choice(["game", "skills"]), default=None,
              help="Include latest session data as context")
def ask(question, mode):
    """Ask your AI hockey coach anything.

    Examples:
        python main.py ask "How can I improve my first stride?"
        python main.py ask -m skills "Why is my knee bend so shallow?"
        python main.py ask -m game "Am I playing too much in the neutral zone?"
    """
    from src.coach import HockeyCoach
    from src.compare import SessionStore

    context = None
    if mode:
        store = SessionStore()
        current, _ = store.compare_latest(mode)
        context = current

    coach = HockeyCoach()
    response = coach.ask(" ".join(question), context_stats=context)
    click.echo(f"\n{response}\n")


@cli.command()
@click.option("--mode", "-m", type=click.Choice(["game", "skills"]), required=True)
def review(mode):
    """Get AI coaching review of your latest session vs previous."""
    from src.coach import HockeyCoach
    from src.compare import SessionStore

    store = SessionStore()
    current, previous = store.compare_latest(mode)

    if not current:
        click.echo(f"No {mode} sessions found. Run an analysis first.")
        return

    coach = HockeyCoach()
    if mode == "game":
        response = coach.review_game(current, previous)
    else:
        response = coach.review_skills(current, previous)

    click.echo(f"\n{response}\n")


@cli.command()
@click.option("--mode", "-m", type=click.Choice(["game", "skills"]), required=True)
def plan(mode):
    """Generate an improvement plan from all your saved sessions."""
    from src.coach import HockeyCoach
    from src.compare import SessionStore

    store = SessionStore()
    sessions = store.load_all(mode)

    if len(sessions) < 2:
        click.echo(f"Need at least 2 {mode} sessions for a plan. You have {len(sessions)}.")
        return

    coach = HockeyCoach()
    all_stats = [s["stats"] for s in sessions]
    response = coach.improvement_plan(all_stats)
    click.echo(f"\n{response}\n")


@cli.command()
@click.option("--mode", "-m", type=click.Choice(["game", "skills"]), default=None)
def sessions(mode):
    """List all saved analysis sessions."""
    from src.compare import SessionStore

    store = SessionStore()
    entries = store.list_sessions(mode)

    if not entries:
        click.echo("No sessions saved yet.")
        return

    click.echo(f"\n{'Mode':<10} {'Label':<30} {'Timestamp':<25}")
    click.echo("-" * 65)
    for e in entries:
        click.echo(f"{e['mode']:<10} {e['label']:<30} {e['timestamp']:<25}")
    click.echo()


@cli.command()
@click.option("--mode", "-m", type=click.Choice(["game", "skills"]), required=True)
@click.argument("metric", type=str)
def trend(mode, metric):
    """Show a metric trend across sessions.

    Examples:
        python main.py trend -m skills summary.knee_bend.mean
        python main.py trend -m game total_ice_time_min
    """
    from src.compare import SessionStore

    store = SessionStore()
    data = store.trend(mode, metric)

    if not data:
        click.echo(f"No data found for metric '{metric}' in {mode} sessions.")
        return

    click.echo(f"\nTrend: {metric}")
    click.echo("-" * 50)
    for timestamp, value in data:
        date = timestamp[:10]
        click.echo(f"  {date}  {value:.2f}")
    click.echo()


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("--output", "-o", default="output/calibration.npz", help="Save calibration to")
def calibrate(video, output):
    """Interactively calibrate rink homography from a video frame.

    Click 4+ matching points between the camera view and rink template.
    """
    import cv2
    from src.homography import RinkMapper

    cap = cv2.VideoCapture(video)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        click.echo("Could not read video frame.")
        return

    click.echo("Rink calibration — click matching points on the video frame.")
    click.echo("Standard rink reference points (in feet from bottom-left corner):")
    click.echo("  Center ice:     (100, 42.5)")
    click.echo("  Left blue line: (75, 42.5)  /  Right blue line: (125, 42.5)")
    click.echo("  Left goal line: (11, 42.5)  /  Right goal line: (189, 42.5)")
    click.echo()

    camera_pts = []

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            camera_pts.append((x, y))
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(frame, str(len(camera_pts)), (x + 10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Calibrate", frame)
            click.echo(f"  Point {len(camera_pts)}: pixel ({x}, {y})")

    cv2.imshow("Calibrate", frame)
    cv2.setMouseCallback("Calibrate", on_click)
    click.echo("Click points on the frame, then press 'q' when done.")
    while True:
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()

    if len(camera_pts) < 4:
        click.echo("Need at least 4 points. Aborting.")
        return

    click.echo(f"\nEnter rink coordinates (feet) for each of the {len(camera_pts)} points:")
    rink_pts = []
    for i, (px, py) in enumerate(camera_pts):
        coords = click.prompt(f"  Point {i+1} (pixel {px},{py}) -> rink x,y", type=str)
        x, y = [float(v.strip()) for v in coords.split(",")]
        rink_pts.append((x, y))

    mapper = RinkMapper()
    mapper.calibrate_from_points(camera_pts, rink_pts)
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    mapper.save_calibration(output)
    click.echo(f"Calibration saved to {output}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_coach(mode, stats, store):
    """Run AI coaching feedback after an analysis."""
    try:
        from src.coach import HockeyCoach

        previous_sessions = store.load_latest(mode, n=2)
        previous = previous_sessions[1]["stats"] if len(previous_sessions) > 1 else None

        coach = HockeyCoach()
        click.echo("\n--- AI Coach Feedback ---")
        if mode == "game":
            response = coach.review_game(stats, previous)
        else:
            response = coach.review_skills(stats, previous)
        click.echo(f"\n{response}\n")
    except Exception as e:
        click.echo(f"\n(AI coaching unavailable: {e})")
        click.echo("Set ANTHROPIC_API_KEY to enable coaching feedback.\n")


if __name__ == "__main__":
    cli()
