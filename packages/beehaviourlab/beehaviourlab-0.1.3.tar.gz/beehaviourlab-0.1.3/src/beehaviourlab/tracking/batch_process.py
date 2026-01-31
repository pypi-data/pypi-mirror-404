from pathlib import Path
from typing import Iterable, Optional

import click

from beehaviourlab.tracking import process_video


VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".mpg", ".mpeg"}


def _iter_videos(root: Path, name_filter: Optional[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        if name_filter and name_filter not in path.name:
            continue
        yield path


@click.command()
@click.option(
    "--input-dir",
    "input_dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Directory to search for videos (recursively).",
)
@click.option(
    "--output-dir-name",
    default="tracking_outputs",
    show_default=True,
    help="Directory name to create alongside each video for outputs.",
)
@click.option(
    "--filter",
    "name_filter",
    default=None,
    help="Only process videos whose filename contains this string.",
)
def main(input_dir: Path, output_dir_name: str, name_filter: Optional[str]) -> None:
    """Run the tracking pipeline for every video in a directory tree."""
    videos = sorted(_iter_videos(input_dir, name_filter))
    if not videos:
        click.echo("No matching videos found.")
        return

    click.echo(f"Found {len(videos)} video(s).")
    seen_by_dir: dict[Path, set[str]] = {}
    for video in videos:
        stems = seen_by_dir.setdefault(video.parent, set())
        if video.stem in stems:
            click.echo(
                f"Warning: skipping '{video}' because a video with the same name was already processed."
            )
            continue
        stems.add(video.stem)
        output_dir = video.parent / output_dir_name / video.stem
        click.echo(f"\nProcessing: {video}")
        click.echo(f"Output dir: {output_dir}")
        process_video.main.callback(video, output_dir)
