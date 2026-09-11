from __future__ import annotations

import urllib.error
import urllib.request

from minicode.network_safety import (
    MAX_RESPONSE_BYTES,
    build_safe_http_opener,
    read_bounded,
    validate_public_http_url,
)
from minicode.tooling import ToolContext, ToolDefinition, ToolResult

MAX_CONTENT_LENGTH = 50000
def _is_safe_url(url: str) -> tuple[bool, str]:
    """Compatibility wrapper around the shared public-network policy."""
    try:
        validate_public_http_url(url)
        return True, "OK"
    except ValueError as exc:
        return False, str(exc)


def _validate(input_data: dict) -> dict:
    url = input_data.get("url")
    if not isinstance(url, str) or not url:
        raise ValueError("url is required")
    validate_public_http_url(url)
    max_chars = int(input_data.get("max_chars", 10000))
    if max_chars < 100 or max_chars > MAX_CONTENT_LENGTH:
        raise ValueError(f"max_chars must be between 100 and {MAX_CONTENT_LENGTH}")
    return {"url": url, "max_chars": max_chars}


def _run(input_data: dict, context: ToolContext) -> ToolResult:
    url = input_data["url"]
    max_chars = input_data["max_chars"]

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "MiniCode-Loop/0.1.0 (Terminal Coding Assistant)",
                "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
            },
        )

        opener = build_safe_http_opener()
        
        with opener.open(req, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "")
            charset = "utf-8"

            if "charset=" in content_type:
                charset = content_type.split("charset=")[1].split(";")[0].strip()

            byte_limit = min(MAX_RESPONSE_BYTES, max(4096, max_chars * 4))
            raw, byte_truncated = read_bounded(response, byte_limit)
            try:
                text = raw.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                text = raw.decode("utf-8", errors="replace")

            # If HTML, try to extract meaningful content
            if "text/html" in content_type:
                text = _extract_text_from_html(text)

            # Truncate
            truncated = byte_truncated or len(text) > max_chars
            if truncated:
                text = text[:max_chars] + f"\n\n... [Content truncated at {max_chars} chars]"

            header = "\n".join([
                f"URL: {url}",
                f"CONTENT_TYPE: {content_type}",
                f"STATUS: {response.status}",
                f"CHARS: {len(text)}",
                f"TRUNCATED: {'yes' if truncated else 'no'}",
                "",
            ])

            return ToolResult(ok=True, output=header + text)

    except urllib.error.HTTPError as e:
        return ToolResult(
            ok=False,
            output=f"HTTP Error {e.code}: {e.reason}\nURL: {url}",
        )
    except urllib.error.URLError as e:
        return ToolResult(
            ok=False,
            output=f"Failed to fetch URL: {e.reason}\nURL: {url}",
        )
    except Exception as e:
        return ToolResult(
            ok=False,
            output=f"Error fetching URL: {e}\nURL: {url}",
        )


def _extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML content."""
    import re

    # Remove script and style elements
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL)
    # Remove all tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


web_fetch_tool = ToolDefinition(
    name="web_fetch",
    description="Fetch content from a URL. Supports HTML (extracted to text), JSON, and plain text. Useful for reading documentation, APIs, or web content.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to fetch content from"},
            "max_chars": {"type": "number", "description": "Maximum characters to return (default: 10000)"},
        },
        "required": ["url"],
    },
    validator=_validate,
    run=_run,
)
