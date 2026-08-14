import pytest

from app.core.security import middleware


@pytest.fixture(autouse=True)
def reset_local_rate_limit_state():
    middleware.rate_limiter._local.clear()
    yield
    middleware.rate_limiter._local.clear()
