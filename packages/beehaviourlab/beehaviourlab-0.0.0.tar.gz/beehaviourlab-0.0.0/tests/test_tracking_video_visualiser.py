from pathlib import Path

import pytest

from beehaviourlab.tracking import tracking_video_visualiser as tvv


def _sample_video() -> Path:
    return Path("tests/data/sample_vid.mp4")


def _sample_csv() -> Path:
    return Path("tests/data/sample_vid_yolo_tracking_fixed_ids.csv")


def test_load_detections_from_sample_csv() -> None:
    detections = tvv.load_detections(_sample_csv())
    assert detections
    first_frame = min(detections)
    assert len(detections[first_frame]) > 0
    det = detections[first_frame][0]
    assert det.frame_id == first_frame
    assert det.w > 0
    assert det.h > 0


def test_load_detections_missing_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "missing.csv"
    csv_path.write_text("frame_id,x,y,w,h\n1,10,10,5,5\n")

    with pytest.raises(ValueError):
        tvv.load_detections(csv_path)


def test_main_generates_output_video(tmp_path: Path) -> None:
    out_path = tmp_path / "annotated.mp4"

    result = tvv.main.callback(
        _sample_video(),
        _sample_csv(),
        out_path,
        persist_frames=5,
        trail_length=5,
        start_frame=0,
        end_frame=1,
        show=False,
    )

    assert result is None
    assert out_path.exists()
    assert out_path.stat().st_size > 0


def test_main_handles_no_detections(tmp_path: Path) -> None:
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text(
        "frame_id,class_id,x,y,w,h,track_id\n"
    )
    out_path = tmp_path / "empty_out.mp4"

    result = tvv.main.callback(
        _sample_video(),
        empty_csv,
        out_path,
        persist_frames=5,
        trail_length=5,
        start_frame=0,
        end_frame=1,
        show=False,
    )

    assert result is None
    assert out_path.exists()
    assert out_path.stat().st_size > 0
