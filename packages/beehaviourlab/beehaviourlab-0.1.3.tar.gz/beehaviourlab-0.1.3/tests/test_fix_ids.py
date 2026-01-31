import polars as pl
from click.testing import CliRunner

from beehaviourlab.tracking.fix_ids import filter_out_feeder, fix_ids
from beehaviourlab.tracking import fix_ids as fix_ids_module


def test_filter_out_feeder_removes_class() -> None:
    df = pl.DataFrame(
        {
            "frame_id": [0, 0],
            "class_id": [1, 2],
            "x": [0.0, 1.0],
            "y": [0.0, 1.0],
        }
    )
    filtered = filter_out_feeder(df)
    assert filtered["class_id"].to_list() == [2]


def test_fix_ids_handles_empty_dataframe() -> None:
    df = pl.DataFrame(
        {
            "frame_id": pl.Series([], dtype=pl.Int64),
            "x": pl.Series([], dtype=pl.Float64),
            "y": pl.Series([], dtype=pl.Float64),
        }
    )
    result = fix_ids(df, num_objects=2)
    assert result.is_empty()
    assert "stable_id" in result.columns


def test_fix_ids_interpolates_missing_detection() -> None:
    df = pl.DataFrame(
        {
            "frame_id": [0, 0, 1],
            "class_id": [2, 2, 2],
            "x": [0.0, 10.0, 0.5],
            "y": [0.0, 10.0, 0.5],
        }
    )
    result = fix_ids(df, num_objects=2).sort(["frame_id", "stable_id"])

    assert len(result) == 4
    frame1 = result.filter(pl.col("frame_id") == 1)
    assert frame1["stable_id"].to_list() == [1, 2]

    sid2 = frame1.filter(pl.col("stable_id") == 2)
    assert sid2["x"].to_list() == [10.0]
    assert sid2["y"].to_list() == [10.0]


def test_fix_ids_with_sample_csv() -> None:
    df = pl.read_csv("tests/data/sample_vid_yolo_tracking_raw.csv")
    result = fix_ids(df, num_objects=5)

    assert "stable_id" in result.columns
    assert result["stable_id"].min() >= 1
    assert result["stable_id"].max() <= 5
    assert result["frame_id"].n_unique() == df["frame_id"].n_unique()


def test_fix_ids_adds_missing_stable_id_column() -> None:
    df = pl.DataFrame(
        {
            "frame_id": [0],
            "class_id": [2],
            "x": [1.0],
            "y": [2.0],
        }
    )
    result = fix_ids(df, num_objects=1)
    assert "stable_id" in result.columns


def test_fix_ids_retains_last_position_for_missing_object() -> None:
    df = pl.DataFrame(
        {
            "frame_id": [0, 0, 1],
            "class_id": [2, 2, 2],
            "x": [0.0, 10.0, 0.2],
            "y": [0.0, 10.0, 0.1],
        }
    )
    result = fix_ids(df, num_objects=2).sort(["frame_id", "stable_id"])
    frame1 = result.filter(pl.col("frame_id") == 1)
    sid2 = frame1.filter(pl.col("stable_id") == 2)
    assert sid2["x"].to_list() == [10.0]
    assert sid2["y"].to_list() == [10.0]


def test_fix_ids_cli_writes_output(tmp_path) -> None:
    df = pl.DataFrame(
        {
            "frame_id": [0, 1],
            "class_id": [2, 2],
            "x": [1.0, 2.0],
            "y": [1.0, 2.0],
        }
    )
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    df.write_csv(input_csv)

    runner = CliRunner()
    result = runner.invoke(
        fix_ids_module.main,
        [
            str(input_csv),
            "--output",
            str(output_csv),
            "--num-objects",
            "2",
            "--verbose",
        ],
    )

    assert result.exit_code == 0
    assert output_csv.exists()
    out_df = pl.read_csv(output_csv)
    assert "stable_id" in out_df.columns


def test_fix_ids_cli_dry_run_does_not_write(tmp_path) -> None:
    df = pl.DataFrame(
        {
            "frame_id": [0],
            "class_id": [2],
            "x": [1.0],
            "y": [1.0],
        }
    )
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    df.write_csv(input_csv)

    runner = CliRunner()
    result = runner.invoke(
        fix_ids_module.main,
        [
            str(input_csv),
            "--output",
            str(output_csv),
            "--num-objects",
            "1",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert not output_csv.exists()


def test_fix_ids_cli_missing_columns_errors(tmp_path) -> None:
    df = pl.DataFrame({"frame_id": [0], "class_id": [2]})
    input_csv = tmp_path / "input.csv"
    df.write_csv(input_csv)

    runner = CliRunner()
    result = runner.invoke(fix_ids_module.main, [str(input_csv)])

    assert result.exit_code != 0
    assert "Missing required columns" in result.output
