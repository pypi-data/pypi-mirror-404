from click.testing import CliRunner

from beehaviourlab.cli import bee


def test_bee_help_lists_track_group() -> None:
    runner = CliRunner()
    result = runner.invoke(bee, ["--help"])
    assert result.exit_code == 0
    assert "track" in result.output


def test_track_help_lists_subcommands() -> None:
    runner = CliRunner()
    result = runner.invoke(bee, ["track", "--help"])
    assert result.exit_code == 0
    for command in (
        "run-pipeline",
        "run-yolo",
        "fix-ids",
        "extract-flow",
        "visualise-tracking",
    ):
        assert command in result.output


def test_track_subcommand_help_works() -> None:
    runner = CliRunner()
    subcommands = [
        "run-pipeline",
        "run-yolo",
        "fix-ids",
        "extract-flow",
        "visualise-tracking",
    ]
    for command in subcommands:
        result = runner.invoke(bee, ["track", command, "--help"])
        assert result.exit_code == 0, result.output
