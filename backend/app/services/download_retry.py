from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadRetryPolicy:
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0

    def next_attempt(self, current_retry_count: int) -> int:
        return current_retry_count + 1

    def should_retry(self, current_retry_count: int) -> bool:
        return self.next_attempt(current_retry_count) <= self.max_retries

    def delay(self, attempt: int) -> float:
        return min(self.base_delay_seconds * (2 ** max(attempt - 1, 0)), self.max_delay_seconds)
