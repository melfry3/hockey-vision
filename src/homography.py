"""Rink homography — map camera view positions to overhead rink coordinates."""

import cv2
import numpy as np


# Standard NHL rink dimensions in feet
RINK_LENGTH = 200
RINK_WIDTH = 85


class RinkMapper:
    """Maps pixel coordinates from camera view to standard rink positions."""

    def __init__(self):
        self.homography_matrix = None
        self.src_points = None
        self.dst_points = None

    def calibrate_from_points(self, camera_points, rink_points):
        """Compute homography from matched point pairs.

        camera_points: Nx2 array of (x, y) pixel coords in camera frame
        rink_points: Nx2 array of (x, y) positions on standard rink (in feet)

        Need at least 4 point pairs. Use rink features like:
        - Center ice dot
        - Faceoff circles
        - Blue lines meeting boards
        - Goal lines meeting boards
        - Crease corners
        """
        src = np.array(camera_points, dtype=np.float32)
        dst = np.array(rink_points, dtype=np.float32)

        if len(src) < 4:
            raise ValueError("Need at least 4 point pairs for homography")

        self.homography_matrix, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        self.src_points = src
        self.dst_points = dst
        return self.homography_matrix

    def camera_to_rink(self, pixel_points):
        """Transform pixel coordinates to rink coordinates.

        pixel_points: Nx2 array of (x, y) pixel positions
        Returns: Nx2 array of (x, y) rink positions in feet
        """
        if self.homography_matrix is None:
            raise RuntimeError("Calibrate first with calibrate_from_points()")

        pts = np.array(pixel_points, dtype=np.float32).reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(pts, self.homography_matrix)
        return transformed.reshape(-1, 2)

    def save_calibration(self, path):
        """Save homography matrix to file."""
        if self.homography_matrix is not None:
            np.savez(path, H=self.homography_matrix, src=self.src_points, dst=self.dst_points)

    def load_calibration(self, path):
        """Load homography matrix from file."""
        data = np.load(path)
        self.homography_matrix = data["H"]
        self.src_points = data["src"]
        self.dst_points = data["dst"]
