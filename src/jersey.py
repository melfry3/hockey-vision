"""Jersey number recognition from player crops."""

import cv2
import numpy as np
import easyocr


class JerseyReader:
    """Identifies jersey numbers from cropped player images."""

    def __init__(self, crop_top_pct=0.15, crop_bottom_pct=0.55, min_crop_pixels=30):
        self.reader = easyocr.Reader(["en"], gpu=True, verbose=False)
        self.crop_top_pct = crop_top_pct
        self.crop_bottom_pct = crop_bottom_pct
        self.min_crop_pixels = min_crop_pixels

    def read_number(self, frame, bbox):
        """Attempt to read jersey number from a player bounding box.

        Returns (number_str, confidence) or (None, 0.0).
        """
        x1, y1, x2, y2 = [int(v) for v in bbox]
        h = y2 - y1
        w = x2 - x1

        # Crop to torso region where number is likely visible
        top = y1 + int(h * self.crop_top_pct)
        bottom = y1 + int(h * self.crop_bottom_pct)
        crop = frame[top:bottom, x1:x2]

        if crop.shape[0] < self.min_crop_pixels or crop.shape[1] < self.min_crop_pixels:
            return None, 0.0

        # Preprocess: grayscale, contrast boost
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.equalizeHist(gray)

        results = self.reader.readtext(enhanced, allowlist="0123456789")
        if not results:
            return None, 0.0

        # Look for numeric results (jersey numbers are 1-99)
        best_number = None
        best_conf = 0.0
        for (bbox_coords, text, conf) in results:
            digits = "".join(c for c in text if c.isdigit())
            if digits and 1 <= int(digits) <= 99 and conf > best_conf:
                best_number = digits
                best_conf = conf

        return best_number, best_conf

    def identify_target(self, frame, tracked_players, target_number):
        """Find which tracked player is wearing the target jersey number.

        Returns track_id of the best match, or None.
        """
        candidates = {}  # track_id -> (number, confidence)
        for player in tracked_players:
            number, conf = self.read_number(frame, player["bbox"])
            if number == str(target_number) and conf > 0.5:
                candidates[player["track_id"]] = conf

        if not candidates:
            return None
        return max(candidates, key=candidates.get)
