from pathlib import Path

import pytest

from beehaviourlab.tracking.yolo_predict_to_file import save_bboxes_to_file


@pytest.mark.integration
@pytest.mark.slow
def test_save_bboxes_to_file_with_real_model(tmp_path: Path) -> None:
    model_path = Path("src/beehaviourlab/tracking/model/feeder_bee_YOLO.pt")
    video_path = Path("tests/data/sample_vid.mp4")
    output_path = tmp_path / "detections.csv"

    df = save_bboxes_to_file(
        str(model_path),
        str(video_path),
        str(output_path),
        conf_threshold=0.25,
        xywh=False,
        track=False,
    )

    assert output_path.exists()
    assert df.columns == ["frame_id", "class_id", "x1", "y1", "x2", "y2", "conf"]


@pytest.mark.integration
@pytest.mark.slow
def test_save_bboxes_to_file_with_tracking(tmp_path: Path) -> None:
    model_path = Path("src/beehaviourlab/tracking/model/feeder_bee_YOLO.pt")
    video_path = Path("tests/data/sample_vid.mp4")
    output_path = tmp_path / "tracked.csv"

    df = save_bboxes_to_file(
        str(model_path),
        str(video_path),
        str(output_path),
        conf_threshold=0.25,
        xywh=True,
        track=True,
    )

    assert output_path.exists()
    assert df.columns == [
        "frame_id",
        "class_id",
        "x",
        "y",
        "w",
        "h",
        "track_id",
        "conf",
    ]
