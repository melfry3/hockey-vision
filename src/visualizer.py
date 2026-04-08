"""Draw overlays, heatmaps, and annotated output."""

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def draw_tracked_player(frame, bbox, track_id, is_target=False, label=None):
    """Draw bounding box and label on a frame."""
    x1, y1, x2, y2 = [int(v) for v in bbox]
    color = (0, 255, 0) if is_target else (200, 200, 200)
    thickness = 3 if is_target else 1

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    text = label or f"ID:{track_id}"
    cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return frame


def draw_speed_overlay(frame, speed, position):
    """Draw speed readout near a player."""
    x, y = int(position[0]), int(position[1])
    text = f"{speed:.0f} px/s"
    cv2.putText(frame, text, (x, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    return frame


def draw_pose_overlay(frame, keypoints, confs, min_conf=0.3):
    """Draw skeleton overlay from pose keypoints."""
    connections = [
        (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # arms
        (5, 11), (6, 12), (11, 12),                  # torso
        (11, 13), (13, 15), (12, 14), (14, 16),      # legs
    ]

    for i, (x, y) in enumerate(keypoints):
        if confs[i] > min_conf:
            cv2.circle(frame, (int(x), int(y)), 4, (0, 255, 0), -1)

    for i, j in connections:
        if confs[i] > min_conf and confs[j] > min_conf:
            p1 = (int(keypoints[i][0]), int(keypoints[i][1]))
            p2 = (int(keypoints[j][0]), int(keypoints[j][1]))
            cv2.line(frame, p1, p2, (0, 200, 200), 2)

    return frame


def render_heatmap(heatmap, output_path, title="Position Heatmap"):
    """Save a heatmap as an image."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    im = ax.imshow(heatmap, cmap="hot", interpolation="gaussian", aspect="auto")
    ax.set_title(title)
    ax.set_xlabel("Rink Length")
    ax.set_ylabel("Rink Width")
    plt.colorbar(im, ax=ax, label="Time Spent")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def render_shift_chart(shift_summaries, output_path):
    """Save a bar chart of shift durations."""
    shifts = [s["shift_number"] for s in shift_summaries]
    durations = [s["duration_sec"] for s in shift_summaries]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(shifts, durations, color="#1e88e5")
    ax.set_xlabel("Shift #")
    ax.set_ylabel("Duration (sec)")
    ax.set_title("Shift Durations")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
