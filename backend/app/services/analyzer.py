import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import HTTPException, status

from app.extractors.registry import registry
from app.schemas.analyzer import AnalyzerResult, MediaKind, Platform


PLATFORM_HOSTS: dict[Platform, set[str]] = {
    Platform.YOUTUBE: {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"},
    Platform.TIKTOK: {"tiktok.com", "www.tiktok.com", "vm.tiktok.com"},
    Platform.INSTAGRAM: {"instagram.com", "www.instagram.com"},
    Platform.FACEBOOK: {"facebook.com", "www.facebook.com", "fb.watch"},
    Platform.X: {"x.com", "www.x.com", "twitter.com", "www.twitter.com"},
    Platform.REDDIT: {"reddit.com", "www.reddit.com", "old.reddit.com"},
    Platform.VIMEO: {"vimeo.com", "www.vimeo.com"},
}


def _is_private_or_reserved(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return any((ip.is_private, ip.is_loopback, ip.is_link_local, ip.is_reserved, ip.is_multicast, ip.is_unspecified))


def validate_public_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=422, detail="Only public HTTP and HTTPS URLs are supported")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise HTTPException(status_code=422, detail="Local hostnames are not allowed")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise HTTPException(status_code=422, detail="The hostname could not be resolved") from exc
    if not addresses or any(_is_private_or_reserved(address) for address in addresses):
        raise HTTPException(status_code=422, detail="Private or reserved network addresses are not allowed")
    return raw_url


def detect_platform(raw_url: str) -> Platform:
    hostname = (urlparse(raw_url).hostname or "").lower().rstrip(".")
    for platform, hosts in PLATFORM_HOSTS.items():
        if hostname in hosts or any(hostname.endswith(f".{host}") for host in hosts):
            return platform
    return Platform.GENERIC


def build_preview(raw_url: str) -> AnalyzerResult:
    validate_public_url(raw_url)
    platform = detect_platform(raw_url)
    supported = platform in registry.supported_platforms()
    message = (
        "Platform detected and an authorized extractor is configured."
        if supported
        else "Platform detected, but no platform-approved extractor is configured yet."
    )
    return AnalyzerResult(url=raw_url, platform=platform, content_kind=MediaKind.UNKNOWN, supported=supported, message=message)
