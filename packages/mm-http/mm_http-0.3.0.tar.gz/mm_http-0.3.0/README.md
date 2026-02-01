# mm-http

A simple and convenient HTTP client library for Python with both synchronous and asynchronous support.

## Features

- **Simple API** for one-off HTTP requests
- **Sync and Async** support with identical interfaces
- **JSON path navigation** with dot notation (`response.json_body_or_none("user.profile.name")`)
- **Proxy support** (HTTP and SOCKS5)
- **Unified error handling**
- **Type-safe** with full type annotations
- **No sessions** - optimized for simple, stateless requests

## Quick Start

### Async Usage

```python
from mm_http import http_request

# Simple GET request
response = await http_request("https://api.github.com/users/octocat")
user_name = response.json_body_or_none("name")  # Navigate JSON with dot notation

# POST with JSON data
response = await http_request(
    "https://httpbin.org/post",
    method="POST",
    json={"key": "value"},
    headers={"Authorization": "Bearer token"}
)

# With proxy
response = await http_request(
    "https://api.ipify.org?format=json",
    proxy="socks5://127.0.0.1:1080"
)
```

### Sync Usage

```python
from mm_http import http_request_sync

# Same API, but synchronous
response = http_request_sync("https://api.github.com/users/octocat")
user_name = response.json_body_or_none("name")
```

## API Reference

### Functions

- `http_request(url, **kwargs)` - Async HTTP request
- `http_request_sync(url, **kwargs)` - Sync HTTP request

### Parameters

- `url: str` - Request URL
- `method: str = "GET"` - HTTP method
- `params: dict[str, Any] | None = None` - URL query parameters
- `data: dict[str, Any] | None = None` - Form data
- `json: dict[str, Any] | None = None` - JSON data
- `headers: dict[str, Any] | None = None` - HTTP headers
- `cookies: dict[str, str] | None = None` - Cookies
- `user_agent: str | None = None` - User-Agent header
- `proxy: str | None = None` - Proxy URL (supports http://, https://, socks4://, socks5://)
- `timeout: float | None = 10.0` - Request timeout in seconds
- `verify_ssl: bool = True` - Enable/disable SSL certificate verification
- `follow_redirects: bool = True` - Enable/disable following redirects

### HttpResponse

```python
class HttpResponse(BaseModel):
    status_code: int | None
    body: str | None
    headers: dict[str, str] | None
    transport_error: TransportError | None

    # JSON parsing
    def json_body(self, path: str | None = None) -> Result[Any]
    def json_body_or_none(self, path: str | None = None) -> Any

    # Header access
    def get_header(self, name: str) -> str | None
    @property content_type(self) -> str | None

    # Status checks
    def is_success(self) -> bool  # 2xx status
    def is_err(self) -> bool  # Has transport error or status >= 400

    # Result conversion
    def to_result_ok[T](self, value: T) -> Result[T]
    def to_result_err[T](self, error: str | Exception | None = None) -> Result[T]

    # Pydantic methods
    def model_dump(self, mode: str = "python") -> dict[str, Any]

class TransportError(BaseModel):
    type: TransportErrorType
    message: str
```

### Error Types

```python
class TransportErrorType(str, Enum):
    TIMEOUT = "timeout"
    PROXY = "proxy"
    INVALID_URL = "invalid_url"
    CONNECTION = "connection"
    ERROR = "error"
```

## Examples

### JSON Path Navigation

```python
response = await http_request("https://api.github.com/users/octocat")

# Instead of: json.loads(response.body)["plan"]["name"]
plan_name = response.json_body_or_none("plan.name")

# Safe navigation - returns None if path doesn't exist
followers = response.json_body_or_none("followers_count")
nonexistent = response.json_body_or_none("does.not.exist")  # Returns None

# Or get full JSON
data = response.json_body_or_none()

# When None is a valid value, use json_body() for explicit error handling
result = response.json_body("optional_field")
if result.is_ok():
    value = result.value  # Could be None if field is null in JSON
else:
    print(f"Error: {result.error}")  # "body is None", "JSON decode error", or "path not found: ..."
```

### Error Handling

```python
response = await http_request("https://example.com", timeout=5.0)

# Simple check
if response.is_success():
    data = response.json_body_or_none()

# Detailed error handling
if response.is_err():
    if response.transport_error:
        print(f"Transport error: {response.transport_error.type} - {response.transport_error.message}")
    elif response.status_code >= 400:
        print(f"HTTP error: {response.status_code}")
else:
    print(f"Success: {response.status_code}")
```

### Proxy Usage

```python
# HTTP proxy
response = await http_request(
    "https://httpbin.org/ip",
    proxy="http://proxy.example.com:8080"
)

# SOCKS5 proxy
response = await http_request(
    "https://httpbin.org/ip",
    proxy="socks5://127.0.0.1:1080"
)
```

### Custom Headers and User-Agent

```python
response = await http_request(
    "https://api.example.com/data",
    headers={
        "Authorization": "Bearer your-token",
        "Accept": "application/json"
    },
    user_agent="MyApp/1.0"
)
```

### Result Type Integration

For applications using `Result[T, E]` pattern, `HttpResponse` provides convenient methods to convert responses into Result types:

```python
from mm_result import Result

async def get_user_id() -> Result[int]:
    response = await http_request("https://api.example.com/user")

    if response.is_err():
        return response.to_result_err()  # Returns "HTTP 404" or TransportErrorType.TIMEOUT

    user_id = response.json_body_or_none("id")
    return response.to_result_ok(user_id)

# Usage
result = await get_user_id()
if result.is_ok():
    print(f"User ID: {result.value}")
else:
    print(f"Error: {result.error}")  # "HTTP 404" or TransportErrorType.TIMEOUT
    print(f"HTTP details: {result.extra}")  # Contains full HTTP response data
```

**Result Methods:**
- `to_result_ok(value)` - Create `Result[T]` with success value, preserving HTTP details in `extra`
- `to_result_err(error?)` - Create `Result[T]` with error, preserving HTTP details in `extra`

## When to Use

**Use mm-http when you need:**
- Simple, one-off HTTP requests
- JSON API interactions with easy data access
- Proxy support for requests
- Unified sync/async interface

**Use requests/aiohttp directly when you need:**
- Session management and connection pooling
- Complex authentication flows
- Streaming responses
- Advanced HTTP features
- Custom retry logic
