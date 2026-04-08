"""Main processing pipelines for game and skills analysis."""

import cv2
import json
import os
import numpy as np

from .tracker import PlayerTracker
from .jersey import JerseyReader
from .analytics import SkatingAnalytics
from .pose import PoseAnalyzer
from .visualizer import (
    draw_tracked_player,
    draw_speed_overlay,
    draw_pose_overlay,
    render_heatmap,
    render_shift_chart,
)


def analyze_game(video_path, jersey_number, output_dir="output", config=None):
    """Full game analysis pipeline.

    1. Track all players
    2. Identify target player by jersey number
    3. Compute skating analytics
    4. Generate output (annotated video, heatmap, stats)
    """
    config = config or {}
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_rate = config.get("fps_sample_rate", 5)

    print(f"Video: {width}x{height} @ {fps:.1f} fps, {total_frames} frames")
    print(f"Looking for jersey #{jersey_number}")
    print(f"Sampling every {sample_rate} frames")

    tracker = PlayerTracker()
    jersey_reader = JerseyReader()
    analytics = SkatingAnalytics(fps=fps, sample_rate=sample_rate)

    # Phase 1: Track all players and identify target
    target_track_id = None
    jersey_votes = {}  # track_id -> count of times identified as target
    frame_num = 0

    print("\n--- Phase 1: Tracking players and identifying jersey ---")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % sample_rate != 0:
            frame_num += 1
            continue

        tracked = tracker.update(frame, frame_num)

        # Try to read jersey numbers periodically
        if frame_num % (sample_rate * 10) == 0 and tracked:
            match_id = jersey_reader.identify_target(frame, tracked, jersey_number)
            if match_id is not None:
                jersey_votes[match_id] = jersey_votes.get(match_id, 0) + 1

        if frame_num % (int(fps) * 30) == 0:
            elapsed_min = frame_num / fps / 60
            print(f"  Processed {elapsed_min:.1f} min...")

        frame_num += 1

    # Pick the track most often identified as target jersey
    if jersey_votes:
        target_track_id = max(jersey_votes, key=jersey_votes.get)
        confidence = jersey_votes[target_track_id] / max(sum(jersey_votes.values()), 1)
        print(f"\nIdentified jersey #{jersey_number} as track {target_track_id} "
              f"({jersey_votes[target_track_id]} detections, {confidence:.0%} confidence)")
    else:
        print(f"\nCould not identify jersey #{jersey_number} — showing all tracks")

    # Phase 2: Compute analytics for target player
    print("\n--- Phase 2: Computing analytics ---")
    if target_track_id:
        positions = tracker.get_track(target_track_id)
        shifts = analytics.shift_summary(positions)
        total_distance = analytics.compute_distance(positions)
        ice_time = analytics.compute_ice_time(positions)
        heatmap = analytics.compute_heatmap(positions)

        stats = {
            "jersey_number": jersey_number,
            "track_id": target_track_id,
            "total_ice_time_sec": round(ice_time, 1),
            "total_ice_time_min": round(ice_time / 60, 1),
            "total_distance_px": round(total_distance, 1),
            "num_shifts": len(shifts),
            "shifts": shifts,
        }

        # Save outputs
        stats_path = os.path.join(output_dir, "game_stats.json")
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"  Saved stats: {stats_path}")

        heatmap_path = os.path.join(output_dir, "heatmap.png")
        render_heatmap(heatmap, heatmap_path, f"#{jersey_number} Position Heatmap")
        print(f"  Saved heatmap: {heatmap_path}")

        if shifts:
            shifts_path = os.path.join(output_dir, "shifts.png")
            render_shift_chart(shifts, shifts_path)
            print(f"  Saved shift chart: {shifts_path}")

        print(f"\n--- Results for #{jersey_number} ---")
        print(f"  Ice time: {stats['total_ice_time_min']} min")
        print(f"  Shifts: {stats['num_shifts']}")
        for s in shifts:
            print(f"    Shift {s['shift_number']}: {s['duration_sec']}s")

    cap.release()
    print("\nDone.")
    return stats if target_track_id else None


def analyze_skills(video_path, output_dir="output", config=None):
    """Skills session analysis pipeline.

    Focuses on pose estimation and form metrics rather than player identification.
    Useful for skills classes where you're the primary subject.

    1. Run pose estimation on each frame
    2. Compute form metrics (knee bend, forward lean, stride width)
    3. Generate summary and annotated video
    """
    config = config or {}
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_rate = config.get("fps_sample_rate", 5)

    print(f"Video: {width}x{height} @ {fps:.1f} fps, {total_frames} frames")
    print(f"Skills analysis mode — pose estimation")

    pose_analyzer = PoseAnalyzer()

    # Set up output video
    out_path = os.path.join(output_dir, "skills_annotated.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video = cv2.VideoWriter(out_path, fourcc, fps / sample_rate, (width, height))

    frame_num = 0
    print("\n--- Analyzing poses ---")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % sample_rate != 0:
            frame_num += 1
            continue

        poses = pose_analyzer.analyze_frame(frame, frame_num)

        # Draw pose overlays on frame
        annotated = frame.copy()
        for pose in poses:
            annotated = draw_pose_overlay(
                annotated, pose["keypoints"], pose["keypoint_conf"]
            )

            # Add form metrics as text overlay
            knee = pose_analyzer.compute_knee_bend(pose["keypoints"], pose["keypoint_conf"])
            lean = pose_analyzer.compute_forward_lean(pose["keypoints"], pose["keypoint_conf"])
            y_offset = 30
            if knee:
                for side, angle in knee.items():
                    text = f"{side} knee: {angle:.0f} deg"
                    cv2.putText(annotated, text, (10, y_offset),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    y_offset += 25
            if lean is not None:
                text = f"lean: {lean:.0f} deg"
                cv2.putText(annotated, text, (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        out_video.write(annotated)

        if frame_num % (int(fps) * 30) == 0:
            elapsed_min = frame_num / fps / 60
            print(f"  Processed {elapsed_min:.1f} min...")

        frame_num += 1

    out_video.release()
    cap.release()

    # Generate summary
    summary = pose_analyzer.summarize_session()
    stats = {"mode": "skills", "summary": summary}

    stats_path = os.path.join(output_dir, "skills_stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n--- Skills Session Summary ---")
    if "knee_bend" in summary:
        kb = summary["knee_bend"]
        print(f"  Knee bend: avg {kb['mean']:.0f} deg (range {kb['min']:.0f}-{kb['max']:.0f})")
        if kb["mean"] > 140:
            print(f"    -> Too upright! Aim for 90-120 degrees for better power.")
        elif kb["mean"] < 90:
            print(f"    -> Very deep bend — great for explosiveness.")
    if "forward_lean" in summary:
        fl = summary["forward_lean"]
        print(f"  Forward lean: avg {fl['mean']:.0f} deg (range {fl['min']:.0f}-{fl['max']:.0f})")
        if fl["mean"] < 15:
            print(f"    -> Too upright. Lean forward more for speed and balance.")

    print(f"\n  Annotated video: {out_path}")
    print(f"  Stats: {stats_path}")
    print("Done.")
    return stats
