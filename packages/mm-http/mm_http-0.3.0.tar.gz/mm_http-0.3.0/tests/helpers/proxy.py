"""Proxy testing utilities."""

import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from mm_http import http_request, http_request_sync

PUBLIC_IP_SERVICES = [
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://checkip.amazonaws.com",
    "https://ifconfig.me/ip",
    "https://ipinfo.io/ip",
    "https://v4.ident.me",
]


def get_proxy_host(proxy_url: str) -> str:
    """Extract host from proxy URL like 'socks5://user:pass@1.2.3.4:1080' -> '1.2.3.4'."""
    parsed = urlparse(proxy_url)
    if not parsed.hostname:
        raise ValueError(f"Cannot extract host from proxy URL: {proxy_url}")
    return parsed.hostname


async def get_ip_via_proxy(proxy: str, timeout: float = 10.0) -> str | None:
    """Query multiple IP services in parallel, return first valid IP response."""

    async def fetch_ip(url: str) -> str | None:
        response = await http_request(url, proxy=proxy, timeout=timeout)
        if response.is_success() and response.body:
            ip = response.body.strip()
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                return ip
        return None

    tasks = [asyncio.create_task(fetch_ip(url)) for url in PUBLIC_IP_SERVICES]

    # Return first successful result
    for coro in asyncio.as_completed(tasks):
        result = await coro
        if result:
            # Cancel remaining tasks
            for task in tasks:
                task.cancel()
            return result

    return None


def get_ip_via_proxy_sync(proxy: str, timeout: float = 10.0) -> str | None:
    """Query multiple IP services in parallel via ThreadPoolExecutor, return first valid IP."""

    def fetch_ip(url: str) -> str | None:
        response = http_request_sync(url, proxy=proxy, timeout=timeout)
        if response.is_success() and response.body:
            ip = response.body.strip()
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                return ip
        return None

    with ThreadPoolExecutor(max_workers=len(PUBLIC_IP_SERVICES)) as executor:
        futures = [executor.submit(fetch_ip, url) for url in PUBLIC_IP_SERVICES]
        for future in futures:
            result = future.result()
            if result:
                return result

    return None
