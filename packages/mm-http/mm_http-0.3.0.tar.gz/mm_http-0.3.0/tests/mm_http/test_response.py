"""Unit tests for HttpResponse, TransportError, and TransportErrorType."""

import pytest
from mm_result import Result

from mm_http import HttpResponse, TransportError, TransportErrorType


class TestTransportErrorType:
    """Tests for TransportErrorType enum."""

    def test_enum_values_exist(self):
        """All expected enum values are present."""
        assert TransportErrorType.TIMEOUT == "timeout"
        assert TransportErrorType.PROXY == "proxy"
        assert TransportErrorType.INVALID_URL == "invalid_url"
        assert TransportErrorType.CONNECTION == "connection"
        assert TransportErrorType.ERROR == "error"

    def test_string_representation(self):
        """Enum values are strings."""
        assert isinstance(TransportErrorType.TIMEOUT, str)
        assert TransportErrorType.TIMEOUT.value == "timeout"


class TestTransportError:
    """Tests for TransportError model."""

    def test_creation(self):
        """Create TransportError with type and message."""
        error = TransportError(type=TransportErrorType.TIMEOUT, message="Request timed out")
        assert error.type == TransportErrorType.TIMEOUT
        assert error.message == "Request timed out"

    def test_serialization(self):
        """Serialize TransportError to dict."""
        error = TransportError(type=TransportErrorType.CONNECTION, message="Connection refused")
        data = error.model_dump()
        assert data == {"type": "connection", "message": "Connection refused"}


class TestHttpResponseValidation:
    """Tests for HttpResponse validation logic."""

    def test_valid_http_response(self):
        """Create valid HTTP response with status code."""
        response = HttpResponse(status_code=200, body="OK", headers={"Content-Type": "text/plain"})
        assert response.status_code == 200
        assert response.body == "OK"
        assert response.transport_error is None

    def test_valid_transport_error(self):
        """Create valid response with transport error."""
        response = HttpResponse(transport_error=TransportError(type=TransportErrorType.TIMEOUT, message="timeout"))
        assert response.status_code is None
        assert response.transport_error is not None

    def test_invalid_both_set(self):
        """Reject response with both HTTP data and transport error."""
        with pytest.raises(ValueError, match="Cannot have both"):
            HttpResponse(status_code=200, transport_error=TransportError(type=TransportErrorType.ERROR, message="err"))

    def test_invalid_neither_set(self):
        """Reject response with neither HTTP data nor transport error."""
        with pytest.raises(ValueError, match="Must have either"):
            HttpResponse()

    def test_factory_method(self):
        """Create response using from_transport_error factory."""
        response = HttpResponse.from_transport_error(TransportErrorType.PROXY, "Proxy failed")
        assert response.transport_error is not None
        assert response.transport_error.type == TransportErrorType.PROXY
        assert response.transport_error.message == "Proxy failed"


class TestHttpResponseJsonParsing:
    """Tests for JSON body parsing."""

    @pytest.mark.parametrize(
        ("body", "path", "expected"),
        [
            ('{"name": "John"}', "name", "John"),
            ('{"user": {"id": 123}}', "user.id", 123),
            ('{"items": [1, 2, 3]}', "items[0]", 1),
            ('{"a": {"b": {"c": "deep"}}}', "a.b.c", "deep"),
            ('{"count": 42}', None, {"count": 42}),
        ],
    )
    def test_path_navigation(self, body: str, path: str | None, expected):
        """Navigate JSON with dot notation paths."""
        response = HttpResponse(status_code=200, body=body)
        assert response.json_body_or_none(path) == expected

    def test_none_body(self):
        """Return None when body is None."""
        response = HttpResponse(status_code=204, body=None)
        assert response.json_body_or_none("any.path") is None

    def test_invalid_json(self):
        """Return None for invalid JSON."""
        response = HttpResponse(status_code=200, body="not json")
        assert response.json_body_or_none() is None

    def test_missing_path(self):
        """Return None for non-existent path."""
        response = HttpResponse(status_code=200, body='{"a": 1}')
        assert response.json_body_or_none("b.c.d") is None

    def test_null_value_in_json(self):
        """Return None for null JSON value."""
        response = HttpResponse(status_code=200, body='{"nullable": null}')
        assert response.json_body_or_none("nullable") is None

    def test_json_body_explicit_error_none_body(self):
        """json_body returns error for None body."""
        response = HttpResponse(status_code=204, body=None)
        result = response.json_body("field")
        assert result.is_err()
        assert result.error == "body is None"

    def test_json_body_explicit_error_invalid_json(self):
        """json_body returns error for invalid JSON."""
        response = HttpResponse(status_code=200, body="not json")
        result = response.json_body()
        assert result.is_err()
        assert "JSON decode error" in str(result.error)

    def test_json_body_explicit_error_missing_path(self):
        """json_body returns error for missing path."""
        response = HttpResponse(status_code=200, body='{"a": 1}')
        result = response.json_body("b.c")
        assert result.is_err()
        assert "path not found" in str(result.error)

    def test_json_body_returns_null_value(self):
        """json_body returns None for null JSON value (not error)."""
        response = HttpResponse(status_code=200, body='{"nullable": null}')
        result = response.json_body("nullable")
        assert result.is_ok()
        assert result.value is None


class TestHttpResponseHeaders:
    """Tests for header access."""

    def test_get_header(self):
        """Get header by name."""
        response = HttpResponse(status_code=200, headers={"Content-Type": "application/json"})
        assert response.get_header("Content-Type") == "application/json"

    def test_get_header_case_insensitive(self):
        """Get header case-insensitively."""
        response = HttpResponse(status_code=200, headers={"Content-Type": "text/html"})
        assert response.get_header("content-type") == "text/html"
        assert response.get_header("CONTENT-TYPE") == "text/html"

    def test_get_header_missing(self):
        """Return None for missing header."""
        response = HttpResponse(status_code=200, headers={"X-Custom": "value"})
        assert response.get_header("Authorization") is None

    def test_get_header_no_headers(self):
        """Return None when headers is None."""
        response = HttpResponse(status_code=200, body="OK")
        assert response.get_header("Any-Header") is None

    def test_content_type_property(self):
        """Get content type via property."""
        response = HttpResponse(status_code=200, headers={"Content-Type": "application/json; charset=utf-8"})
        assert response.content_type == "application/json; charset=utf-8"


class TestHttpResponseStatusChecks:
    """Tests for status check methods."""

    @pytest.mark.parametrize(
        ("status_code", "expected"),
        [
            (100, False),
            (199, False),
            (200, True),
            (201, True),
            (299, True),
            (300, False),
            (400, False),
            (500, False),
        ],
    )
    def test_is_success(self, status_code: int, expected: bool):
        """is_success returns True only for 2xx status codes."""
        response = HttpResponse(status_code=status_code)
        assert response.is_success() == expected

    def test_is_success_transport_error(self):
        """is_success returns False for transport errors."""
        response = HttpResponse.from_transport_error(TransportErrorType.TIMEOUT, "timeout")
        assert response.is_success() is False

    @pytest.mark.parametrize(
        ("status_code", "expected"),
        [
            (200, False),
            (299, False),
            (300, False),
            (399, False),
            (400, True),
            (404, True),
            (500, True),
            (503, True),
        ],
    )
    def test_is_err_status_codes(self, status_code: int, expected: bool):
        """is_err returns True for status >= 400."""
        response = HttpResponse(status_code=status_code)
        assert response.is_err() == expected

    def test_is_err_transport_error(self):
        """is_err returns True for transport errors."""
        response = HttpResponse.from_transport_error(TransportErrorType.CONNECTION, "refused")
        assert response.is_err() is True


class TestHttpResponseErrorMessage:
    """Tests for error_message property."""

    def test_transport_error_message(self):
        """Format transport error as message."""
        response = HttpResponse.from_transport_error(TransportErrorType.TIMEOUT, "connection timed out")
        assert response.error_message == "timeout: connection timed out"

    def test_http_error_message(self):
        """Format HTTP error as message."""
        response = HttpResponse(status_code=404, body="Not Found")
        assert response.error_message == "HTTP 404"

    def test_success_no_message(self):
        """Return None for successful responses."""
        response = HttpResponse(status_code=200, body="OK")
        assert response.error_message is None

    def test_3xx_no_message(self):
        """Return None for 3xx redirect responses."""
        response = HttpResponse(status_code=302)
        assert response.error_message is None


class TestHttpResponseResultConversion:
    """Tests for Result type conversion."""

    def test_to_result_ok(self):
        """Convert to success Result with value."""
        response = HttpResponse(status_code=200, body='{"id": 123}')
        result: Result[int] = response.to_result_ok(42)
        assert result.is_ok()
        assert result.value == 42
        assert result.context is not None
        assert result.context["status_code"] == 200

    def test_to_result_err_transport_error(self):
        """Convert transport error to error Result."""
        response = HttpResponse.from_transport_error(TransportErrorType.TIMEOUT, "timed out")
        result: Result[str] = response.to_result_err()
        assert result.is_err()
        assert result.error == TransportErrorType.TIMEOUT
        assert result.context is not None

    def test_to_result_err_http_error(self):
        """Convert HTTP error to error Result."""
        response = HttpResponse(status_code=500, body="Server Error")
        result: Result[str] = response.to_result_err()
        assert result.is_err()
        assert result.error == "HTTP 500"

    def test_to_result_err_custom_error(self):
        """Convert to error Result with custom error message."""
        response = HttpResponse(status_code=400, body="Bad Request")
        result: Result[str] = response.to_result_err("validation failed")
        assert result.is_err()
        assert result.error == "validation failed"

    def test_result_context_contains_response(self):
        """Result context contains full response data."""
        response = HttpResponse(status_code=201, body="created", headers={"X-Id": "abc"})
        result = response.to_result_ok("value")
        assert result.context is not None
        assert result.context["status_code"] == 201
        assert result.context["body"] == "created"
        assert result.context["headers"] == {"X-Id": "abc"}
