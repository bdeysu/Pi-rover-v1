"""Optional YOLO object detection, kept separate from camera capture."""

import config


class ObjectDetector:
    def __init__(self):
        self.enabled = False
        self.model = None

        if not config.YOLO_ENABLED:
            print("YOLO is disabled in config.py")
            return

        try:
            from ultralytics import YOLO

            print("Loading YOLO model:", config.MODEL_PATH)
            self.model = YOLO(config.MODEL_PATH)
            self.enabled = True
            print("YOLO loaded")
        except Exception as error:
            print("YOLO couldn't start:", error)

    def detect(self, frame):
        """Return simple dictionaries that Flask can convert to JSON."""
        if not self.enabled:
            return []

        results = self.model.predict(
            frame,
            imgsz=config.YOLO_IMAGE_SIZE,
            conf=config.YOLO_CONFIDENCE,
            verbose=False,
        )
        detections = []

        if not results or results[0].boxes is None:
            return detections

        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            name = self.model.names.get(class_id, str(class_id))
            detections.append(
                {
                    "name": name,
                    "conf": confidence,
                    "box": [int(x1), int(y1), int(x2), int(y2)],
                }
            )

        return detections
