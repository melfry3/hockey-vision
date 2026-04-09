"""Manual player identification — click to select yourself in a frame."""

import cv2
import numpy as np


def select_player_from_frame(frame, tracked_players, team_filter=None, title="Click on yourself"):
    """Show a frame with bounding boxes and let the user click to select a player.

    tracked_players: list of dicts with 'track_id', 'bbox', 'center'.
    team_filter: optional list of track_ids to highlight (e.g., white team only).

    Returns the selected track_id, or None if cancelled.
    """
    display = frame.copy()

    # Draw all tracked players
    for player in tracked_players:
        tid = player["track_id"]
        x1, y1, x2, y2 = [int(v) for v in player["bbox"]]

        if team_filter and tid in team_filter:
            # Highlight team-filtered players in green
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(display, f"T{tid}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        elif team_filter:
            # Dim non-matching players
            cv2.rectangle(display, (x1, y1), (x2, y2), (100, 100, 100), 1)
        else:
            # No filter — show all equally
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 200, 200), 2)
            cv2.putText(display, f"T{tid}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 200), 1)

    # Instructions
    cv2.putText(display, f"{title} - press 'q' to cancel", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    selected_id = [None]  # mutable container for closure

    def on_click(event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        # Find which player bbox contains the click
        best_tid = None
        best_area = float("inf")
        for player in tracked_players:
            if team_filter and player["track_id"] not in team_filter:
                continue
            bx1, by1, bx2, by2 = [int(v) for v in player["bbox"]]
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                area = (bx2 - bx1) * (by2 - by1)
                if area < best_area:  # pick smallest containing box
                    best_area = area
                    best_tid = player["track_id"]
        if best_tid is not None:
            selected_id[0] = best_tid

    cv2.imshow(title, display)
    cv2.setMouseCallback(title, on_click)

    while True:
        key = cv2.waitKey(100) & 0xFF
        if selected_id[0] is not None:
            break
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    return selected_id[0]


def select_player_from_video(video_path, tracker, team_classifier=None,
                             target_team=None, seek_seconds=0):
    """Open a video, seek to a frame, run detection, and let user click to identify.

    Returns (track_id, frame_number) or (None, None).
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    # Seek to the requested time
    if seek_seconds > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(seek_seconds * fps))

    ret, frame = cap.read()
    if not ret:
        print("Could not read video frame.")
        cap.release()
        return None, None

    frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

    # Run tracking on this frame
    tracked = tracker.update(frame, frame_num)

    if not tracked:
        print("No players detected in this frame. Try a different time.")
        cap.release()
        return None, None

    # Build team filter if requested
    team_track_ids = None
    if team_classifier and target_team:
        team_results = team_classifier.classify_all(frame, tracked)
        team_track_ids = [
            tid for tid, (team, _) in team_results.items()
            if team == target_team
        ]
        print(f"Found {len(team_track_ids)} {target_team} team players "
              f"out of {len(tracked)} total")

    title = f"Click on yourself (#{target_team} team highlighted)" if target_team else "Click on yourself"
    selected = select_player_from_frame(frame, tracked, team_filter=team_track_ids, title=title)

    cap.release()

    if selected is not None:
        print(f"Selected track ID: {selected}")
    else:
        print("No player selected.")

    return selected, frame_num
