from pathlib import Path

import polars as pl
import pytest

from beehaviourlab.tracking import yolo_predict_to_file as yptf


class _FakeTensor:
    def __init__(self, value: int) -> None:
        self._value = value

    def item(self) -> int:
        return self._value


class _FakeBox:
    def __init__(
        self,
        conf: float,
        cls_id: int,
        xywh: tuple[int, int, int, int],
        xyxy: tuple[int, int, int, int],
    ) -> None:
        self.conf = [conf]
        self.cls = _FakeTensor(cls_id)
        self.xywh = [xywh]
        self.xyxy = [xyxy]


class _FakeBoxes(list):
    def __init__(self, boxes: list[_FakeBox], ids: list[_FakeTensor] | None = None):
        super().__init__(boxes)
        self.id = ids


class _FakeResults:
    def __init__(self, boxes: _FakeBoxes) -> None:
        self.boxes = boxes


class _FakeResultsNone:
    boxes = None


class _FakeYOLO:
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path

    def __call__(self, frame):
        boxes = _FakeBoxes(
            [
                _FakeBox(0.9, 1, (10, 20, 30, 40), (10, 20, 40, 60)),
                _FakeBox(0.2, 2, (11, 21, 31, 41), (11, 21, 41, 61)),
            ]
        )
        return [_FakeResults(boxes)]

    def track(self, frame, persist: bool, tracker: str, verbose: bool):
        boxes = _FakeBoxes(
            [
                _FakeBox(0.4, 3, (5, 6, 7, 8), (5, 6, 12, 14)),
                _FakeBox(0.7, 4, (9, 10, 11, 12), (9, 10, 20, 22)),
            ],
            ids=[_FakeTensor(10), _FakeTensor(11)],
        )
        return [_FakeResults(boxes)]


class _FakeYOLOEmpty:
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path

    def __call__(self, frame):
        return [None]

    def track(self, frame, persist: bool, tracker: str, verbose: bool):
        return [None]


class _FakeYOLONoIds:
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path

    def __call__(self, frame):
        return [_FakeResults(_FakeBoxes([]))]

    def track(self, frame, persist: bool, tracker: str, verbose: bool):
        boxes = _FakeBoxes(
            [
                _FakeBox(0.4, 3, (5, 6, 7, 8), (5, 6, 12, 14)),
            ],
            ids=None,
        )
        return [_FakeResults(boxes)]


class _FakeCapture:
    def __init__(self, source: str) -> None:
        self._read_calls = 0

    def isOpened(self) -> bool:
        return True

    def read(self):
        if self._read_calls == 0:
            self._read_calls += 1
            return True, object()
        return False, None

    def release(self) -> None:
        return None


def _sample_video_path() -> str:
    return str(Path(__file__).resolve().parent / "data" / "sample_vid.mp4")


def _model_path() -> str:
    return str(
        Path(__file__).resolve().parents[1]
        / "src"
        / "beehaviourlab"
        / "tracking"
        / "model"
        / "feeder_bee_YOLO.pt"
    )


def test_save_bboxes_to_file_xyxy_filters_by_conf(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(yptf, "YOLO", _FakeYOLO)
    monkeypatch.setattr(yptf.cv2, "VideoCapture", _FakeCapture)

    out_path = tmp_path / "out.csv"
    df = yptf.save_bboxes_to_file(
        _model_path(),
        _sample_video_path(),
        str(out_path),
        conf_threshold=0.5,
        xywh=False,
        track=False,
    )

    assert isinstance(df, pl.DataFrame)
    assert df.columns == ["frame_id", "class_id", "x1", "y1", "x2", "y2", "conf"]
    assert len(df) == 1
    assert df["class_id"].to_list() == [1]
    assert out_path.exists()


def test_save_bboxes_to_file_tracking_outputs_track_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(yptf, "YOLO", _FakeYOLO)
    monkeypatch.setattr(yptf.cv2, "VideoCapture", _FakeCapture)

    out_path = tmp_path / "tracked.csv"
    df = yptf.save_bboxes_to_file(
        _model_path(),
        _sample_video_path(),
        str(out_path),
        conf_threshold=0.95,
        xywh=True,
        track=True,
    )

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
    assert df["track_id"].to_list() == [10, 11]
    assert len(df) == 2
    assert out_path.exists()


def test_save_bboxes_to_file_invalid_conf_exits(tmp_path, capsys) -> None:
    model_path = tmp_path / "model.pt"
    video_path = tmp_path / "video.mp4"
    model_path.write_text("stub")
    video_path.write_text("stub")

    with pytest.raises(SystemExit):
        yptf.save_bboxes_to_file(
            str(model_path),
            str(video_path),
            str(tmp_path / "out.csv"),
            conf_threshold=-0.1,
            xywh=False,
            track=False,
        )

    captured = capsys.readouterr()
    assert "Confidence threshold must be between 0.0 and 1." in captured.out


def test_save_bboxes_to_file_missing_video_exits(tmp_path, capsys) -> None:
    model_path = tmp_path / "model.pt"
    model_path.write_text("stub")
    missing_video = tmp_path / "missing.mp4"

    with pytest.raises(SystemExit):
        yptf.save_bboxes_to_file(
            str(model_path),
            str(missing_video),
            str(tmp_path / "out.csv"),
            conf_threshold=0.5,
            xywh=False,
            track=False,
        )

    captured = capsys.readouterr()
    assert "Source file" in captured.out


def test_save_bboxes_to_file_missing_model_exits(tmp_path, capsys) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_text("stub")
    missing_model = tmp_path / "missing.pt"

    with pytest.raises(SystemExit):
        yptf.save_bboxes_to_file(
            str(missing_model),
            str(video_path),
            str(tmp_path / "out.csv"),
            conf_threshold=0.5,
            xywh=False,
            track=False,
        )

    captured = capsys.readouterr()
    assert "Model file" in captured.out


def test_save_bboxes_to_file_handles_empty_results(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(yptf, "YOLO", _FakeYOLOEmpty)
    monkeypatch.setattr(yptf.cv2, "VideoCapture", _FakeCapture)

    out_path = tmp_path / "empty.csv"
    df = yptf.save_bboxes_to_file(
        _model_path(),
        _sample_video_path(),
        str(out_path),
        conf_threshold=0.5,
        xywh=False,
        track=False,
    )

    assert df.is_empty()
    assert out_path.exists()


def test_save_bboxes_to_file_handles_missing_track_ids(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(yptf, "YOLO", _FakeYOLONoIds)
    monkeypatch.setattr(yptf.cv2, "VideoCapture", _FakeCapture)

    out_path = tmp_path / "no_ids.csv"
    df = yptf.save_bboxes_to_file(
        _model_path(),
        _sample_video_path(),
        str(out_path),
        conf_threshold=0.5,
        xywh=True,
        track=True,
    )

    assert df.is_empty()
    assert out_path.exists()


def test_cli_uses_default_config(monkeypatch, tmp_path) -> None:
    from click.testing import CliRunner

    model_path = tmp_path / "model.pt"
    video_path = tmp_path / "video.mp4"
    output_path = tmp_path / "out.csv"
    model_path.write_text("stub")
    video_path.write_text("stub")

    called = {}

    def _fake_save(model, source, output, conf, xywh, track):
        called["args"] = (model, source, output, conf, xywh, track)
        return None

    monkeypatch.setattr(yptf, "save_bboxes_to_file", _fake_save)

    runner = CliRunner()
    result = runner.invoke(
        yptf.main,
        [
            "--model-path",
            str(model_path),
            "--source-video",
            str(video_path),
            "--output-path",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert called["args"] == (
        str(model_path),
        str(video_path),
        str(output_path),
        yptf.cfg.conf_threshold,
        yptf.cfg.xywh,
        yptf.cfg.track,
    )
