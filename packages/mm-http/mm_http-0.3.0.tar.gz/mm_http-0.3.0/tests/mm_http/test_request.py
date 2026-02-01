"""Async HTTP tests using pytest-httpserver."""

import json
from collections.abc import Callable
from typing import Any

import pytest
from pytest_httpserver import HTTPServer
from werkzeug import Request, Response

from mm_http import TransportErrorType, http_request
from tests.helpers.proxy import get_ip_via_proxy, get_proxy_host


class TestAsyncHttpRequestBasic:
    """Basic HTTP method tests."""

    async def test_get(self, httpserver: HTTPServer):
        """Send GET request."""
        httpserver.expect_request("/get", method="GET").respond_with_data("OK")
        response = await http_request(httpserver.url_for("/get"))
        assert response.status_code == 200
        assert response.body == "OK"

    async def test_post(self, httpserver: HTTPServer):
        """Send POST request."""
        httpserver.expect_request("/post", method="POST").respond_with_data("Created", status=201)
        response = await http_request(httpserver.url_for("/post"), method="POST")
        assert response.status_code == 201

    async def test_put(self, httpserver: HTTPServer):
        """Send PUT request."""
        httpserver.expect_request("/put", method="PUT").respond_with_data("Updated")
        response = await http_request(httpserver.url_for("/put"), method="PUT")
        assert response.status_code == 200

    async def test_delete(self, httpserver: HTTPServer):
        """Send DELETE request."""
        httpserver.expect_request("/delete", method="DELETE").respond_with_data("", status=204)
        response = await http_request(httpserver.url_for("/delete"), method="DELETE")
        assert response.status_code == 204


class TestAsyncHttpRequestParams:
    """Tests for query parameters."""

    async def test_dict_params(self, httpserver: HTTPServer):
        """Send request with dict params."""

        def handler(request: Request) -> Response:
            assert request.args.get("key") == "value"
            assert request.args.get("num") == "42"
            return Response("OK")

        httpserver.expect_request("/params").respond_with_handler(handler)
        response = await http_request(httpserver.url_for("/params"), params={"key": "value", "num": 42})
        assert response.status_code == 200

    async def test_special_chars(self, httpserver: HTTPServer):
        """Encode special characters in params."""

        def handler(request: Request) -> Response:
            assert request.args.get("q") == "hello world"
            assert request.args.get("special") == "a=b&c"
            return Response("OK")

        httpserver.expect_request("/special").respond_with_handler(handler)
        response = await http_request(httpserver.url_for("/special"), params={"q": "hello world", "special": "a=b&c"})
        assert response.status_code == 200


class TestAsyncHttpRequestBody:
    """Tests for request body."""

    async def test_json_body(self, httpserver: HTTPServer):
        """Send JSON body."""

        def handler(request: Request) -> Response:
            data = json.loads(request.get_data(as_text=True))
            assert data == {"name": "test", "value": 123}
            assert "application/json" in request.headers.get("Content-Type", "")
            return Response("OK")

        httpserver.expect_request("/json", method="POST").respond_with_handler(handler)
        response = await http_request(httpserver.url_for("/json"), method="POST", json={"name": "test", "value": 123})
        assert response.status_code == 200

    async def test_form_data(self, httpserver: HTTPServer):
        """Send form data."""

        def handler(request: Request) -> Response:
            assert request.form.get("username") == "john"
            assert request.form.get("password") == "secret"
            return Response("OK")

        httpserver.expect_request("/form", method="POST").respond_with_handler(handler)
        response = await http_request(httpserver.url_for("/form"), method="POST", data={"username": "john", "password": "secret"})
        assert response.status_code == 200


class TestAsyncHttpRequestHeaders:
    """Tests for request headers."""

    async def test_custom_headers(self, httpserver: HTTPServer):
        """Send custom headers."""

        def handler(request: Request) -> Response:
            assert request.headers.get("X-Custom") == "custom-value"
            assert request.headers.get("Authorization") == "Bearer token123"
            return Response("OK")

        httpserver.expect_request("/headers").respond_with_handler(handler)
        response = await http_request(
            httpserver.url_for("/headers"), headers={"X-Custom": "custom-value", "Authorization": "Bearer token123"}
        )
        assert response.status_code == 200

    async def test_user_agent(self, httpserver: HTTPServer):
        """Send custom user agent."""

        def handler(request: Request) -> Response:
            assert request.headers.get("User-Agent") == "MyApp/1.0"
            return Response("OK")

        httpserver.expect_request("/ua").respond_with_handler(handler)
        response = await http_request(httpserver.url_for("/ua"), user_agent="MyApp/1.0")
        assert response.status_code == 200

    async def test_cookies(self, httpserver: HTTPServer):
        """Send cookies."""

        def handler(request: Request) -> Response:
            assert request.cookies.get("session") == "abc123"
            return Response("OK")

        httpserver.expect_request("/cookies").respond_with_handler(handler)
        response = await http_request(httpserver.url_for("/cookies"), cookies={"session": "abc123"})
        assert response.status_code == 200


class TestAsyncHttpRequestResponse:
    """Tests for response parsing."""

    async def test_status_code(self, httpserver: HTTPServer):
        """Parse status code."""
        httpserver.expect_request("/status").respond_with_data("OK", status=201)
        response = await http_request(httpserver.url_for("/status"))
        assert response.status_code == 201

    async def test_body(self, httpserver: HTTPServer):
        """Parse response body."""
        httpserver.expect_request("/body").respond_with_data("Response body content")
        response = await http_request(httpserver.url_for("/body"))
        assert response.body == "Response body content"

    async def test_headers(self, httpserver: HTTPServer):
        """Parse response headers."""
        httpserver.expect_request("/resp-headers").respond_with_data("OK", headers={"X-Response-Id": "resp-123"})
        response = await http_request(httpserver.url_for("/resp-headers"))
        assert response.get_header("X-Response-Id") == "resp-123"

    @pytest.mark.parametrize(
        ("status", "expected_success", "expected_err"),
        [
            (200, True, False),
            (201, True, False),
            (204, True, False),
            (301, False, False),
            (400, False, True),
            (404, False, True),
            (500, False, True),
        ],
    )
    async def test_various_status_codes(self, httpserver: HTTPServer, status: int, expected_success: bool, expected_err: bool):
        """Handle various HTTP status codes."""
        httpserver.expect_request(f"/status/{status}").respond_with_data("", status=status)
        response = await http_request(httpserver.url_for(f"/status/{status}"))
        assert response.status_code == status
        assert response.is_success() == expected_success
        assert response.is_err() == expected_err


class TestAsyncHttpRequestJson:
    """Tests for JSON response parsing."""

    async def test_json_response(self, setup_json_endpoint: Callable[[], str], json_response_data: dict[str, Any]):
        """Parse JSON response body."""
        url = setup_json_endpoint()
        response = await http_request(url)
        assert response.json_body_or_none() == json_response_data
        assert response.json_body_or_none("user.id") == 123
        assert response.json_body_or_none("user.profile.name") == "John Doe"


class TestAsyncHttpRequestRedirects:
    """Tests for redirect handling."""

    async def test_follow_redirects_true(self, httpserver: HTTPServer):
        """Follow redirects by default."""
        httpserver.expect_request("/redirect").respond_with_data("", status=302, headers={"Location": "/final"})
        httpserver.expect_request("/final").respond_with_data("Final destination")
        response = await http_request(httpserver.url_for("/redirect"), follow_redirects=True)
        assert response.status_code == 200
        assert response.body == "Final destination"

    async def test_follow_redirects_false(self, httpserver: HTTPServer):
        """Don't follow redirects when disabled."""
        httpserver.expect_request("/redirect").respond_with_data("", status=302, headers={"Location": "/final"})
        response = await http_request(httpserver.url_for("/redirect"), follow_redirects=False)
        assert response.status_code == 302


class TestAsyncHttpRequestTimeout:
    """Tests for timeout handling."""

    async def test_timeout_error(self, setup_timeout_endpoint: Callable[[float], str]):
        """Timeout returns transport error."""
        url = setup_timeout_endpoint(2.0)
        response = await http_request(url, timeout=0.5)
        assert response.transport_error is not None
        assert response.transport_error.type == TransportErrorType.TIMEOUT

    async def test_custom_timeout(self, setup_timeout_endpoint: Callable[[float], str]):
        """Custom timeout allows longer requests."""
        url = setup_timeout_endpoint(0.3)
        response = await http_request(url, timeout=5.0)
        assert response.status_code == 200


class TestAsyncHttpRequestErrors:
    """Tests for error handling."""

    async def test_connection_error(self):
        """Connection error returns transport error."""
        response = await http_request("http://localhost:59999/nonexistent")
        assert response.transport_error is not None
        assert response.transport_error.type == TransportErrorType.CONNECTION

    async def test_invalid_url(self):
        """Invalid URL returns transport error."""
        response = await http_request("not-a-valid-url")
        assert response.transport_error is not None
        assert response.transport_error.type == TransportErrorType.INVALID_URL


class TestAsyncHttpRequestProxy:
    """Tests for proxy functionality."""

    async def test_http_proxy(self, proxy_http: str):
        """Request via HTTP proxy, verify IP matches proxy host."""
        proxy_host = get_proxy_host(proxy_http)
        ip = await get_ip_via_proxy(proxy_http)
        assert ip is not None, "Failed to get IP via HTTP proxy"
        assert ip == proxy_host, f"Expected IP {proxy_host}, got {ip}"

    async def test_socks5_proxy(self, proxy_socks5: str):
        """Request via SOCKS5 proxy, verify IP matches proxy host."""
        proxy_host = get_proxy_host(proxy_socks5)
        ip = await get_ip_via_proxy(proxy_socks5)
        assert ip is not None, "Failed to get IP via SOCKS5 proxy"
        assert ip == proxy_host, f"Expected IP {proxy_host}, got {ip}"

    async def test_invalid_proxy(self):
        """Invalid proxy returns PROXY or CONNECTION transport error."""
        response = await http_request("https://api.ipify.org", proxy="socks5://127.0.0.1:59999", timeout=5.0)
        assert response.transport_error is not None
        assert response.transport_error.type in (TransportErrorType.PROXY, TransportErrorType.CONNECTION)
