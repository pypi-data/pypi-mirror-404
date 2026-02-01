# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2025-01-31
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

"""
HTTP 客户端与认证头拦截器：从当前上下文注入认证头，支持同步/异步、可选重试。
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Union

import httpx

from ..context import get_current_headers, is_current_context_valid

logger = logging.getLogger(__name__)

# 需要传递的认证头列表（与 auth 目录下 AuthHeader 对齐）
AUTH_HEADER_KEYS = [
    "x-fiuai-user",
    "x-fiuai-auth-tenant-id",
    "x-fiuai-current-company",
    "x-fiuai-impersonation",
    "x-fiuai-unique-no",
    "x-fiuai-trace-id",
    "x-fiuai-client",
    "x-fiuai-channel",
    "x-fiuai-lang",
    "accept-language",
]


def extract_auth_headers() -> Dict[str, str]:
    """
    从当前上下文中提取认证头信息。

    Returns:
        Dict[str, str]: 认证头字典，若上下文无效则返回空字典。
    """
    try:
        if not is_current_context_valid():
            logger.debug("current context is invalid, cannot extract auth headers")
            return {}
        headers = get_current_headers()
        if not headers:
            logger.debug("cannot get request headers from current context")
            return {}
        auth_headers = {}
        for key in AUTH_HEADER_KEYS:
            value = headers.get(key)
            if value:
                auth_headers[key] = value
        return auth_headers
    except Exception as e:
        logger.warning("failed to extract auth headers from context: %s", e)
        return {}


async def auth_header_interceptor(request: httpx.Request) -> None:
    """
    异步认证头拦截器：为请求注入当前上下文的认证头，并在有 body 时设置默认 Content-Type。
    """
    auth_headers = extract_auth_headers()
    if auth_headers:
        for key, value in auth_headers.items():
            request.headers[key] = value
        logger.debug("added auth headers to request: %s", list(auth_headers.keys()))
    else:
        logger.debug("no auth headers found in context, skipping header injection")
    if request.content and "content-type" not in request.headers:
        request.headers["content-type"] = "application/json"
        logger.debug("added default Content-Type: application/json")


def sync_auth_header_interceptor(request: httpx.Request) -> None:
    """
    同步认证头拦截器：为请求注入当前上下文的认证头，并在有 body 时设置默认 Content-Type。
    """
    auth_headers = extract_auth_headers()
    if auth_headers:
        for key, value in auth_headers.items():
            request.headers[key] = value
        logger.debug("added auth headers to request: %s", list(auth_headers.keys()))
    else:
        logger.debug("no auth headers found in context, skipping header injection")
    if request.content and "content-type" not in request.headers:
        request.headers["content-type"] = "application/json"
        logger.debug("added default Content-Type: application/json")


class RetryableAsyncClient(httpx.AsyncClient):
    """支持重试的异步 httpx 客户端。"""

    def __init__(
        self,
        retry_count: int = 0,
        retry_interval: float = 1.0,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.retry_count = retry_count
        self.retry_interval = retry_interval

    async def _request_with_retry(
        self,
        method: str,
        url: Union[httpx.URL, str],
        *args: Any,
        **kwargs: Any,
    ) -> httpx.Response:
        last_exception: Optional[Exception] = None
        for attempt in range(self.retry_count + 1):
            try:
                response = await super().request(method, url, *args, **kwargs)
                if response.status_code >= 500 and attempt < self.retry_count:
                    logger.warning(
                        "request failed with status %s, retrying (%s/%s)",
                        response.status_code,
                        attempt + 1,
                        self.retry_count,
                    )
                    await response.aclose()
                    await asyncio.sleep(self.retry_interval)
                    continue
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.retry_count:
                    logger.warning(
                        "request failed with status %s, retrying (%s/%s)",
                        e.response.status_code,
                        attempt + 1,
                        self.retry_count,
                    )
                    await e.response.aclose()
                    await asyncio.sleep(self.retry_interval)
                    continue
                last_exception = e
                logger.error("request failed with client error: %s", e)
                raise
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.retry_count:
                    logger.warning(
                        "request failed: %s, retrying (%s/%s)",
                        e,
                        attempt + 1,
                        self.retry_count,
                    )
                    await asyncio.sleep(self.retry_interval)
                else:
                    logger.error("request failed after %s attempts: %s", self.retry_count + 1, e)
                    raise
        if last_exception:
            raise last_exception
        raise httpx.HTTPError("request failed")

    async def get(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._request_with_retry("GET", url, *args, **kwargs)

    async def post(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._request_with_retry("POST", url, *args, **kwargs)

    async def put(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._request_with_retry("PUT", url, *args, **kwargs)

    async def delete(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._request_with_retry("DELETE", url, *args, **kwargs)

    async def patch(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._request_with_retry("PATCH", url, *args, **kwargs)

    async def head(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._request_with_retry("HEAD", url, *args, **kwargs)

    async def options(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return await self._request_with_retry("OPTIONS", url, *args, **kwargs)


class RetryableSyncClient(httpx.Client):
    """支持重试的同步 httpx 客户端。"""

    def __init__(
        self,
        retry_count: int = 0,
        retry_interval: float = 1.0,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.retry_count = retry_count
        self.retry_interval = retry_interval

    def _request_with_retry(
        self,
        method: str,
        url: Union[httpx.URL, str],
        *args: Any,
        **kwargs: Any,
    ) -> httpx.Response:
        last_exception: Optional[Exception] = None
        for attempt in range(self.retry_count + 1):
            try:
                response = super().request(method, url, *args, **kwargs)
                if response.status_code >= 500 and attempt < self.retry_count:
                    logger.warning(
                        "request failed with status %s, retrying (%s/%s)",
                        response.status_code,
                        attempt + 1,
                        self.retry_count,
                    )
                    response.close()
                    time.sleep(self.retry_interval)
                    continue
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.retry_count:
                    logger.warning(
                        "request failed with status %s, retrying (%s/%s)",
                        e.response.status_code,
                        attempt + 1,
                        self.retry_count,
                    )
                    e.response.close()
                    time.sleep(self.retry_interval)
                    continue
                last_exception = e
                logger.error("request failed with client error: %s", e)
                raise
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.retry_count:
                    logger.warning(
                        "request failed: %s, retrying (%s/%s)",
                        e,
                        attempt + 1,
                        self.retry_count,
                    )
                    time.sleep(self.retry_interval)
                else:
                    logger.error("request failed after %s attempts: %s", self.retry_count + 1, e)
                    raise
        if last_exception:
            raise last_exception
        raise httpx.HTTPError("request failed")

    def get(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("GET", url, *args, **kwargs)

    def post(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("POST", url, *args, **kwargs)

    def put(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("PUT", url, *args, **kwargs)

    def delete(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("DELETE", url, *args, **kwargs)

    def patch(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("PATCH", url, *args, **kwargs)

    def head(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("HEAD", url, *args, **kwargs)

    def options(self, url: Union[httpx.URL, str], *args: Any, **kwargs: Any) -> httpx.Response:
        return self._request_with_retry("OPTIONS", url, *args, **kwargs)


def create_http_client(
    base_url: Optional[str] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
    verify: bool = True,
    retry_count: int = 0,
    retry_interval: float = 1.0,
    **kwargs: Any,
) -> httpx.AsyncClient:
    """创建带认证头拦截器的 httpx 异步客户端。"""
    client_kwargs: Dict[str, Any] = {
        "timeout": timeout,
        "follow_redirects": follow_redirects,
        "verify": verify,
        **kwargs,
    }
    if base_url is not None:
        client_kwargs["base_url"] = base_url
    if retry_count > 0:
        return RetryableAsyncClient(
            retry_count=retry_count,
            retry_interval=retry_interval,
            **client_kwargs,
            event_hooks={"request": [auth_header_interceptor]},
        )
    return httpx.AsyncClient(
        **client_kwargs,
        event_hooks={"request": [auth_header_interceptor]},
    )


def create_sync_http_client(
    base_url: Optional[str] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
    verify: bool = True,
    retry_count: int = 0,
    retry_interval: float = 1.0,
    **kwargs: Any,
) -> httpx.Client:
    """创建带认证头拦截器的 httpx 同步客户端。"""
    client_kwargs: Dict[str, Any] = {
        "timeout": timeout,
        "follow_redirects": follow_redirects,
        "verify": verify,
        **kwargs,
    }
    if base_url is not None:
        client_kwargs["base_url"] = base_url
    if retry_count > 0:
        return RetryableSyncClient(
            retry_count=retry_count,
            retry_interval=retry_interval,
            **client_kwargs,
            event_hooks={"request": [sync_auth_header_interceptor]},
        )
    return httpx.Client(
        **client_kwargs,
        event_hooks={"request": [sync_auth_header_interceptor]},
    )


_global_async_client: Optional[httpx.AsyncClient] = None
_global_sync_client: Optional[httpx.Client] = None


def get_async_http_client(
    base_url: Optional[str] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
    verify: bool = True,
    retry_count: int = 0,
    retry_interval: float = 1.0,
    **kwargs: Any,
) -> httpx.AsyncClient:
    """获取全局 httpx 异步客户端（单例）。"""
    global _global_async_client
    if _global_async_client is None:
        _global_async_client = create_http_client(
            base_url=base_url,
            timeout=timeout,
            follow_redirects=follow_redirects,
            verify=verify,
            retry_count=retry_count,
            retry_interval=retry_interval,
            **kwargs,
        )
    return _global_async_client


def get_sync_http_client(
    base_url: Optional[str] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
    verify: bool = True,
    retry_count: int = 0,
    retry_interval: float = 1.0,
    **kwargs: Any,
) -> httpx.Client:
    """获取全局 httpx 同步客户端（单例）。"""
    global _global_sync_client
    if _global_sync_client is None:
        _global_sync_client = create_sync_http_client(
            base_url=base_url,
            timeout=timeout,
            follow_redirects=follow_redirects,
            verify=verify,
            retry_count=retry_count,
            retry_interval=retry_interval,
            **kwargs,
        )
    return _global_sync_client


def close_global_clients() -> None:
    """关闭全局客户端。"""
    global _global_async_client, _global_sync_client
    if _global_async_client:
        _global_async_client.close()
        _global_async_client = None
    if _global_sync_client:
        _global_sync_client.close()
        _global_sync_client = None
