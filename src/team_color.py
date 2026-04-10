"""Team color classification — separate white vs dark jerseys."""

import cv2
import numpy as np


class TeamClassifier:
    """Classify players as white or dark team based on jersey color.

    Uses K-means clustering on HSV saturation to dynamically split players
    into two groups per frame. White jerseys cluster at low saturation,
    dark/colored jerseys cluster at high saturation.
    """

    def _get_saturation(self, frame, bbox):
        """Extract mean saturation from jersey crop region."""
        x1, y1, x2, y2 = [int(v) for v in bbox]
        h = y2 - y1
        w = x2 - x1

        top = y1 + int(h * 0.15)
        bottom = y1 + int(h * 0.50)
        left = x1 + int(w * 0.15)
        right = x2 - int(w * 0.15)

        if bottom <= top or right <= left:
            return None

        crop = frame[top:bottom, left:right]
        if crop.size == 0:
            return None

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        return float(np.mean(hsv[:, :, 1]))

    def classify_player(self, frame, bbox):
        """Classify a single player (fallback when few players detected)."""
        sat = self._get_saturation(frame, bbox)
        if sat is None:
            return "unknown", 0
        # Fallback fixed threshold when clustering isn't possible
        team = "white" if sat < 80 else "dark"
        return team, sat

    def classify_all(self, frame, tracked_players):
        """Classify all tracked players using K-means clustering.

        Dynamically finds the natural split between white and dark teams
        based on saturation values in this frame. Falls back to a fixed
        threshold if too few players are detected for clustering.

        Returns dict of track_id -> ('white' | 'dark', saturation).
        """
        # Collect saturation values
        sat_data = {}
        for player in tracked_players:
            sat = self._get_saturation(frame, player["bbox"])
            if sat is not None:
                sat_data[player["track_id"]] = sat

        if not sat_data:
            return {}

        tids = list(sat_data.keys())
        sats = np.array([sat_data[tid] for tid in tids], dtype=np.float32)

        if len(sats) < 4:
            # Too few players for reliable clustering — use fixed threshold
            results = {}
            for tid, sat in zip(tids, sats):
                team = "white" if sat < 80 else "dark"
                results[tid] = (team, float(sat))
            return results

        # K-means with k=2 on saturation values
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(
            sats.reshape(-1, 1), 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS
        )

        # The cluster with lower mean saturation is "white"
        white_label = 0 if centers[0][0] < centers[1][0] else 1

        results = {}
        for tid, sat, label in zip(tids, sats, labels.flatten()):
            team = "white" if label == white_label else "dark"
            results[tid] = (team, float(sat))
        return results

    def filter_by_team(self, frame, tracked_players, target_team):
        """Return only players matching the target team color."""
        results = self.classify_all(frame, tracked_players)
        return [p for p in tracked_players
                if results.get(p["track_id"], ("unknown",))[0] == target_team]

    def build_team_votes(self, frame, tracked_players, existing_votes=None):
        """Accumulate team color votes per track ID across frames."""
        votes = existing_votes or {}
        results = self.classify_all(frame, tracked_players)
        for tid, (team, _) in results.items():
            if team == "unknown":
                continue
            if tid not in votes:
                votes[tid] = {"white": 0, "dark": 0}
            votes[tid][team] += 1
        return votes

    def get_team_tracks(self, team_votes, target_team, min_votes=3, min_ratio=0.6):
        """Get track IDs confidently classified as the target team."""
        team_tracks = []
        for tid, votes in team_votes.items():
            total = votes["white"] + votes["dark"]
            if total < min_votes:
                continue
            ratio = votes[target_team] / total
            if ratio >= min_ratio:
                team_tracks.append(tid)
        return team_tracks
