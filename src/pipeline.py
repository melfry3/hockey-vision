"""Main processing pipelines for game and skills analysis."""

import cv2
import json
import os
import numpy as np

from .tracker import PlayerTracker
from .jersey import JerseyReader
from .team_color import TeamClassifier
from .identify import browse_and_select
from .analytics import SkatingAnalytics
from .pose import PoseAnalyzer
from .visualizer import (
    draw_tracked_player,
    draw_speed_overlay,
    draw_pose_overlay,
    render_heatmap,
    render_shift_chart,
)


def analyze_game(video_paths, jersey_number, output_dir="output", config=None,
                 skip_warmup_seconds=0, team_color=None, identify_at=None):
    """Full game analysis pipeline. Supports single video or multiple clips.

    Player identification:
    1. Open video browser at identify_at time (or warmup+60s)
    2. User clicks on themselves (team color highlights white vs dark)
    3. Run full tracking pass, following the selected player by appearance
       proximity to the initial selection

    video_paths: single path string or list of paths.
    jersey_number: your number.
    skip_warmup_seconds: seconds to skip at the start of the first clip.
    team_color: 'white' or 'dark'.
    identify_at: seconds into first clip to show identification frame.
    """
    config = config or {}
    os.makedirs(output_dir, exist_ok=True)

    if isinstance(video_paths, str):
        video_paths = [video_paths]

    sample_rate = config.get("fps_sample_rate", 5)

    print(f"=== Game Analysis ===", flush=True)
    print(f"Jersey #{jersey_number}" + (f" ({team_color})" if team_color else ""), flush=True)
    print(f"Clips: {len(video_paths)}", flush=True)
    print(f"Sampling every {sample_rate} frames", flush=True)

    team_classifier = TeamClassifier()

    # ---------------------------------------------------------------
    # Phase 0: Identify yourself
    # ---------------------------------------------------------------
    browse_start = identify_at if identify_at else skip_warmup_seconds + 60
    print(f"\n--- Phase 0: Identify yourself ---", flush=True)
    print(f"Opening video at {browse_start}s — navigate to a frame where "
          "you're on the ice, then click on yourself.", flush=True)
    print("  Right/d: +5s | Left/a: -5s | Space: +30s | b: -30s | q: cancel",
          flush=True)

    id_tracker = PlayerTracker()
    selected_track, selected_frame = browse_and_select(
        video_paths[0], id_tracker,
        team_classifier=team_classifier,
        target_team=team_color,
        start_seconds=browse_start,
    )

    if selected_track is None:
        print("No player selected. Cannot continue.", flush=True)
        return None

    # Get the selected player's position to match in the full pass
    selected_positions = id_tracker.get_track(selected_track)
    if not selected_positions:
        print("Could not get position for selected player.", flush=True)
        return None

    # Use the last known position as the anchor point
    _, _, anchor_center = selected_positions[-1]
    anchor_frame = selected_positions[-1][0]
    print(f"Anchor: track {selected_track} at frame {anchor_frame}, "
          f"position ({anchor_center[0]:.0f}, {anchor_center[1]:.0f})", flush=True)

    # ---------------------------------------------------------------
    # Phase 1: Full tracking pass with re-identification
    # ---------------------------------------------------------------
    print(f"\n--- Phase 1: Tracking all players ---", flush=True)
    print(f"Will re-identify you when track is lost.", flush=True)
    tracker = PlayerTracker()
    team_classifier = TeamClassifier()
    frame_offset = 0
    game_fps = 30

    # Track re-identification state
    current_track_id = None
    last_known_center = anchor_center
    all_my_positions = []  # unified position list across track ID changes
    frames_since_seen = 0
    max_reacquire_dist = 150  # max pixels to match when reacquiring
    lost_threshold = int(10 * 30 / sample_rate)  # ~10 sec of frames before giving up

    for i, path in enumerate(video_paths):
        skip = skip_warmup_seconds if i == 0 else 0

        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_min = total_frames / fps / 60

        print(f"\n  Clip: {os.path.basename(path)}", flush=True)
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

            if tracked:
                # Check if our current track is still alive
                current_player = None
                if current_track_id is not None:
                    for p in tracked:
                        if p["track_id"] == current_track_id:
                            current_player = p
                            break

                if current_player is not None:
                    # Still tracking — record position
                    last_known_center = current_player["center"]
                    all_my_positions.append((
                        global_frame,
                        current_player["bbox"],
                        current_player["center"],
                    ))
                    frames_since_seen = 0
                else:
                    # Lost track — try to reacquire by proximity
                    frames_since_seen += 1

                    if frames_since_seen <= lost_threshold:
                        # Filter to team color if available
                        if team_color:
                            candidates = team_classifier.filter_by_team(
                                frame, tracked, team_color
                            )
                        else:
                            candidates = tracked

                        best_tid = None
                        best_dist = float("inf")
                        for p in candidates:
                            cx, cy = p["center"]
                            dist = np.sqrt(
                                (cx - last_known_center[0]) ** 2 +
                                (cy - last_known_center[1]) ** 2
                            )
                            if dist < best_dist:
                                best_dist = dist
                                best_tid = p["track_id"]
                                best_center = p["center"]
                                best_bbox = p["bbox"]

                        if best_tid is not None and best_dist < max_reacquire_dist:
                            current_track_id = best_tid
                            last_known_center = best_center
                            all_my_positions.append((
                                global_frame, best_bbox, best_center,
                            ))
                            frames_since_seen = 0

                # Initial acquisition at the anchor frame
                if current_track_id is None and frames_since_seen == 0:
                    anchor_frame_in_clip = anchor_frame
                    if abs(global_frame - anchor_frame_in_clip) < sample_rate * 3:
                        best_tid = None
                        best_dist = float("inf")
                        for p in tracked:
                            cx, cy = p["center"]
                            dist = np.sqrt(
                                (cx - anchor_center[0]) ** 2 +
                                (cy - anchor_center[1]) ** 2
                            )
                            if dist < best_dist:
                                best_dist = dist
                                best_tid = p["track_id"]
                        if best_tid is not None and best_dist < 100:
                            current_track_id = best_tid
                            print(f"  Acquired track {current_track_id} "
                                  f"(distance: {best_dist:.0f}px)", flush=True)

            if frame_num % (int(fps) * 30) == 0:
                elapsed_min = frame_num / fps / 60
                print(f"    {elapsed_min:.1f} min... "
                      f"(tracking: {'YES' if frames_since_seen == 0 else f'lost {frames_since_seen}'})",
                      flush=True)

            frame_num += 1

        cap.release()
        frame_offset += frame_num

    if not all_my_positions:
        print("Could not track you in any frames.", flush=True)
        return None

    print(f"\nTracked you across {len(all_my_positions)} frames.", flush=True)

    # ---------------------------------------------------------------
    # Phase 2: Compute analytics
    # ---------------------------------------------------------------
    print(f"\n--- Phase 2: Computing analytics ---", flush=True)
    analytics = SkatingAnalytics(fps=game_fps, sample_rate=sample_rate)

    positions = all_my_positions
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
        "track_id": current_track_id,
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
    print(f"  Saved stats: {stats_path}", flush=True)

    heatmap_path = os.path.join(output_dir, "heatmap.png")
    render_heatmap(heatmap, heatmap_path, f"#{jersey_number} Position Heatmap")
    print(f"  Saved heatmap: {heatmap_path}", flush=True)

    if shifts:
        shifts_path = os.path.join(output_dir, "shifts.png")
        render_shift_chart(shifts, shifts_path)
        print(f"  Saved shift chart: {shifts_path}", flush=True)

    print(f"\n--- Results for #{jersey_number} ---", flush=True)
    print(f"  Ice time: {stats['total_ice_time_min']} min", flush=True)
    print(f"  Shifts: {stats['num_shifts']}", flush=True)
    print(f"  Avg shift: {stats['avg_shift_duration_sec']}s", flush=True)
    print(f"  Avg speed: {stats['avg_speed_px_sec']:.0f} px/s", flush=True)
    print(f"  Max speed: {stats['max_speed_px_sec']:.0f} px/s", flush=True)
    for s in shifts:
        print(f"    Shift {s['shift_number']}: {s['duration_sec']}s", flush=True)

    print("\nDone.", flush=True)
    return stats


def analyze_skills(video_path, output_dir="output", config=None):
    """Skills session analysis pipeline.

    Focuses on pose estimation and form metrics rather than player identification.
    Useful for skills classes where you're the primary subject.
    """
    config = config or {}
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_rate = config.get("fps_sample_rate", 5)

    print(f"Video: {width}x{height} @ {fps:.1f} fps, {total_frames} frames", flush=True)
    print(f"Skills analysis mode — pose estimation", flush=True)

    pose_analyzer = PoseAnalyzer()

    out_path = os.path.join(output_dir, "skills_annotated.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video = cv2.VideoWriter(out_path, fourcc, fps / sample_rate, (width, height))

    frame_num = 0
    print("\n--- Analyzing poses ---", flush=True)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % sample_rate != 0:
            frame_num += 1
            continue

        poses = pose_analyzer.analyze_frame(frame, frame_num)

        annotated = frame.copy()
        for pose in poses:
            annotated = draw_pose_overlay(
                annotated, pose["keypoints"], pose["keypoint_conf"]
            )

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
            print(f"  Processed {elapsed_min:.1f} min...", flush=True)

        frame_num += 1

    out_video.release()
    cap.release()

    summary = pose_analyzer.summarize_session()
    stats = {"mode": "skills", "summary": summary}

    stats_path = os.path.join(output_dir, "skills_stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n--- Skills Session Summary ---", flush=True)
    if "knee_bend" in summary:
        kb = summary["knee_bend"]
        print(f"  Knee bend: avg {kb['mean']:.0f} deg (range {kb['min']:.0f}-{kb['max']:.0f})", flush=True)
        if kb["mean"] > 140:
            print(f"    -> Too upright! Aim for 90-120 degrees for better power.", flush=True)
        elif kb["mean"] < 90:
            print(f"    -> Very deep bend — great for explosiveness.", flush=True)
    if "forward_lean" in summary:
        fl = summary["forward_lean"]
        print(f"  Forward lean: avg {fl['mean']:.0f} deg (range {fl['min']:.0f}-{fl['max']:.0f})", flush=True)
        if fl["mean"] < 15:
            print(f"    -> Too upright. Lean forward more for speed and balance.", flush=True)

    print(f"\n  Annotated video: {out_path}", flush=True)
    print(f"  Stats: {stats_path}", flush=True)
    print("Done.", flush=True)
    return stats
