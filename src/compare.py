"""Session comparison — track improvement over time."""

import json
import os
import glob
from datetime import datetime


SESSIONS_DIR = "sessions"


class SessionStore:
    """Stores and retrieves analysis results for comparison across sessions."""

    def __init__(self, base_dir=SESSIONS_DIR):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save(self, stats, mode, label=None):
        """Save a session result.

        mode: 'game' or 'skills'
        label: optional label like '2026-04-07-skills-class'
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label = label or timestamp
        filename = f"{mode}_{label}.json"
        path = os.path.join(self.base_dir, filename)

        record = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "label": label,
            "stats": stats,
        }

        with open(path, "w") as f:
            json.dump(record, f, indent=2)

        print(f"Session saved: {path}")
        return path

    def load_latest(self, mode, n=1):
        """Load the N most recent sessions of a given mode."""
        pattern = os.path.join(self.base_dir, f"{mode}_*.json")
        files = sorted(glob.glob(pattern), reverse=True)
        sessions = []
        for path in files[:n]:
            with open(path) as f:
                sessions.append(json.load(f))
        return sessions

    def load_all(self, mode):
        """Load all sessions of a given mode, oldest first."""
        pattern = os.path.join(self.base_dir, f"{mode}_*.json")
        files = sorted(glob.glob(pattern))
        sessions = []
        for path in files:
            with open(path) as f:
                sessions.append(json.load(f))
        return sessions

    def compare_latest(self, mode):
        """Compare the two most recent sessions of a given mode.

        Returns (current, previous) or (current, None) if only one session exists.
        """
        sessions = self.load_latest(mode, n=2)
        if len(sessions) == 0:
            return None, None
        elif len(sessions) == 1:
            return sessions[0]["stats"], None
        else:
            return sessions[0]["stats"], sessions[1]["stats"]

    def trend(self, mode, metric_path):
        """Extract a single metric across all sessions for trend analysis.

        metric_path: dot-separated path like 'summary.knee_bend.mean'
        Returns list of (timestamp, value) tuples.
        """
        sessions = self.load_all(mode)
        trend_data = []
        for session in sessions:
            value = session["stats"]
            for key in metric_path.split("."):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    value = None
                    break
            if value is not None:
                trend_data.append((session["timestamp"], value))
        return trend_data

    def list_sessions(self, mode=None):
        """List all saved sessions."""
        if mode:
            pattern = os.path.join(self.base_dir, f"{mode}_*.json")
        else:
            pattern = os.path.join(self.base_dir, "*.json")

        files = sorted(glob.glob(pattern))
        entries = []
        for path in files:
            with open(path) as f:
                data = json.load(f)
            entries.append({
                "file": os.path.basename(path),
                "mode": data.get("mode"),
                "label": data.get("label"),
                "timestamp": data.get("timestamp"),
            })
        return entries
