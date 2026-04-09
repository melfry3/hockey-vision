"""Player tracking using ByteTrack via Ultralytics."""

from ultralytics import YOLO


class PlayerTracker:
    """Tracks detected players across frames using ByteTrack."""

    def __init__(self, model_path="yolo11l.pt", confidence=0.2, imgsz=1280):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.imgsz = imgsz
        self.track_history = {}  # track_id -> list of (frame_num, bbox, center)

    def update(self, frame, frame_num):
        """Run detection + tracking on a frame.

        Returns list of dicts with keys: track_id, bbox, center, confidence.
        """
        results = self.model.track(
            frame,
            conf=self.confidence,
            imgsz=self.imgsz,
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False,
        )
        tracked = []
        for result in results:
            if result.boxes.id is None:
                continue
            for box, track_id in zip(result.boxes, result.boxes.id):
                if int(box.cls[0]) != 0:  # person class only
                    continue
                tid = int(track_id)
                bbox = box.xyxy[0].cpu().numpy()
                cx = float((bbox[0] + bbox[2]) / 2)
                cy = float((bbox[1] + bbox[3]) / 2)
                center = (cx, cy)

                if tid not in self.track_history:
                    self.track_history[tid] = []
                self.track_history[tid].append((frame_num, bbox, center))

                tracked.append({
                    "track_id": tid,
                    "bbox": bbox,
                    "center": center,
                    "confidence": float(box.conf[0]),
                })
        return tracked

    def get_track(self, track_id):
        """Get full position history for a track."""
        return self.track_history.get(track_id, [])

    def all_tracks(self):
        """Return all track IDs and their frame counts."""
        return {tid: len(positions) for tid, positions in self.track_history.items()}
