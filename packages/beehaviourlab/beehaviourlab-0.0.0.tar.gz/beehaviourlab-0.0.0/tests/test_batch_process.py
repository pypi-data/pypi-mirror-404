from pathlib import Path

from click.testing import CliRunner

from beehaviourlab.tracking import batch_process


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("stub")


def test_batch_process_processes_videos_and_writes_per_stem_dirs(
    tmp_path, monkeypatch
) -> None:
    _touch(tmp_path / "a.mp4")
    _touch(tmp_path / "b.mov")

    calls = []

    def fake_callback(video_path, output_dir):
        calls.append((video_path, output_dir))

    monkeypatch.setattr(batch_process.process_video.main, "callback", fake_callback)

    runner = CliRunner()
    result = runner.invoke(
        batch_process.main,
        ["--input-dir", str(tmp_path), "--output-dir-name", "tracking_outputs"],
    )

    assert result.exit_code == 0
    assert len(calls) == 2
    assert calls[0][1] == tmp_path / "tracking_outputs" / calls[0][0].stem
    assert calls[1][1] == tmp_path / "tracking_outputs" / calls[1][0].stem


def test_batch_process_filters_by_name(tmp_path, monkeypatch) -> None:
    _touch(tmp_path / "keep_this.mp4")
    _touch(tmp_path / "skip_this.mp4")

    calls = []

    def fake_callback(video_path, output_dir):
        calls.append(video_path)

    monkeypatch.setattr(batch_process.process_video.main, "callback", fake_callback)

    runner = CliRunner()
    result = runner.invoke(
        batch_process.main,
        ["--input-dir", str(tmp_path), "--filter", "keep"],
    )

    assert result.exit_code == 0
    assert calls == [tmp_path / "keep_this.mp4"]


def test_batch_process_skips_duplicate_stems_per_directory(tmp_path, monkeypatch) -> None:
    _touch(tmp_path / "same.mp4")
    _touch(tmp_path / "same.mov")

    calls = []

    def fake_callback(video_path, output_dir):
        calls.append(video_path)

    monkeypatch.setattr(batch_process.process_video.main, "callback", fake_callback)

    runner = CliRunner()
    result = runner.invoke(batch_process.main, ["--input-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0].stem == "same"
    assert "Warning: skipping" in result.output


def test_batch_process_allows_same_stem_in_different_dirs(
    tmp_path, monkeypatch
) -> None:
    _touch(tmp_path / "dir1" / "same.mp4")
    _touch(tmp_path / "dir2" / "same.mov")

    calls = []

    def fake_callback(video_path, output_dir):
        calls.append(video_path)

    monkeypatch.setattr(batch_process.process_video.main, "callback", fake_callback)

    runner = CliRunner()
    result = runner.invoke(batch_process.main, ["--input-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert {p.parent.name for p in calls} == {"dir1", "dir2"}
