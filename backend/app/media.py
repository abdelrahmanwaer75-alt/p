from dataclasses import dataclass
from pathlib import Path
from uuid import UUID


ALLOWED_OUTPUT_FORMATS = {"mp4", "mkv", "webm", "mp3", "m4a"}


@dataclass(frozen=True)
class MediaOutput:
    task_id: UUID
    path: Path
    format_id: str


class MediaStorage:
    def __init__(self, root: str = "backend/data/media") -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def output_for(self, task_id: UUID, format_id: str) -> MediaOutput:
        normalized = format_id.lower().strip()
        if normalized not in ALLOWED_OUTPUT_FORMATS:
            raise ValueError(f"Unsupported output format: {format_id}")
        path = (self.root / f"{task_id}.{normalized}").resolve()
        if self.root not in path.parents:
            raise ValueError("Output path escapes the media root")
        return MediaOutput(task_id=task_id, path=path, format_id=normalized)


class FfmpegCommandBuilder:
    def build_remux(self, input_path: Path, output: MediaOutput) -> list[str]:
        if not input_path.is_absolute():
            raise ValueError("FFmpeg input path must be absolute")
        if not output.path.is_absolute():
            raise ValueError("FFmpeg output path must be absolute")
        return [
            "ffmpeg",
            "-hide_banner",
            "-nostdin",
            "-y",
            "-i",
            str(input_path),
            "-map",
            "0",
            "-c",
            "copy",
            str(output.path),
        ]
