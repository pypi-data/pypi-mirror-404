from importlib import resources
from pathlib import Path

import click


@click.command()
def print_tracking() -> None:
    """Print the default tracking_config.yaml to stdout."""
    resource = resources.files("beehaviourlab.config").joinpath("tracking_config.yaml")
    with resources.as_file(resource) as path:
        click.echo(path.read_text())


@click.command()
@click.option(
    "--output-dir",
    default=".",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory to write config files into.",
)
def init(output_dir: Path) -> None:
    """Write default config files into the chosen directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    tracking_path = output_dir / "tracking_config.yaml"
    tracker_dir = output_dir / "tracking"
    tracker_dir.mkdir(parents=True, exist_ok=True)
    tracker_path = tracker_dir / "custom_tracker.yaml"

    tracking_resource = resources.files("beehaviourlab.config").joinpath(
        "tracking_config.yaml"
    )
    tracker_resource = resources.files("beehaviourlab.tracking").joinpath(
        "custom_tracker.yaml"
    )

    with resources.as_file(tracking_resource) as path:
        tracking_path.write_text(path.read_text())
    with resources.as_file(tracker_resource) as path:
        tracker_path.write_text(path.read_text())

    click.echo(f"Wrote {tracking_path}")
    click.echo(f"Wrote {tracker_path}")
