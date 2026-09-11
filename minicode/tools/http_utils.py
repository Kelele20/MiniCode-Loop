from __future__ import annotations

import json
import urllib.error
import urllib.request

from minicode.network_safety import build_safe_http_opener, read_bounded, validate_public_http_url
from minicode.tooling import ToolDefinition, ToolContext, ToolResult


MAX_REQUEST_BODY_BYTES = 100_000
MAX_HTTP_RESPONSE_BYTES = 50_000


def _validate_http_request(input_data: dict) -> dict:
    """Validate input for http_request tool."""
    url = input_data.get("url", "")
    raw_method = input_data.get("method", "GET")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url is required and must be a non-empty string")
    if not isinstance(raw_method, str):
        raise ValueError("method must be a string")
    method = raw_method.upper()
    if method not in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}:
        raise ValueError(f"Invalid method: {method}")
    normalized_url = url.strip()
    validate_public_http_url(normalized_url)
    headers = input_data.get("headers", {})
    if not isinstance(headers, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in headers.items()
    ):
        raise ValueError("headers must contain only string keys and values")
    body = input_data.get("body", "")
    if not isinstance(body, (str, dict)):
        raise ValueError("body must be a string or JSON object")
    encoded_body = json.dumps(body).encode("utf-8") if isinstance(body, dict) else body.encode("utf-8")
    if len(encoded_body) > MAX_REQUEST_BODY_BYTES:
        raise ValueError(f"body exceeds {MAX_REQUEST_BODY_BYTES} bytes")
    timeout = input_data.get("timeout", 30)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 1 <= timeout <= 60:
        raise ValueError("timeout must be between 1 and 60 seconds")
    return {
        "url": normalized_url,
        "method": method,
        "headers": headers,
        "body": body,
        "timeout": float(timeout),
    }


def _run_http_request(input_data: dict, context: ToolContext) -> ToolResult:
    """Make an HTTP request."""
    url = input_data["url"]
    method = input_data["method"]
    headers = input_data.get("headers", {})
    body = input_data.get("body", "")
    timeout = input_data.get("timeout", 30)

    if context.permissions is None and method not in {"GET", "HEAD"}:
        return ToolResult(ok=False, output=f"Network request requires approval: {method} {url}")
    if context.permissions is not None:
        try:
            context.permissions.ensure_network_request(method, url)
        except RuntimeError as exc:
            return ToolResult(ok=False, output=str(exc))

    # Build request
    req = urllib.request.Request(url, method=method)
    for key, value in headers.items():
        req.add_header(key, value)
    
    if body and method in {"POST", "PUT", "PATCH"}:
        if isinstance(body, dict):
            body = json.dumps(body)
            req.add_header("Content-Type", "application/json")
        req.data = body.encode("utf-8")
    
    try:
        with build_safe_http_opener().open(req, timeout=timeout) as response:
            status = getattr(response, "status", None)
            response_headers = dict(response.headers)
            raw, truncated = read_bounded(response, MAX_HTTP_RESPONSE_BYTES)
            content = raw.decode("utf-8", errors="replace")
            
            # Try to parse JSON
            try:
                content = json.dumps(json.loads(content), indent=2, ensure_ascii=False)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            if truncated:
                content += f"\n\n... [Response truncated at {MAX_HTTP_RESPONSE_BYTES} bytes]"
            
            lines = [
                "--- Response ---",
                f"Status: {status}",
                f"Headers: {json.dumps(response_headers, indent=2)}",
                "",
                "Body:",
                content[:10000],  # Limit output
            ]
            
            return ToolResult(ok=True, output="\n".join(lines))
    
    except urllib.error.HTTPError as e:
        raw, truncated = read_bounded(e, MAX_HTTP_RESPONSE_BYTES)
        detail = raw.decode("utf-8", errors="replace")
        if truncated:
            detail += "\n... [Error response truncated]"
        return ToolResult(ok=False, output=f"HTTP {e.code}: {e.reason}\n{detail}")
    except urllib.error.URLError as e:
        return ToolResult(ok=False, output=f"Network error: {e.reason}")
    except Exception as e:
        return ToolResult(ok=False, output=f"Error: {e}")


http_request_tool = ToolDefinition(
    name="http_request",
    description="Make HTTP requests (GET, POST, PUT, DELETE, etc.). Supports custom headers and JSON body.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Request URL"},
            "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS"},
            "headers": {"type": "object", "description": "Request headers as key-value pairs"},
            "body": {"type": "string", "description": "Request body (for POST, PUT, PATCH)"},
            "timeout": {"type": "number", "description": "Request timeout in seconds (default: 30)"}
        },
        "required": ["url"]
    },
    validator=_validate_http_request,
    run=_run_http_request,
)
