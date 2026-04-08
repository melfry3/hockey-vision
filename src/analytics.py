"""Compute skating analytics from tracking data."""

import numpy as np
from collections import defaultdict


class SkatingAnalytics:
    """Compute stats from tracked player positions."""

    def __init__(self, fps=30, sample_rate=5):
        self.fps = fps
        self.sample_rate = sample_rate
        self.effective_fps = fps / sample_rate

    def compute_speed(self, positions, smoothing_window=5):
        """Estimate speed from a sequence of (frame_num, bbox, center) tuples.

        Returns list of (frame_num, speed_pixels_per_second).
        Speed is in pixels/sec — use homography to convert to feet/sec.
        """
        if len(positions) < 2:
            return []

        speeds = []
        for i in range(1, len(positions)):
            f0, _, c0 = positions[i - 1]
            f1, _, c1 = positions[i]
            dt = (f1 - f0) / self.fps
            if dt <= 0:
                continue
            dist = np.sqrt((c1[0] - c0[0]) ** 2 + (c1[1] - c0[1]) ** 2)
            speed = dist / dt
            speeds.append((f1, speed))

        # Smooth
        if smoothing_window > 1 and len(speeds) >= smoothing_window:
            raw_speeds = [s for _, s in speeds]
            kernel = np.ones(smoothing_window) / smoothing_window
            smoothed = np.convolve(raw_speeds, kernel, mode="same")
            speeds = [(speeds[i][0], float(smoothed[i])) for i in range(len(speeds))]

        return speeds

    def compute_distance(self, positions):
        """Total distance traveled in pixels."""
        total = 0.0
        for i in range(1, len(positions)):
            _, _, c0 = positions[i - 1]
            _, _, c1 = positions[i]
            total += np.sqrt((c1[0] - c0[0]) ** 2 + (c1[1] - c0[1]) ** 2)
        return total

    def compute_ice_time(self, positions):
        """Estimate total ice time from tracked frames."""
        if len(positions) < 2:
            return 0.0
        first_frame = positions[0][0]
        last_frame = positions[-1][0]
        return (last_frame - first_frame) / self.fps

    def compute_heatmap(self, positions, rink_mapper=None, resolution=100):
        """Generate a position heatmap.

        If rink_mapper is provided, maps to rink coordinates.
        Returns 2D numpy array of position density.
        """
        if not positions:
            return np.zeros((resolution, resolution))

        centers = np.array([c for _, _, c in positions])

        if rink_mapper and rink_mapper.homography_matrix is not None:
            centers = rink_mapper.camera_to_rink(centers)
            # Normalize to rink dimensions
            x_range = (0, 200)  # rink length in feet
            y_range = (0, 85)   # rink width in feet
        else:
            x_range = (centers[:, 0].min(), centers[:, 0].max())
            y_range = (centers[:, 1].min(), centers[:, 1].max())

        heatmap = np.zeros((resolution, resolution))
        for cx, cy in centers:
            xi = int((cx - x_range[0]) / (x_range[1] - x_range[0] + 1e-8) * (resolution - 1))
            yi = int((cy - y_range[0]) / (y_range[1] - y_range[0] + 1e-8) * (resolution - 1))
            xi = np.clip(xi, 0, resolution - 1)
            yi = np.clip(yi, 0, resolution - 1)
            heatmap[yi, xi] += 1

        return heatmap

    def detect_shifts(self, positions, gap_threshold_sec=10):
        """Split positions into shifts based on tracking gaps.

        A gap > gap_threshold_sec between consecutive frames = new shift.
        Returns list of shifts, each a list of (frame_num, bbox, center).
        """
        if not positions:
            return []

        gap_frames = gap_threshold_sec * self.fps
        shifts = []
        current_shift = [positions[0]]

        for i in range(1, len(positions)):
            frame_gap = positions[i][0] - positions[i - 1][0]
            if frame_gap > gap_frames:
                shifts.append(current_shift)
                current_shift = []
            current_shift.append(positions[i])

        if current_shift:
            shifts.append(current_shift)

        return shifts

    def shift_summary(self, positions, gap_threshold_sec=10):
        """Generate per-shift stats."""
        shifts = self.detect_shifts(positions, gap_threshold_sec)
        summaries = []
        for i, shift in enumerate(shifts):
            duration = self.compute_ice_time(shift)
            distance = self.compute_distance(shift)
            speeds = self.compute_speed(shift)
            avg_speed = np.mean([s for _, s in speeds]) if speeds else 0.0
            max_speed = max([s for _, s in speeds]) if speeds else 0.0

            summaries.append({
                "shift_number": i + 1,
                "start_frame": shift[0][0],
                "end_frame": shift[-1][0],
                "duration_sec": round(duration, 1),
                "distance_px": round(distance, 1),
                "avg_speed_px_sec": round(avg_speed, 1),
                "max_speed_px_sec": round(max_speed, 1),
            })
        return summaries
