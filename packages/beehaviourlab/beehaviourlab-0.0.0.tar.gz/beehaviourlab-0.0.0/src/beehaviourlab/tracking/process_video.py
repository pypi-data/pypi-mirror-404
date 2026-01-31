from pathlib import Path
import click

from beehaviourlab.tracking import (
    save_bboxes_to_file,
    fix_ids_df,
    extract_flow_info_df,
)
from beehaviourlab.config import ConfigFiles, get_config

cfg = get_config(ConfigFiles.TRACKING)


@click.command()
@click.option(
    "--input",
    "input_file",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the input video file.",
)
@click.option(
    "--output",
    "output_dir",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory to store output CSV files.",
)
def main(input_file: Path, output_dir: Path) -> None:
    """
    Video processing script that creates CSV files with object tracking information.

    Args:
        input_file (Path): Path to the input video file.
        output_dir (Path): Directory to store output CSV files.

    Returns:
        None
    """
    click.echo(f"Input video file: {input_file}")
    click.echo(f"Output directory: {output_dir.absolute()}")

    output_dir.mkdir(parents=True, exist_ok=True)

    click.echo("Running YOLO tracking...")
    output_csv_1 = output_dir / f"{input_file.stem}_{cfg.csv1_name}"
    df = save_bboxes_to_file(
        cfg.model_path,
        str(input_file),
        str(output_csv_1),
        cfg.conf_threshold,
        cfg.xywh,
        cfg.track,
    )
    click.echo(f"Output raw CSV file to {output_csv_1}")

    click.echo("Fixing IDs...")
    output_csv_2 = output_dir / f"{input_file.stem}_{cfg.csv2_name}"
    df = fix_ids_df(df, cfg.num_objects)
    df.write_csv(output_csv_2)
    click.echo(f"Saved fixed IDs CSV to {output_csv_2}")

    click.echo("Extracting flow info...")
    output_csv_3 = output_dir / f"{input_file.stem}_{cfg.csv3_name}"
    df = extract_flow_info_df(df)
    df.write_csv(output_csv_3)
    click.echo(f"Saved velocity CSV to {output_csv_3}")
    
    click.echo("Done!")


if __name__ == "__main__":
    main()
