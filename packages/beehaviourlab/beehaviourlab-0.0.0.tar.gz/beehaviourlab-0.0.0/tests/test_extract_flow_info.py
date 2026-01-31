from pathlib import Path

import polars as pl
import pytest
from click.testing import CliRunner

from beehaviourlab.tracking.extract_flow_info import extract_flow_info, main


def test_extract_flow_info_adds_columns() -> None:
    df = pl.read_csv("tests/data/sample_vid_yolo_tracking_fixed_ids.csv")
    out = extract_flow_info(df)

    assert "dx" in out.columns
    assert "dy" in out.columns
    assert "speed" in out.columns
    assert "speed_smoothed" in out.columns
    assert out["speed"].dtype == pl.Float64
    assert len(out) == len(df)
    assert out["speed"].max() > 0


def test_extract_flow_info_corner_coords_conversion() -> None:
    df = pl.DataFrame(
        {
            "stable_id": [1, 1],
            "frame_id": [0, 1],
            "x1": [0, 10],
            "y1": [0, 0],
            "x2": [10, 20],
            "y2": [10, 10],
        }
    )
    out = extract_flow_info(df).sort(["frame_id"])

    assert out["w"].to_list() == [10, 10]
    assert out["h"].to_list() == [10, 10]
    assert out["x"].to_list() == [5.0, 15.0]
    assert out["y"].to_list() == [5.0, 5.0]
    assert out["speed"].to_list() == [0.0, 10.0]


def test_extract_flow_info_empty_exits() -> None:
    df = pl.DataFrame(
        {
            "stable_id": pl.Series([], dtype=pl.Int64),
            "frame_id": pl.Series([], dtype=pl.Int64),
            "x": pl.Series([], dtype=pl.Float64),
            "y": pl.Series([], dtype=pl.Float64),
        }
    )
    with pytest.raises(SystemExit):
        extract_flow_info(df)


def test_main_writes_output(tmp_path: Path) -> None:
    input_csv = Path("tests/data/sample_vid_yolo_tracking_fixed_ids.csv")
    output_csv = tmp_path / "flow.csv"

    result = main.callback(input_csv, output_csv, False, False)
    assert result is None
    assert output_csv.exists()
    df_out = pl.read_csv(output_csv)
    assert "speed_smoothed" in df_out.columns
    assert df_out["speed"].max() > 0


def test_main_dry_run_does_not_write(tmp_path: Path) -> None:
    input_csv = Path("tests/data/sample_vid_yolo_tracking_fixed_ids.csv")
    output_csv = tmp_path / "flow.csv"

    result = main.callback(input_csv, output_csv, True, False)
    assert result is None
    assert not output_csv.exists()


def test_main_errors_on_missing_coordinates(tmp_path: Path) -> None:
    df = pl.DataFrame(
        {"stable_id": [1], "frame_id": [0], "class_id": [1]}
    )
    input_csv = tmp_path / "missing_coords.csv"
    df.write_csv(input_csv)

    with pytest.raises(Exception) as exc:
        main.callback(input_csv, None, True, False)

    assert "Missing coordinate columns" in str(exc.value)


def test_main_verbose_writes_output(tmp_path: Path) -> None:
    input_csv = Path("tests/data/sample_vid_yolo_tracking_fixed_ids.csv")
    output_csv = tmp_path / "flow_verbose.csv"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            str(input_csv),
            "--output",
            str(output_csv),
            "--verbose",
        ],
    )

    assert result.exit_code == 0
    assert output_csv.exists()
    assert "Detected coordinate format" in result.output
    assert "Per-object movement statistics" in result.output


def test_main_cli_missing_required_columns(tmp_path: Path) -> None:
    df = pl.DataFrame({"frame_id": [0], "x": [1.0], "y": [1.0]})
    input_csv = tmp_path / "missing_required.csv"
    df.write_csv(input_csv)

    runner = CliRunner()
    result = runner.invoke(main, [str(input_csv)])

    assert result.exit_code != 0
    assert "Error processing file" in result.output
