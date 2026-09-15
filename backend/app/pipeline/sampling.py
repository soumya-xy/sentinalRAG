"""2.1 Frame sampling using OpenCV (fixed interval). Writes only into a temp work dir."""

from __future__ import annotations

import logging
from pathlib import Path

import cv2

from app.core.config import get_settings
from app.pipeline.types import SampledFrame

logger = logging.getLogger("sentinelrag.sampling")


def seconds_to_label(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def probe_video(video_path: Path) -> tuple[float | None, float]:
    """Return (duration_seconds, fps). Duration is None if the file cannot be read."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None, 0.0
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)
    cap.release()
    if fps > 1e-3 and frame_count > 0:
        return frame_count / fps, fps
    return None, fps


class FrameSampler:
    def sample(self, video_path: Path, *, video_id: str, work_dir: Path) -> list[SampledFrame]:
        settings = get_settings()
        interval_sec = settings.frame_sample_interval_seconds or 1.5
        frames_dir = work_dir / "frames" / video_id
        frames_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error("Could not open video %s", video_path)
            return []

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0) or 30.0
        frame_step = max(1, int(round(fps * interval_sec)))

        frames: list[SampledFrame] = []
        frame_index = 0
        saved_index = 0

        while True:
            grabbed = cap.grab()
            if not grabbed:
                break
            if frame_index % frame_step == 0:
                ok, frame = cap.retrieve()
                if not ok or frame is None:
                    frame_index += 1
                    continue
                t_sec = frame_index / fps
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
            frame_index += 1

        cap.release()
        logger.info("Sampled %s frames from %s", len(frames), video_id)
        return frames
