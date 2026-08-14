from pydantic import HttpUrl, TypeAdapter


_http_url_adapter = TypeAdapter(HttpUrl)


def as_http_url(value: str | HttpUrl) -> HttpUrl:
    return _http_url_adapter.validate_python(value)


def as_optional_http_url(value: str | HttpUrl | None) -> HttpUrl | None:
    return None if value is None else as_http_url(value)
