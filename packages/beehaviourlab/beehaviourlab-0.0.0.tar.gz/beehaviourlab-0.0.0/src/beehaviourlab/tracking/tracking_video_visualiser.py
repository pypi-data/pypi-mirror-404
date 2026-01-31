#!/usr/bin/env python3
"""
Video tracking visualiser
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Optional, Tuple

import click
import cv2
import pandas as pd

DEFAULT_FPS = 30.0
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
WINDOW_NAME = "tracking"
REQUIRED_COLS = ["frame_id", "class_id", "x", "y", "w", "h", "track_id"]
PALETTE = [
    (235, 64, 52),
    (52, 168, 235),
    (52, 235, 119),
    (208, 52, 235),
    (52, 235, 219),
    (235, 202, 52),
    (235, 143, 52),
    (112, 52, 235),
]


def _video_option_help() -> str:
    return "Input video that will receive drawn tracks."


def _csv_option_help() -> str:
    return "CSV file containing detections with columns frame_id,x,y,w,h,class_id,track_id."


def _out_option_help() -> str:
    return "Destination video file that will contain the overlays."


def _persist_option_help() -> str:
    return "How many frames after the last detection to keep drawing a trail."


def _trail_option_help() -> str:
    return "Number of past positions to retain per track for trail drawing."


def _start_option_help() -> str:
    return "Frame index to start processing from (0 = beginning)."


def _end_option_help() -> str:
    return "Inclusive frame index to stop at; defaults to the end of the video."


def _show_option_help() -> str:
    return "Display a live preview window while writing the video."


@dataclass(frozen=True)
class Detection:
    frame_id: int
    class_id: int
    cx: int
    cy: int
    w: int
    h: int
    track_id: int
    stable_id: Optional[int] = None
    status: Optional[str] = None
    filtered_class: Optional[int] = None

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        x1 = int(self.cx - self.w / 2)
        y1 = int(self.cy - self.h / 2)
        return (x1, y1, self.w, self.h)

    @property
    def centre(self) -> Tuple[int, int]:
        return (self.cx, self.cy)


def colour_for_class(class_id: int) -> Tuple[int, int, int]:
    return PALETTE[class_id % len(PALETTE)]


def load_detections(csv_path: Path) -> Dict[int, List[Detection]]:
    df = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    has_status = "status" in df.columns
    has_stable_id = "stable_id" in df.columns
    has_filtered_class = "filtered_class_id" in df.columns
    keep_cols = (
        REQUIRED_COLS
        + (["status"] if has_status else [])
        + (["stable_id"] if has_stable_id else [])
        + (["filtered_class_id"] if has_filtered_class else [])
    )
    cols = df[keep_cols].copy()

    # Only coerce numeric for required numeric fields
    for col in REQUIRED_COLS:
        cols[col] = pd.to_numeric(cols[col], errors="coerce")

    cols = cols.dropna(subset=REQUIRED_COLS)

    for col in ["frame_id", "class_id", "x", "y", "w", "h", "track_id"]:
        cols[col] = cols[col].astype(int)

    cols["w"] = cols["w"].clip(lower=1)
    cols["h"] = cols["h"].clip(lower=1)

    detections_by_frame: Dict[int, List[Detection]] = defaultdict(list)
    for row in cols.itertuples(index=False):
        stable_id = getattr(row, "stable_id") if has_stable_id else None
        status_val = getattr(row, "status") if has_status else None
        filtered_class = (
            getattr(row, "filtered_class_id", None) if has_filtered_class else None
        )
        det = Detection(
            frame_id=row.frame_id,
            class_id=row.class_id,
            cx=row.x,
            cy=row.y,
            w=row.w,
            h=row.h,
            track_id=row.track_id,
            stable_id=stable_id
            if stable_id is not None and pd.notna(stable_id)
            else None,
            status=str(status_val)
            if (status_val is not None and pd.notna(status_val))
            else None,
            filtered_class=filtered_class
            if filtered_class is not None and pd.notna(filtered_class)
            else None,
        )
        detections_by_frame[det.frame_id].append(det)
    return detections_by_frame


def draw_bbox(frame, det: Detection, colour: Tuple[int, int, int]) -> None:
    x, y, w, h = det.bbox
    cv2.rectangle(frame, (x, y), (x + w, y + h), colour, 2)
    label_parts = [
        f"cls {det.class_id if det.filtered_class is None else det.filtered_class}",
        f"id {det.track_id}",
    ]
    if det.status:
        label_parts.append(det.status)
    if det.stable_id is not None:
        label_parts.append(f"st_id {det.stable_id}")
    label = " | ".join(label_parts)
    _draw_label(frame, (x, y - 8), label, colour)


def _draw_label(
    frame, origin: Tuple[int, int], text: str, colour: Tuple[int, int, int]
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    thickness = 1
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    x, y = origin
    y = max(th + 4, y)
    cv2.rectangle(frame, (x - 2, y - th - 4), (x + tw + 2, y + 2), WHITE, -1)
    cv2.putText(frame, text, (x, y), font, scale, colour, thickness, cv2.LINE_AA)


def draw_trail(frame, points: Iterable[Tuple[int, int]]) -> None:
    pts = list(points)
    if len(pts) < 2:
        return
    for i in range(1, len(pts)):
        p1 = pts[i - 1]
        p2 = pts[i]
        alpha = i / len(pts)
        col = (int(255 * (1 - alpha)), int(255 * (1 - alpha)), int(255 * (1 - alpha)))
        cv2.line(frame, p1, p2, col, 2)


def _bbox_visible(det: Detection, frame_width: int, frame_height: int) -> bool:
    x, y, w, h = det.bbox
    if w <= 0 or h <= 0:
        return False
    if x >= frame_width or y >= frame_height:
        return False
    if x + w <= 0 or y + h <= 0:
        return False
    return True


@dataclass(frozen=True)
class VisualisationConfig:
    persist_frames: int
    trail_length: int
    start_frame: int
    end_frame: int | None
    show: bool

    @classmethod
    def from_cli(
        cls,
        persist_frames: int,
        trail_length: int,
        start_frame: int,
        end_frame: int | None,
        show: bool,
    ) -> "VisualisationConfig":
        safe_persist = max(0, persist_frames)
        safe_trail = max(1, trail_length)
        safe_start = max(0, start_frame)
        safe_end = None if end_frame is None else max(safe_start, end_frame, 0)
        return cls(
            persist_frames=safe_persist,
            trail_length=safe_trail,
            start_frame=safe_start,
            end_frame=safe_end,
            show=show,
        )

    def resolved_end(self, frame_count: int | None) -> int | None:
        if self.end_frame is not None:
            return self.end_frame
        if frame_count is None:
            return None
        return max(self.start_frame, frame_count - 1)


@dataclass(frozen=True)
class VideoMeta:
    fps: float
    width: int
    height: int
    frame_count: int | None


@dataclass
class TrackingState:
    trail_length: int
    persist_frames: int
    trails: Dict[int, Deque[Tuple[int, int]]] = field(default_factory=dict)
    last_seen: Dict[int, int] = field(default_factory=dict)

    def record(self, frame_idx: int, detections: Iterable[Detection]) -> None:
        for det in detections:
            trail = self.trails.get(det.track_id)
            if trail is None:
                trail = deque(maxlen=self.trail_length)
                self.trails[det.track_id] = trail
            trail.append(det.centre)
            self.last_seen[det.track_id] = frame_idx

    def visible_trails(self, frame_idx: int) -> Iterable[Iterable[Tuple[int, int]]]:
        stale: List[int] = []
        for track_id, pts in list(self.trails.items()):
            last = self.last_seen.get(track_id, -10**9)
            if frame_idx - last <= self.persist_frames:
                yield pts
            else:
                stale.append(track_id)
        for track_id in stale:
            self.trails.pop(track_id, None)
            self.last_seen.pop(track_id, None)

    @property
    def active_track_count(self) -> int:
        return len(self.trails)


def _open_video(video_path: Path) -> tuple[cv2.VideoCapture, VideoMeta]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count_raw = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_count = (
        int(frame_count_raw)
        if frame_count_raw and frame_count_raw > 0
        else None
    )
    return cap, VideoMeta(fps=fps, width=width, height=height, frame_count=frame_count)


def _create_writer(out_path: Path, meta: VideoMeta) -> cv2.VideoWriter:
    suffix = out_path.suffix.lower()
    fourcc = cv2.VideoWriter_fourcc(*("mp4v" if suffix == ".mp4" else "avc1"))
    writer = cv2.VideoWriter(str(out_path), fourcc, meta.fps, (meta.width, meta.height))
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open writer for: {out_path}")
    return writer


def _render_frame(
    frame,
    frame_idx: int,
    detections: Iterable[Detection],
    state: TrackingState,
    fps: float,
) -> None:
    frame_height, frame_width = frame.shape[:2]
    for det in detections:
        if not _bbox_visible(det, frame_width, frame_height):
            continue
        colour = colour_for_class(
            det.class_id if det.filtered_class is None else det.filtered_class
        )
        draw_bbox(frame, det, colour)
    for trail in state.visible_trails(frame_idx):
        draw_trail(frame, trail)
    text = f"frame {frame_idx} | fps ~{fps:.1f} | tracks active {state.active_track_count}"
    _draw_label(frame, (8, 24), text, BLACK)


def _maybe_show(frame) -> bool:
    cv2.imshow(WINDOW_NAME, frame)
    key = cv2.waitKey(1) & 0xFF
    return key in (27, ord("q"))


def _process_video(
    cap: cv2.VideoCapture,
    writer: cv2.VideoWriter,
    detections_by_frame: Dict[int, List[Detection]],
    meta: VideoMeta,
    config: VisualisationConfig,
) -> None:
    if config.start_frame:
        cap.set(cv2.CAP_PROP_POS_FRAMES, config.start_frame)
    state = TrackingState(
        trail_length=config.trail_length,
        persist_frames=config.persist_frames,
    )
    end_frame = config.resolved_end(meta.frame_count)
    frame_idx = config.start_frame
    while end_frame is None or frame_idx <= end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        detections = detections_by_frame.get(frame_idx, [])
        state.record(frame_idx, detections)
        _render_frame(frame, frame_idx, detections, state, meta.fps)
        writer.write(frame)
        if config.show and _maybe_show(frame):
            break
        frame_idx += 1


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--video",
    "video_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help=_video_option_help(),
)
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help=_csv_option_help(),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    required=True,
    help=_out_option_help(),
)
@click.option(
    "--persist-frames",
    default=15,
    show_default=True,
    type=int,
    help=_persist_option_help(),
)
@click.option(
    "--trail-length",
    default=20,
    show_default=True,
    type=int,
    help=_trail_option_help(),
)
@click.option(
    "--start-frame",
    default=0,
    show_default=True,
    type=int,
    help=_start_option_help(),
)
@click.option(
    "--end-frame",
    default=None,
    type=int,
    help=_end_option_help(),
)
@click.option("--show", is_flag=True, help=_show_option_help())
def main(
    video_path: Path,
    csv_path: Path,
    out_path: Path,
    persist_frames: int,
    trail_length: int,
    start_frame: int,
    end_frame: int | None,
    show: bool,
) -> None:
    """Render a tracking overlay video from detections CSV data.

    The CSV should contain tracking detections with columns like:
    - frame_id
    - x, y, w, h
    - track_id
    Output is a new video with bounding boxes and trails drawn on top of the input.

    Examples:
        bee track tracking-video-visualiser --video input.mp4 --csv tracks.csv \\
            --out annotated.mp4
        bee track tracking-video-visualiser --video input.mp4 --csv tracks.csv \\
            --out annotated.mp4 --start-frame 100 --end-frame 300 --show
    """
    config = VisualisationConfig.from_cli(
        persist_frames=persist_frames,
        trail_length=trail_length,
        start_frame=start_frame,
        end_frame=end_frame,
        show=show,
    )
    detections_by_frame = load_detections(csv_path)
    cap, meta = _open_video(video_path)
    try:
        writer = _create_writer(out_path, meta)
    except BaseException:
        cap.release()
        raise
    try:
        _process_video(cap, writer, detections_by_frame, meta, config)
    finally:
        cap.release()
        writer.release()
        if config.show:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
