"""Hockey Vision CLI — analyze your hockey game and skills footage."""

import click
import yaml
import os


@click.group()
def cli():
    """Hockey Vision — ice hockey video analysis."""
    pass


@cli.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("--jersey", "-j", type=int, required=True, help="Your jersey number")
@click.option("--output", "-o", default="output", help="Output directory")
@click.option("--config", "-c", default="config.yaml", help="Config file path")
def game(video, jersey, output, config):
    """Analyze a game video. Tracks you by jersey number and generates stats."""
    cfg = {}
    if os.path.exists(config):
        with open(config) as f:
            cfg = yaml.safe_load(f) or {}

    from src.pipeline import analyze_game
    analyze_game(video, jersey, output_dir=output, config=cfg.get("analysis", {}))


@cli.command()
@click.argument("video", type=click.Path(exists=True))
@click.option("--output", "-o", default="output", help="Output directory")
@click.option("--config", "-c", default="config.yaml", help="Config file path")
def skills(video, output, config):
    """Analyze a skills session. Focuses on skating form and body mechanics."""
    cfg = {}
    if os.path.exists(config):
        with open(config) as f:
            cfg = yaml.safe_load(f) or {}

    from src.pipeline import analyze_skills
    analyze_skills(video, output_dir=output, config=cfg.get("analysis", {}))


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


if __name__ == "__main__":
    cli()
