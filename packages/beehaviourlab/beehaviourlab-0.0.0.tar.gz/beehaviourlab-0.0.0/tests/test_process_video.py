from pathlib import Path

import polars as pl

from beehaviourlab.tracking import process_video as pv


def _sample_video_path() -> Path:
    return Path("tests/data/sample_vid.mp4")


def _detections_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "frame_id": [0, 0],
            "class_id": [1, 1],
            "x": [10, 20],
            "y": [10, 20],
            "w": [5, 5],
            "h": [5, 5],
            "track_id": [1, 2],
            "conf": [0.9, 0.8],
            "stable_id": [1, 2],
            "dx": [0.0, 1.0],
            "dy": [0.0, 1.0],
            "speed": [0.0, 1.4142],
            "speed_smoothed": [0.0, 1.0],
        }
    )


def _empty_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "frame_id": pl.Series([], dtype=pl.Int64),
            "class_id": pl.Series([], dtype=pl.Int64),
            "x": pl.Series([], dtype=pl.Float64),
            "y": pl.Series([], dtype=pl.Float64),
            "w": pl.Series([], dtype=pl.Float64),
            "h": pl.Series([], dtype=pl.Float64),
            "track_id": pl.Series([], dtype=pl.Int64),
            "conf": pl.Series([], dtype=pl.Float64),
            "stable_id": pl.Series([], dtype=pl.Int64),
            "dx": pl.Series([], dtype=pl.Float64),
            "dy": pl.Series([], dtype=pl.Float64),
            "speed": pl.Series([], dtype=pl.Float64),
            "speed_smoothed": pl.Series([], dtype=pl.Float64),
        }
    )


def test_process_video_runs_pipeline(tmp_path, monkeypatch) -> None:
    output_dir = tmp_path / "out"
    input_video = _sample_video_path()

    calls = {}

    def fake_save(model, source, output, conf, xywh, track):
        calls["save"] = (model, source, output, conf, xywh, track)
        df = _detections_df()
        pl.DataFrame(df).write_csv(output)
        return df

    def fake_fix(df, num_objects):
        calls["fix"] = num_objects
        return df

    def fake_extract(df):
        calls["extract"] = True
        return df

    monkeypatch.setattr(pv, "save_bboxes_to_file", fake_save)
    monkeypatch.setattr(pv, "fix_ids_df", fake_fix)
    monkeypatch.setattr(pv, "extract_flow_info_df", fake_extract)

    result = pv.main.callback(input_video, output_dir)
    assert result is None

    assert (output_dir / f"{input_video.stem}_{pv.cfg.csv1_name}").exists()
    assert (output_dir / f"{input_video.stem}_{pv.cfg.csv2_name}").exists()
    assert (output_dir / f"{input_video.stem}_{pv.cfg.csv3_name}").exists()


def test_process_video_handles_no_detections(tmp_path, monkeypatch) -> None:
    output_dir = tmp_path / "out"
    input_video = _sample_video_path()

    calls = {}

    def fake_save(model, source, output, conf, xywh, track):
        calls["save"] = True
        df = _empty_df()
        pl.DataFrame(df).write_csv(output)
        return df

    def fake_fix(df, num_objects):
        calls["fix"] = True
        return df

    def fake_extract(df):
        calls["extract"] = True
        return df

    monkeypatch.setattr(pv, "save_bboxes_to_file", fake_save)
    monkeypatch.setattr(pv, "fix_ids_df", fake_fix)
    monkeypatch.setattr(pv, "extract_flow_info_df", fake_extract)

    result = pv.main.callback(input_video, output_dir)
    assert result is None
    assert (output_dir / f"{input_video.stem}_{pv.cfg.csv2_name}").exists()
    assert (output_dir / f"{input_video.stem}_{pv.cfg.csv3_name}").exists()
