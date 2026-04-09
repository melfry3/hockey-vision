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
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(display, f"T{tid}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        elif team_filter:
            cv2.rectangle(display, (x1, y1), (x2, y2), (100, 100, 100), 1)
        else:
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 200, 200), 2)
            cv2.putText(display, f"T{tid}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 200), 1)

    cv2.putText(display, f"{title} | 'q'=cancel | click any player", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    selected_id = [None]

    def on_click(event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        # Find which player bbox contains the click — match ANY player, not just filtered
        best_tid = None
        best_area = float("inf")
        for player in tracked_players:
            bx1, by1, bx2, by2 = [int(v) for v in player["bbox"]]
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                area = (bx2 - bx1) * (by2 - by1)
                if area < best_area:
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


def browse_and_select(video_path, tracker, team_classifier=None, target_team=None,
                      start_seconds=0):
    """Browse video frames with arrow keys to find yourself, then click.

    Controls:
        Right arrow / 'd': jump forward 5 seconds
        Left arrow / 'a': jump back 5 seconds
        Space: jump forward 30 seconds
        'b': jump back 30 seconds
        Click: select a player
        'q': cancel

    Returns (track_id, frame_number) or (None, None).
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps

    current_sec = start_seconds
    selected_id = [None]
    window_name = "Browse: arrow keys to navigate, click to select, 'q' to cancel"

    def on_click(event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        tracked = param.get("tracked", [])
        best_tid = None
        best_area = float("inf")
        for player in tracked:
            bx1, by1, bx2, by2 = [int(v) for v in player["bbox"]]
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                area = (bx2 - bx1) * (by2 - by1)
                if area < best_area:
                    best_area = area
                    best_tid = player["track_id"]
        if best_tid is not None:
            selected_id[0] = best_tid

    click_state = {"tracked": []}

    while True:
        # Seek to current time
        current_sec = max(0, min(current_sec, duration_sec - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(current_sec * fps))
        ret, frame = cap.read()
        if not ret:
            break

        frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

        # Detect players in this frame
        tracked = tracker.update(frame, frame_num)
        click_state["tracked"] = tracked

        # Classify teams if available
        team_track_ids = None
        if team_classifier and target_team and tracked:
            team_results = team_classifier.classify_all(frame, tracked)
            team_track_ids = [
                tid for tid, (team, _) in team_results.items()
                if team == target_team
            ]

        # Draw frame
        display = frame.copy()
        for player in tracked:
            tid = player["track_id"]
            x1, y1, x2, y2 = [int(v) for v in player["bbox"]]
            if team_track_ids and tid in team_track_ids:
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            else:
                cv2.rectangle(display, (x1, y1), (x2, y2), (100, 100, 100), 1)

        time_str = f"{int(current_sec // 60)}:{int(current_sec % 60):02d}"
        players_str = f"{len(team_track_ids or [])} {target_team}" if team_track_ids else f"{len(tracked)} total"
        cv2.putText(display, f"Time: {time_str} | Players: {players_str} | arrows=nav, click=select, q=cancel",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow(window_name, display)
        cv2.setMouseCallback(window_name, on_click, click_state)

        key = cv2.waitKey(0) & 0xFF

        if selected_id[0] is not None:
            break
        if key == ord("q"):
            break
        elif key == ord("d") or key == 83:  # right arrow
            current_sec += 5
        elif key == ord("a") or key == 81:  # left arrow
            current_sec -= 5
        elif key == ord(" "):  # space = jump 30s
            current_sec += 30
        elif key == ord("b"):  # b = back 30s
            current_sec -= 30

    cv2.destroyAllWindows()
    cap.release()

    if selected_id[0] is not None:
        print(f"Selected track {selected_id[0]} at {time_str}", flush=True)
    else:
        print("No player selected.", flush=True)

    return selected_id[0], frame_num if selected_id[0] else None
