# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2025-01-31
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

"""
上下文管理：ContextManager、init_context、WorldData，
以及从当前上下文获取/设置认证数据的 get_auth_data_from_context、set_auth_data、update_auth_data、get_world_data。
可选：user_profile_info 的 set_user_profile_info / get_user_profile_info（请求级存储，不影响未使用的调用方）。
"""

import contextvars
import uuid
import logging
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field

from ..context import RequestContext, get_current_headers, is_current_context_valid
from .type import AuthData
from .header import parse_auth_headers

logger = logging.getLogger(__name__)

_current_context_manager: Optional["ContextManager"] = None

# 可选：请求级 UserProfileInfo，仅当调用方 set 时存在，不 set 则 get 为 None
_user_profile_info: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar(
    "user_profile_info", default=None
)


class WorldData(BaseModel):
    """World 上下文数据模型"""
    event_id: Optional[str] = Field(default=None, description="事件ID")
    task_id: Optional[str] = Field(default=None, description="任务ID")


class ContextManager:
    """
    上下文管理器，用于在后台任务中初始化和管理请求上下文。
    使用 context manager 模式，确保上下文在任务结束时自动清理。

    注意：
    - 上下文只在 `with` 语句块内生效
    - 退出 `with` 块时，上下文会被自动清理
    - 在异步环境中，上下文会在同一个异步任务中保持
    """

    def __init__(
        self,
        auth_data: Optional[AuthData] = None,
        headers: Optional[Dict[str, Any]] = None,
        world_data: Optional[WorldData] = None,
        event_id: Optional[str] = None,
        task_id: Optional[str] = None,
        user_profile_info: Optional[Any] = None,
    ):
        if auth_data and headers:
            raise ValueError("不能同时提供 auth_data 和 headers，请只提供其中一个")

        if world_data:
            self.world_data = world_data
        elif event_id is not None or task_id is not None:
            self.world_data = WorldData(event_id=event_id, task_id=task_id)
        else:
            self.world_data = WorldData()

        self._user_profile_info = user_profile_info
        self._user_profile_info_token: Optional[contextvars.Token] = None

        if auth_data:
            self._context = self._create_context_from_auth_data(auth_data)
        elif headers:
            self._context = RequestContext.from_dict(headers)
        else:
            raise ValueError("必须提供 auth_data 或 headers 之一")

    def _create_context_from_auth_data(self, auth_data: AuthData) -> RequestContext:
        """从认证数据创建请求上下文"""
        headers = {
            "x-fiuai-user": auth_data.user_id,
            "x-fiuai-auth-tenant-id": auth_data.auth_tenant_id,
            "x-fiuai-current-company": auth_data.current_company,
            "x-fiuai-impersonation": auth_data.impersonation or "",
            "x-fiuai-unique-no": auth_data.company_unique_no or auth_data.current_company,
            "x-fiuai-trace-id": auth_data.trace_id or str(uuid.uuid4()),
            "x-fiuai-client": auth_data.client or "unknown",
            "x-fiuai-channel": (auth_data.channel or "default").lower(),
            "x-fiuai-lang": "zh",
            "accept-language": "zh",
        }
        return RequestContext.from_dict(headers)

    def __enter__(self):
        global _current_context_manager
        _current_context_manager = self
        self._context.__enter__()
        if self._user_profile_info is not None:
            self._user_profile_info_token = _user_profile_info.set(self._user_profile_info)
        logger.debug("Context initialized")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._user_profile_info_token is not None:
            _user_profile_info.reset(self._user_profile_info_token)
            self._user_profile_info_token = None
        self._context.__exit__(exc_type, exc_val, exc_tb)
        global _current_context_manager
        _current_context_manager = None
        logger.debug("Context cleaned up")

    def update_auth_data(self, auth_data: AuthData) -> None:
        """更新上下文中的认证数据"""
        new_context = self._create_context_from_auth_data(auth_data)
        if hasattr(self._context, "_token") and self._context._token:
            self._context.__exit__(None, None, None)
        self._context = new_context
        self._context.__enter__()
        logger.debug("Context auth data updated")

    def update_headers(self, headers: Dict[str, Any]) -> None:
        """更新上下文中的请求头"""
        new_context = RequestContext.from_dict(headers)
        if hasattr(self._context, "_token") and self._context._token:
            self._context.__exit__(None, None, None)
        self._context = new_context
        self._context.__enter__()
        logger.debug("Context headers updated")


def init_context(
    auth_data: Optional[AuthData] = None,
    headers: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    auth_tenant_id: Optional[str] = None,
    current_company: Optional[str] = None,
    world_data: Optional[WorldData] = None,
    event_id: Optional[str] = None,
    task_id: Optional[str] = None,
    user_profile_info: Optional[Any] = None,
    **kwargs: Any,
) -> ContextManager:
    """
    初始化上下文，用于后台任务。返回的 ContextManager 必须在 `with` 语句中使用。

    支持三种方式：1) auth_data 对象  2) headers 字典  3) user_id, auth_tenant_id, current_company。
    trace_id 可从 auth_data.trace_id 或 kwargs["trace_id"]（仅方式 3）传入。
    可选 user_profile_info：在 with 块内 get_user_profile_info() 可读。
    """
    if auth_data:
        return ContextManager(
            auth_data=auth_data,
            world_data=world_data,
            event_id=event_id,
            task_id=task_id,
            user_profile_info=user_profile_info,
        )
    if headers:
        return ContextManager(
            headers=headers,
            world_data=world_data,
            event_id=event_id,
            task_id=task_id,
            user_profile_info=user_profile_info,
        )
    if user_id and auth_tenant_id and current_company:
        auth_data = AuthData(
            user_id=user_id,
            auth_tenant_id=auth_tenant_id,
            current_company=current_company,
            impersonation=kwargs.get("impersonation", ""),
            company_unique_no=kwargs.get("company_unique_no", current_company),
            trace_id=kwargs.get("trace_id", str(uuid.uuid4())),
            client=kwargs.get("client", "unknown"),
            channel=kwargs.get("channel", "default"),
        )
        return ContextManager(
            auth_data=auth_data,
            world_data=world_data,
            event_id=event_id,
            task_id=task_id,
            user_profile_info=user_profile_info,
        )
    raise ValueError(
        "必须提供以下之一："
        "1. auth_data 对象 "
        "2. headers 字典 "
        "3. user_id, auth_tenant_id, current_company 基本参数"
    )


def get_auth_data_from_context() -> Optional[AuthData]:
    """从当前上下文中获取认证数据。上下文无效或不存在时返回 None。"""
    try:
        if not is_current_context_valid():
            logger.warning("Current context is invalid, cannot get auth data")
            return None
        headers = get_current_headers()
        if not headers:
            logger.warning("Cannot get headers from current context")
            return None
        return parse_auth_headers(headers)
    except Exception as e:
        logger.warning("Failed to get auth data from context: %s", e)
        return None


def get_auth_data() -> Optional[AuthData]:
    """
    从当前上下文获取认证数据（无参）。
    与 get_auth_data_from_context() 行为一致，供业务方统一使用无参 get_auth_data()。
    上下文无效或不存在时返回 None。
    """
    return get_auth_data_from_context()


def set_auth_data(auth_data: AuthData) -> bool:
    """设置当前上下文中的认证数据。需在 init_context 的 with 块内使用。"""
    global _current_context_manager
    try:
        if _current_context_manager is None:
            logger.warning(
                "ContextManager does not exist, cannot set auth data. "
                "Please initialize context with init_context first"
            )
            return False
        _current_context_manager.update_auth_data(auth_data)
        return True
    except Exception as e:
        logger.warning("Failed to set auth data: %s", e)
        return False


def update_auth_data(
    user_id: Optional[str] = None,
    auth_tenant_id: Optional[str] = None,
    current_company: Optional[str] = None,
    **kwargs: Any,
) -> bool:
    """更新当前上下文中部分认证数据，未提供的字段保持不变。"""
    try:
        current = get_auth_data_from_context()
        if not current:
            logger.warning("Cannot get current auth data, please initialize context first")
            return False
        new_auth_data = AuthData(
            user_id=user_id or current.user_id,
            auth_tenant_id=auth_tenant_id or current.auth_tenant_id,
            current_company=current_company or current.current_company,
            impersonation=kwargs.get("impersonation", current.impersonation),
            company_unique_no=kwargs.get("company_unique_no", current.company_unique_no),
            trace_id=kwargs.get("trace_id", current.trace_id),
            client=kwargs.get("client", current.client),
            channel=kwargs.get("channel", current.channel),
        )
        return set_auth_data(new_auth_data)
    except Exception as e:
        logger.warning("Failed to update auth data: %s", e)
        return False


def get_world_data() -> Optional[WorldData]:
    """从当前上下文中获取 World 上下文数据。"""
    global _current_context_manager
    try:
        if _current_context_manager is None:
            return None
        return _current_context_manager.world_data
    except Exception as e:
        logger.warning("Failed to get world data: %s", e)
        return None


def set_user_profile_info(profile: Optional[Any]) -> None:
    """
    设置当前请求/上下文内的可选 UserProfileInfo。
    仅当需要 profile 时调用；不调用则 get_user_profile_info() 为 None，不影响其他使用者。
    在 HTTP 请求内由业务在 set_user_context 等入口调用；在 with init_context(...) 内也可通过 init_context(..., user_profile_info=...) 传入。
    """
    _user_profile_info.set(profile)


def get_user_profile_info() -> Optional[Any]:
    """
    获取当前请求/上下文内的可选 UserProfileInfo。
    未设置时返回 None；类型由调用方约定（如 profile.UserProfileInfo 或 dict）。
    """
    return _user_profile_info.get()
