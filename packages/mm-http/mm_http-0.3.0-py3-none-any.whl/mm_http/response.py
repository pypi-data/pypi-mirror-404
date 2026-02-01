"""HTTP response models and error types."""

import enum
import json
from typing import Any

import pydash
from mm_result import Result
from pydantic import BaseModel, model_validator


@enum.unique
class TransportErrorType(str, enum.Enum):
    """Transport-level error types."""

    TIMEOUT = "timeout"
    PROXY = "proxy"
    INVALID_URL = "invalid_url"
    CONNECTION = "connection"
    ERROR = "error"


class TransportError(BaseModel):
    """Transport error with type and message."""

    type: TransportErrorType
    message: str


class HttpResponse(BaseModel):
    """HTTP response with status, body, headers, and optional transport error."""

    status_code: int | None = None
    body: str | None = None
    headers: dict[str, str] | None = None
    transport_error: TransportError | None = None

    @model_validator(mode="after")
    def validate_mutually_exclusive_states(self) -> HttpResponse:
        """Validate that response has either HTTP data or transport error, but not both."""
        has_http_response = self.status_code is not None
        has_transport_error = self.transport_error is not None

        if has_http_response and has_transport_error:
            msg = "Cannot have both HTTP response and transport error"
            raise ValueError(msg)

        if not has_http_response and not has_transport_error:
            msg = "Must have either HTTP response or transport error"
            raise ValueError(msg)

        return self

    @classmethod
    def from_transport_error(cls, error_type: TransportErrorType, message: str) -> HttpResponse:
        """Create HttpResponse from transport error."""
        return cls(transport_error=TransportError(type=error_type, message=message))

    def json_body(self, path: str | None = None) -> Result[Any]:
        """Parse body as JSON with explicit error handling."""
        if self.body is None:
            return Result.err("body is None")
        try:
            data = json.loads(self.body)
        except json.JSONDecodeError as e:
            return Result.err(("JSON decode error", e))

        if path:
            if not pydash.has(data, path):
                return Result.err(f"path not found: {path}")
            return Result.ok(pydash.get(data, path))
        return Result.ok(data)

    def json_body_or_none(self, path: str | None = None) -> Any:  # noqa: ANN401 - JSON returns dynamic types
        """Parse body as JSON. Returns None if body is None, JSON invalid, or path not found.

        Warning: Do not use if None is a valid expected value — use json_body() instead.
        """
        if self.body is None:
            return None
        try:
            res = json.loads(self.body)
            return pydash.get(res, path, None) if path else res
        except json.JSONDecodeError:
            return None

    def get_header(self, name: str) -> str | None:
        """Get header value (case-insensitive)."""
        if self.headers is None:
            return None
        name_lower = name.lower()
        for key, value in self.headers.items():
            if key.lower() == name_lower:
                return value
        return None

    def is_success(self) -> bool:
        """Check if response has 2xx status."""
        return self.status_code is not None and 200 <= self.status_code < 300

    def is_err(self) -> bool:
        """Check if response represents an error (has transport error or status >= 400)."""
        return self.transport_error is not None or (self.status_code is not None and self.status_code >= 400)

    @property
    def error_message(self) -> str | None:
        """Get error message if transport_error is set or status_code >= 400, else None."""
        if self.transport_error:
            return f"{self.transport_error.type.value}: {self.transport_error.message}"
        if self.status_code is not None and self.status_code >= 400:
            return f"HTTP {self.status_code}"
        return None

    def to_result_err[T](self, error: str | Exception | tuple[str, Exception] | None = None) -> Result[T]:
        """Create error Result[T] from HttpResponse with meaningful error message."""
        if error is not None:
            result_error = error
        elif self.transport_error is not None:
            result_error = self.transport_error.type
        elif self.status_code is not None:
            result_error = f"HTTP {self.status_code}"
        else:
            result_error = "error"
        return Result.err(result_error, context=self.model_dump(mode="json"))

    def to_result_ok[T](self, value: T) -> Result[T]:
        """Create success Result[T] from HttpResponse with given value."""
        return Result.ok(value, context=self.model_dump(mode="json"))

    @property
    def content_type(self) -> str | None:
        """Get Content-Type header value (case-insensitive)."""
        return self.get_header("content-type")
