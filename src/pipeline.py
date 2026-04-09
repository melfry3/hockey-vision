"""Main processing pipelines for game and skills analysis."""

import cv2
import json
import os
import numpy as np

from .tracker import PlayerTracker
from .jersey import JerseyReader
from .team_color import TeamClassifier
from .identify import select_player_from_frame
from .analytics import SkatingAnalytics
from .pose import PoseAnalyzer
from .visualizer import (
    draw_tracked_player,
    draw_speed_overlay,
    draw_pose_overlay,
    render_heatmap,
    render_shift_chart,
)


def _process_single_video(video_path, tracker, jersey_reader, jersey_number,
                          sample_rate, frame_offset=0, skip_seconds=0):
    """Process a single video clip, returning jersey votes and frame count.

    frame_offset: added to frame numbers so multi-clip frame counts are continuous.
    skip_seconds: skip this many seconds from the start (e.g., to skip warmup).
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_min = total_frames / fps / 60

    print(f"\n  Clip: {os.path.basename(video_path)}")
    print(f"  {width}x{height} @ {fps:.1f} fps, {duration_min:.1f} min")

    # Skip warmup if requested
    skip_frames = int(skip_seconds * fps)
    if skip_frames > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, skip_frames)
        print(f"  Skipping first {skip_seconds}s (warmup)")

    jersey_votes = {}
    frame_num = skip_frames

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % sample_rate != 0:
            frame_num += 1
            continue

        global_frame = frame_offset + frame_num
        tracked = tracker.update(frame, global_frame)

        # Try to read jersey numbers periodically
        if frame_num % (sample_rate * 10) == 0 and tracked:
            match_id = jersey_reader.identify_target(frame, tracked, jersey_number)
            if match_id is not None:
                jersey_votes[match_id] = jersey_votes.get(match_id, 0) + 1

        if frame_num % (int(fps) * 30) == 0:
            elapsed_min = frame_num / fps / 60
            print(f"    {elapsed_min:.1f} min...")

        frame_num += 1

    cap.release()
    return jersey_votes, frame_num, fps


def analyze_game(video_paths, jersey_number, output_dir="output", config=None,
                 skip_warmup_seconds=0, team_color=None):
    """Full game analysis pipeline. Supports single video or multiple clips.

    Player identification strategy:
    1. Track all players across all clips
    2. Classify each track by team color (white vs dark)
    3. Filter to your team
    4. Try jersey OCR on your team's players
    5. If OCR fails, show a frame and let you click on yourself

    video_paths: single path string or list of paths for multi-clip games.
    jersey_number: your number (e.g., 83).
    skip_warmup_seconds: seconds to skip at the start of the first clip.
    team_color: 'white' or 'dark'.
    """
    config = config or {}
    os.makedirs(output_dir, exist_ok=True)

    # Normalize to list
    if isinstance(video_paths, str):
        video_paths = [video_paths]

    sample_rate = config.get("fps_sample_rate", 5)

    print(f"=== Game Analysis ===")
    print(f"Jersey #{jersey_number}" + (f" ({team_color})" if team_color else ""))
    print(f"Clips: {len(video_paths)}")
    print(f"Sampling every {sample_rate} frames", flush=True)

    tracker = PlayerTracker()
    jersey_reader = JerseyReader()
    team_classifier = TeamClassifier()

    # Phase 1: Track across all clips, classify team colors
    print("\n--- Phase 1: Tracking players and classifying teams ---", flush=True)
    all_jersey_votes = {}
    team_votes = {}
    frame_offset = 0
    game_fps = 30
    id_frame = None       # save a good frame for manual selection
    id_frame_tracked = None
    id_frame_num = None

    for i, path in enumerate(video_paths):
        skip = skip_warmup_seconds if i == 0 else 0

        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_min = total_frames / fps / 60

        print(f"\n  Clip: {os.path.basename(path)}")
        print(f"  {width}x{height} @ {fps:.1f} fps, {duration_min:.1f} min", flush=True)

        if i == 0:
            game_fps = fps

        skip_frames = int(skip * fps)
        if skip_frames > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, skip_frames)
            print(f"  Skipping first {skip}s (warmup)", flush=True)

        frame_num = skip_frames
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_num % sample_rate != 0:
                frame_num += 1
                continue

            global_frame = frame_offset + frame_num
            tracked = tracker.update(frame, global_frame)

            # Classify team colors every 10th sampled frame
            if frame_num % (sample_rate * 10) == 0 and tracked:
                team_votes = team_classifier.build_team_votes(
                    frame, tracked, existing_votes=team_votes
                )
                # Also try jersey OCR on team-filtered players
                if team_color:
                    team_players = team_classifier.filter_by_team(
                        frame, tracked, team_color
                    )
                else:
                    team_players = tracked
                match_id = jersey_reader.identify_target(
                    frame, team_players, jersey_number
                )
                if match_id is not None:
                    all_jersey_votes[match_id] = all_jersey_votes.get(match_id, 0) + 1

            # Save a mid-game frame for manual selection fallback
            if i == 0 and id_frame is None and frame_num > skip_frames + int(fps * 30):
                if tracked and len(tracked) >= 5:
                    id_frame = frame.copy()
                    id_frame_tracked = tracked[:]
                    id_frame_num = global_frame

            if frame_num % (int(fps) * 30) == 0:
                elapsed_min = frame_num / fps / 60
                print(f"    {elapsed_min:.1f} min...", flush=True)

            frame_num += 1

        cap.release()
        frame_offset += frame_num

    # Phase 1b: Identify target player
    target_track_id = None

    # Strategy A: Jersey OCR matched
    if all_jersey_votes:
        target_track_id = max(all_jersey_votes, key=all_jersey_votes.get)
        total_votes = sum(all_jersey_votes.values())
        confidence = all_jersey_votes[target_track_id] / max(total_votes, 1)
        print(f"\nJersey OCR identified #{jersey_number} as track {target_track_id} "
              f"({all_jersey_votes[target_track_id]} detections, {confidence:.0%} confidence)",
              flush=True)
        # If very low confidence, fall through to manual
        if all_jersey_votes[target_track_id] < 3:
            print("Low confidence — falling back to manual selection.", flush=True)
            target_track_id = None

    # Strategy B: Manual click-to-identify
    if target_track_id is None and id_frame is not None:
        print(f"\nJersey OCR couldn't reliably find #{jersey_number}.", flush=True)
        print("Opening a frame for manual identification...", flush=True)

        # Get team-filtered track IDs
        team_track_ids = None
        if team_color and team_votes:
            team_track_ids = team_classifier.get_team_tracks(
                team_votes, team_color, min_votes=3, min_ratio=0.6
            )
            # Filter id_frame_tracked to only include tracks in team_track_ids
            filtered_tracked = [
                p for p in id_frame_tracked
                if p["track_id"] in team_track_ids
            ] if team_track_ids else id_frame_tracked
            print(f"Showing {len(filtered_tracked)} {team_color} team players "
                  f"(green boxes). Click on yourself.", flush=True)
        else:
            filtered_tracked = id_frame_tracked
            team_track_ids = None

        target_track_id = select_player_from_frame(
            id_frame, filtered_tracked,
            team_filter=team_track_ids,
            title=f"Click on yourself (#{jersey_number} {team_color or ''})"
        )

        if target_track_id is not None:
            print(f"Selected track {target_track_id}", flush=True)
        else:
            print("No player selected.", flush=True)

    # Phase 2: Compute analytics for target player
    print("\n--- Phase 2: Computing analytics ---")
    analytics = SkatingAnalytics(fps=game_fps, sample_rate=sample_rate)

    if target_track_id:
        positions = tracker.get_track(target_track_id)
        shifts = analytics.shift_summary(positions)
        total_distance = analytics.compute_distance(positions)
        ice_time = analytics.compute_ice_time(positions)
        heatmap = analytics.compute_heatmap(positions)
        speeds = analytics.compute_speed(positions)
        avg_speed = np.mean([s for _, s in speeds]) if speeds else 0.0
        max_speed = max([s for _, s in speeds]) if speeds else 0.0

        stats = {
            "jersey_number": jersey_number,
            "team_color": team_color,
            "track_id": target_track_id,
            "clips": [os.path.basename(p) for p in video_paths],
            "total_ice_time_sec": round(ice_time, 1),
            "total_ice_time_min": round(ice_time / 60, 1),
            "total_distance_px": round(total_distance, 1),
            "avg_speed_px_sec": round(avg_speed, 1),
            "max_speed_px_sec": round(max_speed, 1),
            "num_shifts": len(shifts),
            "avg_shift_duration_sec": round(
                np.mean([s["duration_sec"] for s in shifts]), 1
            ) if shifts else 0,
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
        print(f"  Avg shift: {stats['avg_shift_duration_sec']}s")
        print(f"  Avg speed: {stats['avg_speed_px_sec']:.0f} px/s")
        print(f"  Max speed: {stats['max_speed_px_sec']:.0f} px/s")
        for s in shifts:
            print(f"    Shift {s['shift_number']}: {s['duration_sec']}s")

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
