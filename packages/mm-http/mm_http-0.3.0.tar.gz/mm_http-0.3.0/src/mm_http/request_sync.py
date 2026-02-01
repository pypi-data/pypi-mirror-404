"""Sync HTTP request implementation using requests library."""

from typing import Any

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import InvalidSchema, MissingSchema, ProxyError, SSLError

from .response import HttpResponse, TransportErrorType


def http_request_sync(
    url: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    cookies: dict[str, str] | None = None,
    user_agent: str | None = None,
    proxy: str | None = None,
    timeout: float | None = 10.0,
    verify_ssl: bool = True,
    follow_redirects: bool = True,
) -> HttpResponse:
    """Send a synchronous HTTP request and return the response."""
    if user_agent:
        if headers is None:
            headers = {}
        headers["User-Agent"] = user_agent

    proxies: dict[str, str] | None = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy,
        }

    try:
        res = requests.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            proxies=proxies,
            verify=verify_ssl,
            allow_redirects=follow_redirects,
        )
        return HttpResponse(
            status_code=res.status_code,
            body=res.text,
            headers=dict(res.headers),
        )
    except requests.Timeout as err:
        return HttpResponse.from_transport_error(TransportErrorType.TIMEOUT, str(err))
    except ProxyError as err:
        return HttpResponse.from_transport_error(TransportErrorType.PROXY, str(err))
    except (InvalidSchema, MissingSchema) as err:
        return HttpResponse.from_transport_error(TransportErrorType.INVALID_URL, str(err))
    except (RequestsConnectionError, SSLError) as err:
        return HttpResponse.from_transport_error(TransportErrorType.CONNECTION, str(err))
    except Exception as err:
        return HttpResponse.from_transport_error(TransportErrorType.ERROR, str(err))
