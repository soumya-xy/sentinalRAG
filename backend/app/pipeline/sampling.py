"""2.1 Frame sampling using OpenCV."""
from __future__ import annotations
from pathlib import Path
import cv2
from app.core.config import get_settings
from app.pipeline.types import SampledFrame

def seconds_to_label(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

class FrameSampler:
    def sample(self, video_path: Path, duration_seconds: float = 1020.0) -> list[SampledFrame]:
        settings = get_settings()
        interval_sec = settings.frame_sample_interval_seconds or 1.5
        frames_dir = settings.frames_dir
        frames_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_step = max(1, int(fps * interval_sec))

        frames: list[SampledFrame] = []
        frame_count = 0
        saved_index = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % frame_step == 0:
                t_sec = frame_count / fps
                img_path = frames_dir / f"frame_{saved_index:05d}.jpg"
                cv2.imwrite(str(img_path), frame)
                frames.append(
                    SampledFrame(
                        frame_index=saved_index,
                        timestamp_seconds=t_sec,
                        timestamp_label=seconds_to_label(t_sec),
                        image_path=img_path,
                    )
                )
                saved_index += 1
            frame_count += 1

        cap.release()
        return frames
