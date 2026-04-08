"""Pose estimation for skills analysis mode."""

import numpy as np
from ultralytics import YOLO


# COCO keypoint indices
KEYPOINTS = {
    "nose": 0, "left_eye": 1, "right_eye": 2,
    "left_ear": 3, "right_ear": 4,
    "left_shoulder": 5, "right_shoulder": 6,
    "left_elbow": 7, "right_elbow": 8,
    "left_wrist": 9, "right_wrist": 10,
    "left_hip": 11, "right_hip": 12,
    "left_knee": 13, "right_knee": 14,
    "left_ankle": 15, "right_ankle": 16,
}


class PoseAnalyzer:
    """Analyze skating form and body mechanics from video using pose estimation."""

    def __init__(self, model_path="yolo11m-pose.pt", confidence=0.4):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.frame_poses = []  # list of per-frame pose data

    def analyze_frame(self, frame, frame_num):
        """Extract poses from a frame.

        Returns list of dicts with keys: keypoints, bbox, confidence.
        """
        results = self.model(frame, conf=self.confidence, verbose=False)
        poses = []
        for result in results:
            if result.keypoints is None:
                continue
            for i, kp in enumerate(result.keypoints):
                keypoints = kp.xy[0].cpu().numpy()  # shape: (17, 2)
                confs = kp.conf[0].cpu().numpy() if kp.conf is not None else np.ones(17)
                bbox = result.boxes[i].xyxy[0].cpu().numpy() if result.boxes else None

                pose = {
                    "keypoints": keypoints,
                    "keypoint_conf": confs,
                    "bbox": bbox,
                    "frame_num": frame_num,
                }
                poses.append(pose)

        self.frame_poses.append({"frame_num": frame_num, "poses": poses})
        return poses

    def compute_knee_bend(self, keypoints, confs, min_conf=0.5):
        """Compute knee bend angle — key metric for skating form.

        Good hockey stance has deep knee bend (~90-110 degrees).
        Returns (left_angle, right_angle) in degrees, or None if not visible.
        """
        angles = {}
        for side, (hip_idx, knee_idx, ankle_idx) in [
            ("left", (KEYPOINTS["left_hip"], KEYPOINTS["left_knee"], KEYPOINTS["left_ankle"])),
            ("right", (KEYPOINTS["right_hip"], KEYPOINTS["right_knee"], KEYPOINTS["right_ankle"])),
        ]:
            if all(confs[i] > min_conf for i in [hip_idx, knee_idx, ankle_idx]):
                angles[side] = self._angle_between(
                    keypoints[hip_idx], keypoints[knee_idx], keypoints[ankle_idx]
                )
        return angles if angles else None

    def compute_forward_lean(self, keypoints, confs, min_conf=0.5):
        """Compute torso forward lean angle from vertical.

        Good skating posture has forward lean (~30-45 degrees from vertical).
        Returns angle in degrees, or None.
        """
        shoulder_indices = [KEYPOINTS["left_shoulder"], KEYPOINTS["right_shoulder"]]
        hip_indices = [KEYPOINTS["left_hip"], KEYPOINTS["right_hip"]]

        if not all(confs[i] > min_conf for i in shoulder_indices + hip_indices):
            return None

        mid_shoulder = (keypoints[shoulder_indices[0]] + keypoints[shoulder_indices[1]]) / 2
        mid_hip = (keypoints[hip_indices[0]] + keypoints[hip_indices[1]]) / 2

        # Angle from vertical (0 = upright, 90 = horizontal)
        dx = mid_shoulder[0] - mid_hip[0]
        dy = mid_shoulder[1] - mid_hip[1]  # negative = shoulder above hip in image
        angle_from_vertical = abs(np.degrees(np.arctan2(abs(dx), abs(dy))))
        return angle_from_vertical

    def compute_stride_width(self, keypoints, confs, min_conf=0.5):
        """Compute distance between ankles as a proxy for stride width.

        Returns pixel distance, or None.
        """
        left_ankle = KEYPOINTS["left_ankle"]
        right_ankle = KEYPOINTS["right_ankle"]

        if confs[left_ankle] < min_conf or confs[right_ankle] < min_conf:
            return None

        return float(np.linalg.norm(keypoints[left_ankle] - keypoints[right_ankle]))

    def summarize_session(self):
        """Compute summary stats across all analyzed frames."""
        knee_angles = []
        lean_angles = []
        stride_widths = []

        for frame_data in self.frame_poses:
            for pose in frame_data["poses"]:
                kp = pose["keypoints"]
                conf = pose["keypoint_conf"]

                knee = self.compute_knee_bend(kp, conf)
                if knee:
                    knee_angles.extend(knee.values())

                lean = self.compute_forward_lean(kp, conf)
                if lean is not None:
                    lean_angles.append(lean)

                stride = self.compute_stride_width(kp, conf)
                if stride is not None:
                    stride_widths.append(stride)

        summary = {}
        if knee_angles:
            summary["knee_bend"] = {
                "mean": float(np.mean(knee_angles)),
                "min": float(np.min(knee_angles)),
                "max": float(np.max(knee_angles)),
            }
        if lean_angles:
            summary["forward_lean"] = {
                "mean": float(np.mean(lean_angles)),
                "min": float(np.min(lean_angles)),
                "max": float(np.max(lean_angles)),
            }
        if stride_widths:
            summary["stride_width_px"] = {
                "mean": float(np.mean(stride_widths)),
                "min": float(np.min(stride_widths)),
                "max": float(np.max(stride_widths)),
            }
        return summary

    @staticmethod
    def _angle_between(a, b, c):
        """Angle at point b formed by points a-b-c, in degrees."""
        ba = a - b
        bc = c - b
        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        return float(np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0))))
