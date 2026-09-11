from __future__ import annotations

import io
import urllib.request
from pathlib import Path

import pytest

from minicode.network_safety import SafeRedirectHandler, read_bounded, validate_public_http_url
from minicode.permissions import PermissionManager
from minicode.tooling import ToolContext
from minicode.tools.http_utils import _run_http_request, _validate_http_request
from minicode.tools.web_fetch import _is_safe_url


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://localhost/",
        "http://127.0.0.1/",
        "http://2130706433/",
        "http://169.254.169.254/latest/meta-data/",
        "http://172.31.0.1/",
        "http://[::1]/",
        "http://[fc00::1]/",
        "https://user:password@example.com/",
    ],
)
def test_public_http_policy_rejects_unsafe_targets(url: str) -> None:
    with pytest.raises(ValueError):
        validate_public_http_url(url)
    assert _is_safe_url(url)[0] is False


def test_public_http_policy_accepts_public_ip_literal() -> None:
    target = validate_public_http_url("https://93.184.216.34/docs")
    assert target.scheme == "https"
    assert target.addresses == ("93.184.216.34",)


def test_redirect_handler_revalidates_destination() -> None:
    handler = SafeRedirectHandler()
    request = urllib.request.Request("https://93.184.216.34/")
    with pytest.raises(ValueError):
        handler.redirect_request(request, None, 302, "Found", {}, "http://127.0.0.1/")


def test_http_request_rejects_file_scheme_and_invalid_timeout() -> None:
    with pytest.raises(ValueError, match="scheme"):
        _validate_http_request({"url": "file:///etc/passwd"})
    with pytest.raises(ValueError, match="timeout"):
        _validate_http_request({"url": "https://93.184.216.34/", "timeout": 0})


def test_state_changing_http_request_fails_closed_without_permissions() -> None:
    parsed = _validate_http_request(
        {"url": "https://93.184.216.34/", "method": "POST", "body": "payload"}
    )
    result = _run_http_request(parsed, ToolContext(cwd="."))
    assert result.ok is False
    assert "requires approval" in result.output


def test_network_permission_is_one_shot(tmp_path: Path) -> None:
    prompts: list[dict] = []

    def approve_once(request: dict) -> dict:
        prompts.append(request)
        return {"decision": "allow_once"}

    permissions = PermissionManager(str(tmp_path), prompt=approve_once)
    permissions.ensure_network_request("POST", "https://93.184.216.34/items")
    assert prompts[0]["kind"] == "network"
    assert [choice["decision"] for choice in prompts[0]["choices"]] == [
        "allow_once",
        "deny_once",
    ]


def test_bounded_reader_never_returns_more_than_limit() -> None:
    data, truncated = read_bounded(io.BytesIO(b"abcdef"), 4)
    assert data == b"abcd"
    assert truncated is True
