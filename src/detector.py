"""Player detection using YOLOv11."""

from ultralytics import YOLO


class PlayerDetector:
    """Detects players in video frames using YOLOv11."""

    def __init__(self, model_path="yolo11x.pt", confidence=0.05):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.person_class_id = 0  # COCO 'person'

    def detect(self, frame):
        """Detect all people in a frame.

        Returns list of dicts with keys: bbox (x1,y1,x2,y2), confidence.
        """
        results = self.model(frame, conf=self.confidence, verbose=False)
        detections = []
        for result in results:
            for box in result.boxes:
                if int(box.cls[0]) == self.person_class_id:
                    detections.append({
                        "bbox": box.xyxy[0].cpu().numpy(),
                        "confidence": float(box.conf[0]),
                    })
        return detections
