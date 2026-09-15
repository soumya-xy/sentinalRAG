"""2.2 Object detection — Ultralytics YOLO11 (pretrained COCO)."""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.models.event import BoundingBox
from app.pipeline.types import Detection, SampledFrame
from app.services.ml import get_yolo

logger = logging.getLogger("sentinelrag.detect")


class ObjectDetector:
    def detect(self, frames: list[SampledFrame]) -> list[Detection]:
        settings = get_settings()
        model, device = get_yolo()
        threshold = settings.yolo_confidence_threshold
        allowed = settings.yolo_allowed_classes
        detections: list[Detection] = []

        for frame in frames:
            if frame.image_path is None or not frame.image_path.exists():
                continue

            results = model(
                str(frame.image_path),
                conf=threshold,
                device=device,
                verbose=False,
            )[0]

            if results.boxes is None:
                continue

            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = str(model.names[cls_id])
                if allowed and label not in allowed:
                    continue
                conf = float(box.conf[0])
                x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
                detections.append(
                    Detection(
                        frame=frame,
                        label=label,
                        confidence=round(conf, 3),
                        box=BoundingBox(
                            x=round(x1, 1),
                            y=round(y1, 1),
                            w=round(max(0.0, x2 - x1), 1),
                            h=round(max(0.0, y2 - y1), 1),
                            frame_timestamp=frame.timestamp_label,
                        ),
                        interesting=True,
                    )
                )

        logger.info("YOLO produced %s detections from %s frames", len(detections), len(frames))
        return detections
