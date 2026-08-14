class FeatureNotAvailableError(RuntimeError):
    """Raised when a requested adapter or capability is not implemented."""


class ResourceNotFoundError(LookupError):
    """Raised when an owned resource cannot be found."""


__all__ = ["FeatureNotAvailableError", "ResourceNotFoundError"]
