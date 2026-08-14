from pathlib import Path
from uuid import UUID

import pytest

from app.media import FfmpegCommandBuilder, MediaStorage


def test_media_output_is_inside_storage_root(tmp_path) -> None:
    task_id = UUID("11111111-1111-1111-1111-111111111111")
    output = MediaStorage(str(tmp_path)).output_for(task_id, "mp4")
    assert output.path == Path(tmp_path).resolve() / f"{task_id}.mp4"


def test_media_format_is_allowlisted(tmp_path) -> None:
    with pytest.raises(ValueError):
        MediaStorage(str(tmp_path)).output_for(UUID(int=1), "../../etc/passwd")


def test_ffmpeg_builder_returns_argument_list_without_shell(tmp_path) -> None:
    task_id = UUID(int=2)
    output = MediaStorage(str(tmp_path)).output_for(task_id, "mp4")
    command = FfmpegCommandBuilder().build_remux(Path("/tmp/input.mp4"), output)
    assert command[0] == "ffmpeg"
    assert "-nostdin" in command
    assert all(";" not in item and "&&" not in item for item in command)
