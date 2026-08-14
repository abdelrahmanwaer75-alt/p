from app.schemas.downloads import DownloadStatus


ALLOWED_TRANSITIONS: dict[DownloadStatus, frozenset[DownloadStatus]] = {
    DownloadStatus.QUEUED: frozenset({DownloadStatus.STARTING, DownloadStatus.CANCELLED, DownloadStatus.FAILED}),
    DownloadStatus.STARTING: frozenset({DownloadStatus.DOWNLOADING, DownloadStatus.CANCELLING, DownloadStatus.FAILED, DownloadStatus.QUEUED}),
    DownloadStatus.DOWNLOADING: frozenset({DownloadStatus.COMPLETED, DownloadStatus.CANCELLING, DownloadStatus.FAILED, DownloadStatus.QUEUED}),
    DownloadStatus.PAUSED: frozenset({DownloadStatus.QUEUED, DownloadStatus.CANCELLING}),
    DownloadStatus.CANCELLING: frozenset({DownloadStatus.CANCELLED, DownloadStatus.FAILED}),
    DownloadStatus.COMPLETED: frozenset(),
    DownloadStatus.FAILED: frozenset({DownloadStatus.QUEUED}),
    DownloadStatus.CANCELLED: frozenset(),
}


def can_transition(current: DownloadStatus, target: DownloadStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def require_transition(current: DownloadStatus, target: DownloadStatus) -> None:
    if current == target:
        return
    if not can_transition(current, target):
        raise ValueError(f"Invalid download state transition: {current.value} -> {target.value}")
