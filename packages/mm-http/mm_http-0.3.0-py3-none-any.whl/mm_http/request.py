"""Async HTTP request implementation using aiohttp."""

from typing import Any

import aiohttp
from aiohttp import (
    ClientConnectionError,
    ClientConnectorError,
    ClientHttpProxyError,
    ClientSSLError,
    InvalidUrlClientError,
    ServerConnectionError,
    ServerDisconnectedError,
)
from aiohttp_socks import ProxyConnectionError, ProxyConnector
from multidict import CIMultiDictProxy

from .response import HttpResponse, TransportErrorType


async def http_request(
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
    """Send an HTTP request and return the response."""
    timeout_ = aiohttp.ClientTimeout(total=timeout) if timeout else None
    if user_agent:
        if not headers:
            headers = {}
        headers["User-Agent"] = user_agent

    try:
        if proxy and proxy.startswith("socks"):
            return await _request_with_socks_proxy(
                url,
                method=method,
                params=params,
                data=data,
                json=json,
                headers=headers,
                cookies=cookies,
                proxy=proxy,
                timeout=timeout_,
                verify_ssl=verify_ssl,
                follow_redirects=follow_redirects,
            )
        return await _request_with_http_or_none_proxy(
            url,
            method=method,
            params=params,
            data=data,
            json=json,
            headers=headers,
            cookies=cookies,
            proxy=proxy,
            timeout=timeout_,
            verify_ssl=verify_ssl,
            follow_redirects=follow_redirects,
        )
    except TimeoutError as err:
        return HttpResponse.from_transport_error(TransportErrorType.TIMEOUT, str(err))
    except (aiohttp.ClientProxyConnectionError, ProxyConnectionError, ClientHttpProxyError) as err:
        return HttpResponse.from_transport_error(TransportErrorType.PROXY, str(err))
    except InvalidUrlClientError as err:
        return HttpResponse.from_transport_error(TransportErrorType.INVALID_URL, str(err))
    except (
        ClientConnectorError,
        ServerConnectionError,
        ServerDisconnectedError,
        ClientSSLError,
        ClientConnectionError,
    ) as err:
        return HttpResponse.from_transport_error(TransportErrorType.CONNECTION, str(err))
    except Exception as err:
        return HttpResponse.from_transport_error(TransportErrorType.ERROR, str(err))


async def _request_with_http_or_none_proxy(
    url: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    cookies: dict[str, str] | None = None,
    proxy: str | None = None,
    timeout: aiohttp.ClientTimeout | None,
    verify_ssl: bool,
    follow_redirects: bool,
) -> HttpResponse:
    """Execute request with HTTP proxy or no proxy."""
    async with aiohttp.request(
        method,
        url,
        params=params,
        data=data,
        json=json,
        headers=headers,
        cookies=cookies,
        proxy=proxy,
        timeout=timeout,
        ssl=verify_ssl,
        allow_redirects=follow_redirects,
    ) as res:
        return HttpResponse(
            status_code=res.status,
            body=await res.text(),
            headers=headers_dict(res.headers),
        )


async def _request_with_socks_proxy(
    url: str,
    *,
    method: str = "GET",
    proxy: str,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    cookies: dict[str, str] | None = None,
    timeout: aiohttp.ClientTimeout | None,
    verify_ssl: bool,
    follow_redirects: bool,
) -> HttpResponse:
    """Execute request through SOCKS proxy."""
    connector = ProxyConnector.from_url(proxy, ssl=verify_ssl)
    async with (
        aiohttp.ClientSession(connector=connector) as session,
        session.request(
            method,
            url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            allow_redirects=follow_redirects,
        ) as res,
    ):
        return HttpResponse(
            status_code=res.status,
            body=await res.text(),
            headers=headers_dict(res.headers),
        )


def headers_dict(headers: CIMultiDictProxy[str]) -> dict[str, str]:
    """Convert multidict headers to dict, joining duplicate keys with comma."""
    result: dict[str, str] = {}
    for key in headers:
        values = headers.getall(key)
        if len(values) == 1:
            result[key] = values[0]
        else:
            result[key] = ", ".join(values)
    return result
