import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import HTTPException

from app.core.typing import as_http_url
from app.extractors.registry import registry
from app.schemas.analyzer import AnalyzerResult, MediaKind, Platform


PLATFORM_HOSTS: dict[Platform, set[str]] = {
    Platform.REDDIT: {"reddit.com", "www.reddit.com", "old.reddit.com"},
    Platform.VIMEO: {"vimeo.com", "www.vimeo.com"},
    Platform.DAILYMOTION: {"dailymotion.com", "www.dailymotion.com", "dai.ly"},
    Platform.SOUNDCLOUD: {"soundcloud.com", "www.soundcloud.com"},
    Platform.TWITCH: {"twitch.tv", "www.twitch.tv"},
}

METADATA_HOSTNAMES = {
    "169.254.169.254",
    "metadata.google.internal",
    "metadata.google.com",
    "instance-data.ec2.internal",
}


def _is_private_or_reserved(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return any(
        (
            not ip.is_global,
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_reserved,
            ip.is_multicast,
            ip.is_unspecified,
        )
    )


def resolve_public_addresses(hostname: str, port: int) -> set[str]:
    """Resolve every address and reject if any answer is unsafe.

    Adapters must use this same resolution result when opening a connection rather than
    resolving the hostname again. That prevents a DNS answer from changing between
    validation and the eventual outbound connection.
    """
    try:
        addresses: set[str] = {
            str(item[4][0])
            for item in socket.getaddrinfo(
                hostname,
                port,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
        }
    except (socket.gaierror, socket.timeout) as exc:
        raise HTTPException(status_code=422, detail="The hostname could not be resolved") from exc
    if not addresses or any(_is_private_or_reserved(address) for address in addresses):
        raise HTTPException(status_code=422, detail="Private or reserved network addresses are not allowed")
    return addresses


def validate_public_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=422, detail="Only public HTTP and HTTPS URLs are supported")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="URLs with embedded credentials are not allowed")

    hostname = parsed.hostname.rstrip(".").lower()
    if (
        hostname in {"localhost", "localhost.localdomain"}
        or hostname.endswith((".local", ".localhost", ".internal"))
        or hostname in METADATA_HOSTNAMES
    ):
        raise HTTPException(status_code=422, detail="Local and metadata hostnames are not allowed")

    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        literal_ip = None
    if literal_ip is not None:
        if _is_private_or_reserved(str(literal_ip)):
            raise HTTPException(status_code=422, detail="Private or reserved network addresses are not allowed")
    else:
        resolve_public_addresses(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    return raw_url


def detect_platform(raw_url: str) -> Platform:
    hostname = (urlparse(raw_url).hostname or "").lower().rstrip(".")
    for platform, hosts in PLATFORM_HOSTS.items():
        if hostname in hosts or any(hostname.endswith(f".{host}") for host in hosts):
            return platform
    return Platform.GENERIC


def _generic_result(raw_url: str) -> AnalyzerResult:
    return AnalyzerResult(
        url=as_http_url(raw_url),
        platform=Platform.GENERIC,
        content_kind=MediaKind.UNKNOWN,
        supported=False,
        formats=[],
        audio_formats=[],
        video_formats=[],
        restrictions=["unsupported_platform"],
        limitations=["platform_not_allowed", "metadata_unavailable", "formats_unavailable"],
        message="The URL is valid, but its platform is outside Vidora's approved platform allowlist.",
    )


async def build_preview(raw_url: str, *, authorized: bool = False) -> AnalyzerResult:
    validate_public_url(raw_url)
    platform = detect_platform(raw_url)
    extractor = registry.get(platform)
    if extractor is None or not registry.is_allowed(platform):
        return _generic_result(raw_url)
    return await extractor.analyze(raw_url, authorized=authorized)
