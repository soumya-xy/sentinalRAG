"""2.2 Object detection — Ultralytics YOLO11."""
from __future__ import annotations
from ultralytics import YOLO
from app.core.config import get_settings
from app.models.event import BoundingBox
from app.pipeline.types import Detection, SampledFrame

class ObjectDetector:
    def __init__(self):
        settings = get_settings()
        self.model = YOLO(settings.yolo_model_name)

    def detect(self, frames: list[SampledFrame]) -> list[Detection]:
        settings = get_settings()
        threshold = settings.yolo_confidence_threshold
        detections: list[Detection] = []

        for frame in frames:
            if not frame.image_path or not frame.image_path.exists():
                continue

            results = self.model(
                str(frame.image_path),
                conf=threshold,
                device=settings.yolo_device,
                verbose=False,
            )[0]

            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                conf = float(box.conf[0])
                x_center, y_center, width, height = box.xywh[0].tolist()

                detections.append(
                    Detection(
                        frame=frame,
                        label=label,
                        confidence=round(conf, 3),
                        box=BoundingBox(
                            x=round(x_center, 1),
                            y=round(y_center, 1),
                            w=round(width, 1),
                            h=round(height, 1),
                            frame_timestamp=frame.timestamp_label,
                        ),
                        interesting=True,
                    )
                )
        return detections
