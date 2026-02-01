import json
import os
import time
from collections.abc import Callable
from typing import Any

import pytest
from dotenv import load_dotenv
from pytest_httpserver import HTTPServer
from werkzeug import Request, Response

load_dotenv()


@pytest.fixture
def proxy_http() -> str:
    proxy = os.getenv("PROXY_HTTP")
    if not proxy:
        raise ValueError("PROXY_HTTP environment variable must be set")
    return proxy


@pytest.fixture
def proxy_socks5() -> str:
    proxy = os.getenv("PROXY_SOCKS5")
    if not proxy:
        raise ValueError("PROXY_SOCKS5 environment variable must be set")
    return proxy


@pytest.fixture
def json_response_data() -> dict[str, Any]:
    """Sample nested JSON for testing."""
    return {
        "user": {"id": 123, "profile": {"name": "John Doe", "email": "john@example.com"}},
        "items": [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}],
        "nullable_field": None,
        "count": 42,
    }


@pytest.fixture
def setup_json_endpoint(httpserver: HTTPServer, json_response_data: dict[str, Any]) -> Callable[[], str]:
    """Configure JSON endpoint that returns sample data."""

    def setup() -> str:
        httpserver.expect_request("/json").respond_with_json(json_response_data)
        return httpserver.url_for("/json")

    return setup


@pytest.fixture
def setup_text_endpoint(httpserver: HTTPServer) -> Callable[[str, int], str]:
    """Configure text endpoint with custom content and status."""

    def setup(content: str = "Hello, World!", status: int = 200) -> str:
        httpserver.expect_request("/text").respond_with_data(content, status=status, content_type="text/plain")
        return httpserver.url_for("/text")

    return setup


@pytest.fixture
def setup_echo_endpoint(httpserver: HTTPServer) -> Callable[[], str]:
    """Configure echo endpoint that returns request details."""

    def handler(request: Request) -> Response:
        echo_data = {
            "method": request.method,
            "path": request.path,
            "query_string": request.query_string.decode("utf-8"),
            "headers": dict(request.headers),
            "body": request.get_data(as_text=True),
        }
        return Response(json.dumps(echo_data), content_type="application/json")

    def setup() -> str:
        httpserver.expect_request("/echo").respond_with_handler(handler)
        return httpserver.url_for("/echo")

    return setup


@pytest.fixture
def setup_timeout_endpoint(httpserver: HTTPServer) -> Callable[[float], str]:
    """Configure delayed response endpoint for timeout tests."""

    def setup(delay: float = 2.0) -> str:
        def handler(_request: Request) -> Response:
            time.sleep(delay)
            return Response("OK", content_type="text/plain")

        httpserver.expect_request("/timeout").respond_with_handler(handler)
        return httpserver.url_for("/timeout")

    return setup
