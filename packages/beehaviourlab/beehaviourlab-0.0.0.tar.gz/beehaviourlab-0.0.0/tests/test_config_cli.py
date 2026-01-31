from pathlib import Path

import pytest
from click.testing import CliRunner

from beehaviourlab.config import get_config, ConfigFiles
from beehaviourlab.config import cli as config_cli


def test_config_init_writes_files(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        config_cli.init,
        ["--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert (tmp_path / "tracking_config.yaml").exists()
    assert (tmp_path / "tracking" / "custom_tracker.yaml").exists()


def test_get_config_prefers_local_config(tmp_path: Path, monkeypatch) -> None:
    local_path = tmp_path / "tracking_config.yaml"
    local_path.write_text(
        "\n".join(
            [
                "model_path: \"tracking/model/feeder_bee_YOLO.pt\"",
                "ultralytics_config: \"tracking/custom_tracker.yaml\"",
                "conf_threshold: 0.123",
                "xywh: true",
                "track: true",
                "num_objects: 5",
                "feeder_label: 1",
                "csv1_name: \"a.csv\"",
                "csv2_name: \"b.csv\"",
                "csv3_name: \"c.csv\"",
            ]
        )
    )
    monkeypatch.chdir(tmp_path)

    cfg = get_config(ConfigFiles.TRACKING)
    assert cfg.conf_threshold == 0.123
    assert cfg.csv1_name == "a.csv"


def test_get_config_uses_packaged_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = get_config(ConfigFiles.TRACKING)
    assert hasattr(cfg, "conf_threshold")
    assert hasattr(cfg, "csv1_name")
