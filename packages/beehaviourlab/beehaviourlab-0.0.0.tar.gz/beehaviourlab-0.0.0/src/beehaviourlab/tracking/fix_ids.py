#!/usr/bin/env python3

import click
import polars as pl
import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
from beehaviourlab.config import ConfigFiles, get_config

cfg = get_config(ConfigFiles.TRACKING)


def filter_out_feeder(df: pl.DataFrame) -> pl.DataFrame:
    """
    Filters out feeder objects from the DataFrame.

    Args:
        df (pl.DataFrame): The DataFrame containing bounding box data.

    Returns:
        pl.DataFrame: The filtered DataFrame.
    """
    return df.filter(pl.col("class_id") != cfg.feeder_label)


def fix_ids(df: pl.DataFrame, num_objects: int) -> pl.DataFrame:
    """
    Fixes the IDs in the DataFrame by assigning stable IDs to objects across frames.

    Uses the Hungarian algorithm to maintain consistent object identities across frames
    by minimising the total movement distance between consecutive frame assignments.

    Args:
        df (pl.DataFrame): The DataFrame containing bounding box data with columns:
            - frame_id: Frame number
            - x, y: Object centre coordinates
            - Other detection columns (class_id, conf, etc.)
        num_objects (int): Maximum number of objects to track with stable IDs.

    Returns:
        pl.DataFrame: The DataFrame with fixed stable IDs and interpolated positions
            for missing detections. Includes a new 'stable_id' column with consistent
            object identifiers from 1 to num_objects.

    Note:
        - Missing detections are filled with interpolated positions
        - Objects are assigned stable IDs from 1 to num_objects
        - Assignment is based on minimising Euclidean distance between frames
    """
    if df.is_empty():
        cols = list(df.columns)
        if "stable_id" not in cols:
            cols += ["stable_id"]
        # preserve dtypes where possible
        schema = {c: df.schema.get(c, pl.Float64) for c in cols}
        schema["stable_id"] = pl.Int64
        return pl.DataFrame(
            {c: pl.Series(name=c, values=[], dtype=schema[c]) for c in cols}
        )

    df = filter_out_feeder(df)

    df = df.sort(["frame_id"])

    stable_rows: List[Dict[str, Optional[float]]] = []
    stable_id_list: List[int] = list(range(1, num_objects + 1))
    stable_positions: Dict[int, Optional[Tuple[float, float]]] = {
        sid: None for sid in stable_id_list
    }

    all_columns: List[str] = df.columns
    if "stable_id" not in all_columns:
        all_columns += ["stable_id"]

    frames_list: List[int] = (
        df.select(pl.col("frame_id")).unique().sort("frame_id").to_series().to_list()
    )

    for f in frames_list:
        subdf: pl.DataFrame = df.filter(pl.col("frame_id") == f)

        x_vals: np.ndarray = subdf["x"].to_numpy()
        y_vals: np.ndarray = subdf["y"].to_numpy()
        this_frame_count: int = len(x_vals)

        cost: np.ndarray = np.zeros((num_objects, this_frame_count), dtype=np.float32)

        for i_row, sid in enumerate(stable_id_list):
            old_pos: Optional[Tuple[float, float]] = stable_positions[sid]
            if old_pos is None:
                old_x, old_y = 1e9, 1e9
            else:
                old_x, old_y = old_pos

            for j_col in range(this_frame_count):
                dx: float = x_vals[j_col] - old_x
                dy: float = y_vals[j_col] - old_y
                cost[i_row, j_col] = np.sqrt(dx * dx + dy * dy)

        if this_frame_count > 0:
            row_idx, col_idx = linear_sum_assignment(cost)
        else:
            row_idx, col_idx = [], []

        matched_sids: Set[int] = set()
        matched_detections: Set[int] = set()

        for i_row, j_col in zip(row_idx, col_idx):
            sid: int = stable_id_list[i_row]
            matched_sids.add(sid)
            matched_detections.add(j_col)

            new_x: float = x_vals[j_col]
            new_y: float = y_vals[j_col]
            stable_positions[sid] = (new_x, new_y)

            row_data: Dict[str, Optional[float]] = subdf.slice(j_col, 1).to_dicts()[0]
            row_data["stable_id"] = sid
            stable_rows.append(row_data)

        unmatched_sids: Set[int] = set(stable_id_list) - matched_sids
        for sid in unmatched_sids:
            blank_row: Dict[str, Optional[float]] = {col: None for col in all_columns}
            blank_row["frame_id"] = f
            blank_row["stable_id"] = sid

            old_pos = stable_positions[sid]
            if old_pos is not None:
                blank_row["x"] = old_pos[0]
                blank_row["y"] = old_pos[1]

            stable_rows.append(blank_row)

    df_out: pl.DataFrame = pl.DataFrame(stable_rows)
    df_out = df_out.sort(["frame_id", "stable_id"])

    click.echo(f"rows: {len(stable_rows)}")
    if len(stable_rows) == 0:
        click.echo(f"Input df was empty: {df.is_empty()}")
        click.echo(f"frames_list: {frames_list}")
    else:
        click.echo(f"df_out columns: {pl.DataFrame(stable_rows).columns}")
    return df_out


# CLI Interface
@click.command()
@click.argument("input_csv", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output CSV file path. If not specified, will overwrite input file.",
)
@click.option(
    "--num-objects",
    "-n",
    type=int,
    default=5,
    show_default=True,
    help="Maximum number of objects to track with stable IDs",
)
@click.option("--dry-run", is_flag=True, help="Show statistics without saving output")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed progress information"
)
def main(
    input_csv: Path,
    output: Optional[Path],
    num_objects: int,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Fix object IDs in tracking data using the Hungarian algorithm.

    This script assigns stable, consistent IDs to tracked objects across frames
    by minimising the total movement distance between consecutive assignments.
    Missing detections are interpolated based on last known positions.

    INPUT_CSV: Path to the CSV file containing object tracking data.

    The CSV file must contain the following columns:
    - frame_id: Frame number
    - x, y: Object centre coordinates
    - Additional columns will be preserved (class_id, conf, w, h, etc.)

    Algorithm Details:
    - Uses the Hungarian algorithm (linear_sum_assignment) for optimal assignment
    - Minimises total Euclidean distance between consecutive frame positions
    - Handles missing detections by interpolating last known positions
    - Assigns stable_id values from 1 to NUM_OBJECTS

    Examples:
        # Basic ID fixing with default number of objects
        python fix_ids.py tracking_data.csv

        # Custom output file and number of objects
        python fix_ids.py tracking_data.csv -o fixed_tracking.csv --num-objects 10

        # Dry run to preview statistics
        python fix_ids.py tracking_data.csv --dry-run --verbose
    """
    if verbose:
        click.echo(f"Loading tracking data from: {input_csv}")
        click.echo(f"Maximum objects to track: {num_objects}")

    try:
        # Load the CSV file
        df = pl.read_csv(input_csv)

        if verbose:
            click.echo(
                f"Loaded {len(df):,} detections from {df['frame_id'].n_unique():,} frames"
            )

        # Validate required columns
        required_cols = ["frame_id", "x", "y"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise click.ClickException(
                f"Missing required columns: {missing_cols}\n"
                f"Required columns: {required_cols}"
            )

        # Show input statistics
        if verbose:
            unique_frames = df["frame_id"].n_unique()
            frame_range = f"{df['frame_id'].min()} to {df['frame_id'].max()}"
            avg_detections_per_frame = len(df) / unique_frames
            click.echo(f"Frame range: {frame_range}")
            click.echo(f"Average detections per frame: {avg_detections_per_frame:.1f}")

            # Check if stable_id already exists
            if "stable_id" in df.columns:
                existing_stable_ids = df["stable_id"].n_unique()
                click.echo(
                    f"Found {existing_stable_ids} existing stable IDs (will be overwritten)"
                )

        # Perform ID fixing
        if verbose:
            click.echo("Applying Hungarian algorithm for ID assignment...")

        df_fixed = fix_ids(df, num_objects)

        # Calculate statistics
        total_assignments = len(df_fixed.filter(pl.col("x").is_not_null()))
        total_interpolations = len(df_fixed.filter(pl.col("x").is_null()))

        # Display results
        click.echo("\nID Fixing Results:")
        click.echo(f"  Total stable IDs:     {num_objects}")
        click.echo(f"  Assigned detections:  {total_assignments:,}")
        click.echo(f"  Interpolated gaps:    {total_interpolations:,}")
        click.echo(f"  Total output rows:    {len(df_fixed):,}")

        if verbose and total_interpolations > 0:
            # Show per-stable-ID statistics
            stable_id_stats = (
                df_fixed.group_by("stable_id")
                .agg(
                    [
                        pl.col("x").is_not_null().sum().alias("detections"),
                        pl.col("x").is_null().sum().alias("interpolations"),
                        pl.len().alias("total_frames"),
                    ]
                )
                .sort("stable_id")
            )

            click.echo("\nPer-object statistics:")
            click.echo("  Stable ID | Detections | Interpolations | Total Frames")
            click.echo("  ----------|------------|----------------|-------------")
            for row in stable_id_stats.rows(named=True):
                sid = row["stable_id"]
                det = row["detections"]
                interp = row["interpolations"]
                total = row["total_frames"]
                click.echo(f"  {sid:>8} | {det:>10} | {interp:>14} | {total:>11}")

        if not dry_run:
            # Determine output path
            output_path = output if output else input_csv

            if verbose:
                click.echo(f"\nSaving fixed tracking data to: {output_path}")

            # Save the fixed data
            df_fixed.write_csv(output_path)
            click.echo(f"✅ Successfully saved {len(df_fixed):,} rows to {output_path}")
        else:
            click.echo("\n🔍 Dry run complete - no files were modified")

    except Exception as e:
        raise click.ClickException(f"Error processing file: {e}")


if __name__ == "__main__":
    main()
