"""Team color classification — separate white vs dark jerseys."""

import cv2
import numpy as np


class TeamClassifier:
    """Classify players as white or dark team based on jersey color."""

    def __init__(self, brightness_threshold=160):
        self.brightness_threshold = brightness_threshold

    def classify_player(self, frame, bbox):
        """Classify a single player as 'white' or 'dark'.

        Samples the upper torso region where the jersey is visible.
        Returns ('white' | 'dark', mean_brightness).
        """
        x1, y1, x2, y2 = [int(v) for v in bbox]
        h = y2 - y1
        w = x2 - x1

        # Crop to upper torso (jersey area, skip head and legs)
        top = y1 + int(h * 0.15)
        bottom = y1 + int(h * 0.50)
        left = x1 + int(w * 0.15)
        right = x2 - int(w * 0.15)

        if bottom <= top or right <= left:
            return "unknown", 0

        crop = frame[top:bottom, left:right]
        if crop.size == 0:
            return "unknown", 0

        # Convert to grayscale and get mean brightness
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(np.mean(gray))

        team = "white" if mean_brightness > self.brightness_threshold else "dark"
        return team, mean_brightness

    def classify_all(self, frame, tracked_players):
        """Classify all tracked players in a frame.

        Returns dict of track_id -> ('white' | 'dark', brightness).
        """
        results = {}
        for player in tracked_players:
            team, brightness = self.classify_player(frame, player["bbox"])
            results[player["track_id"]] = (team, brightness)
        return results

    def filter_by_team(self, frame, tracked_players, target_team):
        """Return only players matching the target team color."""
        matching = []
        for player in tracked_players:
            team, _ = self.classify_player(frame, player["bbox"])
            if team == target_team:
                matching.append(player)
        return matching

    def build_team_votes(self, frame, tracked_players, existing_votes=None):
        """Accumulate team color votes per track ID across frames.

        Returns updated votes dict: track_id -> {'white': N, 'dark': N}.
        """
        votes = existing_votes or {}
        for player in tracked_players:
            tid = player["track_id"]
            team, brightness = self.classify_player(frame, player["bbox"])
            if team == "unknown":
                continue
            if tid not in votes:
                votes[tid] = {"white": 0, "dark": 0}
            votes[tid][team] += 1
        return votes

    def get_team_tracks(self, team_votes, target_team, min_votes=3, min_ratio=0.6):
        """Get track IDs that are confidently classified as the target team.

        min_votes: minimum number of classification samples.
        min_ratio: minimum fraction of votes for the target team.
        """
        team_tracks = []
        for tid, votes in team_votes.items():
            total = votes["white"] + votes["dark"]
            if total < min_votes:
                continue
            ratio = votes[target_team] / total
            if ratio >= min_ratio:
                team_tracks.append(tid)
        return team_tracks
