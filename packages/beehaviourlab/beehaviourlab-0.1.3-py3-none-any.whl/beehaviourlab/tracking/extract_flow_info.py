#!/usr/bin/env python3

import sys
import polars as pl
import click
from pathlib import Path
from typing import Optional


def extract_flow_info(df: pl.DataFrame) -> pl.DataFrame:
    """
    Extracts flow information from the DataFrame, including velocity and speed.

    Computes movement vectors (dx, dy), instantaneous speed, and smoothed speed
    for each tracked object across frames. Handles both corner coordinate format
    (x1, y1, x2, y2) and centre coordinate format (x, y).

    Args:
        df (pl.DataFrame): The DataFrame containing bounding box data with columns:
            - stable_id: Object identifier
            - frame_id: Frame number
            - Either (x, y) centre coordinates OR (x1, y1, x2, y2) corner coordinates

    Returns:
        pl.DataFrame: The DataFrame with additional flow information columns:
            - dx, dy: Movement vectors between consecutive frames
            - speed: Instantaneous speed (Euclidean distance moved)
            - speed_smoothed: Median-filtered speed over 5-frame window
            - x, y: Centre coordinates (converted from corners if needed)
            - w, h: Width and height (computed from corners if needed)

    Note:
        - Speed calculations use frame-to-frame differences within each stable_id
        - Missing values are filled with 0
        - Smoothing uses a rolling median filter with window size 5
        - Empty DataFrames will cause the function to exit with an error message
    """
    if df.is_empty():
        print("No objects detected for flow info! Ending processing")
        sys.exit(0)

    if "x1" in df.columns:
        # First, create width and height columns
        df = df.with_columns(
            [
                (pl.col("x2") - pl.col("x1")).alias("w"),
                (pl.col("y2") - pl.col("y1")).alias("h"),
            ]
        )
        # Then, create centre coordinates using the newly created w and h columns
        df = df.with_columns(
            [
                (pl.col("x1") + pl.col("w") / 2).alias("x"),
                (pl.col("y1") + pl.col("h") / 2).alias("y"),
            ]
        )

    df = df.sort(["stable_id", "frame_id"])

    df = df.with_columns(
        [
            (pl.col("x") - pl.col("x").shift(1)).over(["stable_id"]).alias("dx"),
            (pl.col("y") - pl.col("y").shift(1)).over(["stable_id"]).alias("dy"),
        ]
    )

    df = df.with_columns(
        [(pl.col("dx").pow(2) + pl.col("dy").pow(2)).sqrt().alias("speed")]
    )

    df = df.fill_null(0)

    df = df.with_columns(
        [
            pl.col("speed")
            .rolling_map(lambda s: s.median(), window_size=5, min_samples=1)
            .alias("speed_smoothed")
        ]
    )

    return df


# CLI Interface
@click.command()
@click.argument("input_csv", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output CSV file path. If not specified, will overwrite input file.",
)
@click.option("--dry-run", is_flag=True, help="Show statistics without saving output")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed progress information"
)
def main(input_csv: Path, output: Optional[Path], dry_run: bool, verbose: bool) -> None:
    """Extract flow information from object tracking data.

    This script computes movement vectors, instantaneous speed, and smoothed speed
    for tracked objects across video frames. It handles both corner coordinate
    and centre coordinate input formats.

    INPUT_CSV: Path to the CSV file containing object tracking data.

    The CSV file must contain the following columns:
    - stable_id: Object identifier for tracking across frames
    - frame_id: Frame number for temporal ordering
    - Coordinates in one of these formats:
      * Centre format: x, y (centre coordinates)
      * Corner format: x1, y1, x2, y2 (bounding box corners)

    Flow Information Computed:
    - dx, dy: Movement vectors between consecutive frames
    - speed: Instantaneous speed (Euclidean distance per frame)
    - speed_smoothed: Median-filtered speed over 5-frame window

    Examples:
        # Basic flow extraction
        python extract_flow_info.py tracking_data.csv

        # Custom output file
        python extract_flow_info.py tracking_data.csv -o flow_data.csv

        # Dry run to preview statistics
        python extract_flow_info.py tracking_data.csv --dry-run --verbose
    """
    if verbose:
        click.echo(f"Loading tracking data from: {input_csv}")

    try:
        # Load the CSV file
        df = pl.read_csv(input_csv)

        if verbose:
            click.echo(
                f"Loaded {len(df):,} detections from {df['frame_id'].n_unique():,} frames"
            )

        # Validate required columns
        required_cols = ["stable_id", "frame_id"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise click.ClickException(
                f"Missing required columns: {missing_cols}\n"
                f"Required columns: {required_cols}"
            )

        # Check coordinate format
        has_centre_coords = "x" in df.columns and "y" in df.columns
        has_corner_coords = all(col in df.columns for col in ["x1", "y1", "x2", "y2"])

        if not (has_centre_coords or has_corner_coords):
            raise click.ClickException(
                "Missing coordinate columns. Need either:\n"
                "  - Centre format: x, y\n"
                "  - Corner format: x1, y1, x2, y2"
            )

        coord_format = (
            "corner" if has_corner_coords and not has_centre_coords else "centre"
        )
        if verbose:
            click.echo(f"Detected coordinate format: {coord_format}")

        # Show input statistics
        if verbose:
            unique_objects = df["stable_id"].n_unique()
            unique_frames = df["frame_id"].n_unique()
            frame_range = f"{df['frame_id'].min()} to {df['frame_id'].max()}"
            avg_detections_per_frame = len(df) / unique_frames
            click.echo(f"Unique objects: {unique_objects}")
            click.echo(f"Frame range: {frame_range}")
            click.echo(f"Average detections per frame: {avg_detections_per_frame:.1f}")

        # Perform flow extraction
        if verbose:
            click.echo("Computing movement vectors and speed...")

        df_flow = extract_flow_info(df)

        # Calculate statistics
        speed_stats = df_flow.select(["speed", "speed_smoothed"]).describe()
        movement_count = len(df_flow.filter(pl.col("speed") > 0))
        stationary_count = len(df_flow.filter(pl.col("speed") == 0))

        # Display results
        click.echo("\nFlow Extraction Results:")
        click.echo(f"  Total data points:    {len(df_flow):,}")
        click.echo(
            f"  Movement detected:    {movement_count:,} ({movement_count / len(df_flow) * 100:.1f}%)"
        )
        click.echo(
            f"  Stationary points:    {stationary_count:,} ({stationary_count / len(df_flow) * 100:.1f}%)"
        )

        if verbose:
            click.echo("\nSpeed Statistics:")
            print(speed_stats)

            # Show per-object movement statistics
            object_stats = (
                df_flow.group_by("stable_id")
                .agg(
                    [
                        pl.col("speed").mean().alias("avg_speed"),
                        pl.col("speed").max().alias("max_speed"),
                        pl.col("speed_smoothed").mean().alias("avg_speed_smoothed"),
                        (pl.col("speed") > 0).sum().alias("movement_frames"),
                        pl.len().alias("total_frames"),
                    ]
                )
                .with_columns(
                    (pl.col("movement_frames") / pl.col("total_frames") * 100).alias(
                        "movement_pct"
                    )
                )
                .sort("stable_id")
            )

            click.echo("\nPer-object movement statistics:")
            click.echo("  Object ID | Avg Speed | Max Speed | Movement % | Frames")
            click.echo("  ----------|-----------|-----------|------------|-------")
            for row in object_stats.rows(named=True):
                sid = row["stable_id"]
                avg_spd = row["avg_speed"]
                max_spd = row["max_speed"]
                mov_pct = row["movement_pct"]
                frames = row["total_frames"]
                click.echo(
                    f"  {sid:>8} | {avg_spd:>9.2f} | {max_spd:>9.2f} | {mov_pct:>9.1f}% | {frames:>6}"
                )

        if not dry_run:
            # Determine output path
            output_path = output if output else input_csv

            if verbose:
                click.echo(f"\nSaving flow data to: {output_path}")

            # Save the flow data
            df_flow.write_csv(output_path)
            click.echo(f"✅ Successfully saved {len(df_flow):,} rows to {output_path}")
        else:
            click.echo("\n🔍 Dry run complete - no files were modified")

    except Exception as e:
        raise click.ClickException(f"Error processing file: {e}")


if __name__ == "__main__":
    main()
