"""Shared network-boundary validation for model-callable HTTP tools."""

from __future__ import annotations

import ipaddress
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Iterable


DEFAULT_HTTP_TIMEOUT = 30.0
MAX_HTTP_TIMEOUT = 60.0
MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 200_000

Resolver = Callable[..., Iterable[tuple[Any, ...]]]


@dataclass(frozen=True, slots=True)
class ValidatedHttpTarget:
    """Canonical public HTTP target and the addresses observed at validation."""

    url: str
    scheme: str
    hostname: str
    port: int
    addresses: tuple[str, ...]


def _require_global_address(address: str) -> str:
    try:
        parsed = ipaddress.ip_address(address.split("%", 1)[0])
    except ValueError as exc:
        raise ValueError(f"resolved address is invalid: {address}") from exc
    if not parsed.is_global:
        raise ValueError(f"non-public network address is blocked: {parsed.compressed}")
    return parsed.compressed


def validate_public_http_url(
    url: str,
    *,
    resolver: Resolver = socket.getaddrinfo,
) -> ValidatedHttpTarget:
    """Validate an HTTP URL and require every resolved address to be public."""

    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")
    normalized = url.strip()
    try:
        parsed = urllib.parse.urlsplit(normalized)
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"invalid URL: {exc}") from exc
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError("url scheme must be http or https")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("credentials embedded in URLs are not allowed")
    hostname = (parsed.hostname or "").rstrip(".").lower()
    if not hostname:
        raise ValueError("url must include a hostname")
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("localhost is blocked")

    effective_port = port or (443 if scheme == "https" else 80)
    addresses: set[str] = set()
    try:
        literal = ipaddress.ip_address(hostname.split("%", 1)[0])
    except ValueError:
        try:
            results = resolver(hostname, effective_port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError(f"hostname resolution failed: {hostname}: {exc}") from exc
        for result in results:
            sockaddr = result[4]
            if sockaddr:
                addresses.add(_require_global_address(str(sockaddr[0])))
    else:
        addresses.add(_require_global_address(literal.compressed))
    if not addresses:
        raise ValueError(f"hostname resolved to no usable addresses: {hostname}")

    return ValidatedHttpTarget(
        url=normalized,
        scheme=scheme,
        hostname=hostname,
        port=effective_port,
        addresses=tuple(sorted(addresses)),
    )


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler that revalidates every destination."""

    def __init__(self, *, max_redirects: int = MAX_REDIRECTS) -> None:
        super().__init__()
        self.max_redirects = max_redirects
        self.redirect_count = 0

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        self.redirect_count += 1
        if self.redirect_count > self.max_redirects:
            raise urllib.error.HTTPError(
                req.full_url,
                code,
                f"too many redirects (>{self.max_redirects})",
                headers,
                fp,
            )
        validate_public_http_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def build_safe_http_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(SafeRedirectHandler())


def read_bounded(response: Any, limit: int = MAX_RESPONSE_BYTES) -> tuple[bytes, bool]:
    """Read at most ``limit`` bytes and report whether the body was truncated."""

    data = response.read(limit + 1)
    return data[:limit], len(data) > limit
