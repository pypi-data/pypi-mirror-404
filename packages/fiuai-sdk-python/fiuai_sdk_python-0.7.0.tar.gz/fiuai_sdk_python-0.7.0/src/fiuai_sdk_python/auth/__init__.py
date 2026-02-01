from .header import parse_auth_headers, extract_auth_from_request
from .type import AuthData, AuthHeader
from .helper import (
    get_auth_data,
    get_current_user_id,
    get_current_tenant_id,
    get_current_company,
    get_company_unique_no,
    get_impersonation,
    is_impersonating,
)
from .context_mgr import (
    ContextManager,
    init_context,
    WorldData,
    get_auth_data_from_context,
    set_auth_data,
    update_auth_data,
    get_world_data,
    set_user_profile_info,
    get_user_profile_info,
)

# 兼容旧用法：从 request 取 auth 时可用 get_auth_data(request) 或 get_auth_data_from_request(request)
get_auth_data_from_request = get_auth_data

__all__ = [
    "parse_auth_headers",
    "extract_auth_from_request",
    "AuthData",
    "AuthHeader",
    "get_auth_data",
    "get_auth_data_from_request",
    "get_auth_data_from_context",
    "get_current_user_id",
    "get_current_tenant_id",
    "get_current_company",
    "get_company_unique_no",
    "get_impersonation",
    "is_impersonating",
    "ContextManager",
    "init_context",
    "WorldData",
    "set_auth_data",
    "update_auth_data",
    "get_world_data",
    "set_user_profile_info",
    "get_user_profile_info",
]