# -- coding: utf-8 --
# Project: auth
# Created Date: 2025-01-09
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

from fastapi import Request, HTTPException
from typing import Optional, Union, Dict, Literal
from .type import AuthData
from .context_mgr import get_auth_data as get_auth_data_from_context


def get_auth_data(
    request: Optional[Union[Request, Dict[str, str]]] = None,
    engine: Literal["fastapi", "dict"] = "fastapi",
) -> Optional[AuthData]:
    """
    从请求或当前上下文中获取认证数据。
    request 为 None 时从当前 RequestContext 解析（FiuaiContextMiddleware + AuthMiddleware 或 init_context 内可用），无上下文时返回 None。
    传入 request 时从 request 取，不存在时抛 HTTPException/ValueError。
    """
    if request is None:
        return get_auth_data_from_context()
    if engine == "fastapi":
        if not isinstance(request, Request):
            raise TypeError(
                "request must be a FastAPI Request object when engine='fastapi'"
            )
        auth_data = getattr(request.state, "auth_data", None)
        if not auth_data:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Unauthorized",
                    "message": "Authentication data not found",
                    "code": "AUTH_NOT_FOUND",
                },
            )
        return auth_data
    if engine == "dict":
        if not isinstance(request, dict):
            raise TypeError("request must be a dict when engine='dict'")
        auth_data = request.get("auth_data")
        if not auth_data:
            raise ValueError("Authentication data not found in request dict")
        return auth_data
    raise ValueError("engine must be either 'fastapi' or 'dict'")


def get_current_user_id(
    request: Optional[Union[Request, Dict[str, str]]] = None,
    engine: Literal["fastapi", "dict"] = "fastapi",
) -> Optional[str]:
    """
    获取当前用户ID。request 为 None 时从当前上下文取；无上下文或未认证时返回 None。
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.user_id if auth_data else None


def get_current_tenant_id(
    request: Optional[Union[Request, Dict[str, str]]] = None,
    engine: Literal["fastapi", "dict"] = "fastapi",
) -> Optional[str]:
    """
    获取当前租户ID。request 为 None 时从当前上下文取；无上下文或未认证时返回 None。
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.auth_tenant_id if auth_data else None


def get_current_company(
    request: Optional[Union[Request, Dict[str, str]]] = None,
    engine: Literal["fastapi", "dict"] = "fastapi",
) -> Optional[str]:
    """
    获取当前公司ID。request 为 None 时从当前上下文取；无上下文或未认证时返回 None。
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.current_company if auth_data else None


def get_company_unique_no(
    request: Optional[Union[Request, Dict[str, str]]] = None,
    engine: Literal["fastapi", "dict"] = "fastapi",
) -> Optional[str]:
    """
    获取当前公司唯一编号。request 为 None 时从当前上下文取；无上下文或未认证时返回 None。
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.company_unique_no if auth_data else None


def get_impersonation(
    request: Optional[Union[Request, Dict[str, str]]] = None,
    engine: Literal["fastapi", "dict"] = "fastapi",
) -> Optional[str]:
    """
    获取当前代表的租户ID。request 为 None 时从当前上下文取；无上下文或未认证时返回 None。
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.impersonation if auth_data else None


def get_current_client(
    request: Optional[Union[Request, Dict[str, str]]] = None,
    engine: Literal["fastapi", "dict"] = "fastapi",
) -> Optional[str]:
    """
    获取当前客户端标识。request 为 None 时从当前上下文取；无上下文或未认证时返回 None。
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.client if auth_data else None


def is_impersonating(
    request: Optional[Union[Request, Dict[str, str]]] = None,
    engine: Literal["fastapi", "dict"] = "fastapi",
) -> bool:
    """
    检查是否正在代表其他租户。request 为 None 时从当前上下文取；无上下文或未认证时返回 False。
    """
    auth_data = get_auth_data(request, engine)
    if not auth_data:
        return False
    return bool(
        auth_data.impersonation and auth_data.impersonation != auth_data.auth_tenant_id
    )
