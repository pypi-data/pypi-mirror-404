# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2025 10 Mo
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

import logging
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

# 配置日志
logger = logging.getLogger(__name__)


# {'errors': [{'type': 'ValidationError', 'exception': 'Traceback (most recent call last):\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/fiuai_utils/auth.py", line 143, in wrapper\n    r = func(*args, **kwargs)\n    ^^^^^^^^^^^^^^^^^^^^^\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/fiuai_utils/api/docs/docs.py", line 163, in create_internal_doc\n    r = frappe.new_doc(**d).save()\n        ^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/model/document.py", line 416, in save\n    return self._save(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/model/document.py", line 438, in _save\n    return self.insert()\n           ^^^^^^^^^^^^^\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/model/document.py", line 346, in insert\n    self._validate()\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/model/document.py", line 660, in _validate\n    self._validate_mandatory()\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/model/document.py", line 994, in _validate_mandatory\n    raise frappe.MandatoryError(\nfrappe.exceptions.MandatoryError: [Item, 7384919604195962880]: stock_uom\n\nDuring handling of the above exception, another exception occurred:\n\nTraceback (most recent call last):\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/app.py", line 131, in application\n    response = frappe.api.handle(request)\n               ^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/api/__init__.py", line 51, in handle\n    data = endpoint(**arguments)\n           ^^^^^^^^^^^^^^^^^^^^^\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/fiuai_utils/auth.py", line 147, in wrapper\n    frappe.throw(title=_("INTERNAL_API_ERROR"),msg=_(f"{e}"))\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/__init__.py", line 651, in throw\n    msgprint(\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/__init__.py", line 616, in msgprint\n    _raise_exception()\n  File "fiuai/frappe-fiuai/local/apps/frappe/frappe/__init__.py", line 567, in _raise_exception\n    raise exc\nfrappe.exceptions.ValidationError: [Item, 7384919604195962880]: stock_uom\n', 'message': '[Item, 7384919604195962880]: stock_uom', 'title': 'INTERNAL_API_ERROR', 'indicator': 'red'}], 'messages': [{'message': '错误：商品缺少值：默认计量单位', 'title': '消息'}]}

class ApiResponse(BaseModel):
    """API响应结构体"""
    http_success: bool = Field(description="HTTP是否成功")
    api_success: bool = Field(description="API业务是否成功")
    status_code: int = Field(description="HTTP状态码")
    data: Optional[Any] = Field(description="响应数据", default=None)
    error_code: Optional[List[str]] = Field(description="错误码列表，对应error的title", default=None)
    error_message: Optional[List[str]] = Field(description="错误消息列表，对应error的message", default=None)
    messages: Optional[List[Any]] = Field(description="消息，对应messages字段", default=None)
    
    def is_success(self) -> bool:
        """判断是否完全成功"""
        return self.http_success and self.api_success


def parse_response(response) -> ApiResponse:
    """
    解析HTTP响应，返回结构化的API响应
    
    Args:
        response: httpx响应对象
        
    Returns:
        ApiResponse: 结构化的API响应
    """
    # 检查响应是否存在
    if not response:
        return ApiResponse(
            http_success=False,
            api_success=False,
            status_code=504,
            error_message=["Api no response"],
            error_code=["API_NO_RESPONSE"],
        )
    
   
    # 解析JSON响应
    try:
         # 检查HTTP状态码
        http_success = 200 <= response.status_code < 300
    except Exception as e:
        return ApiResponse(
            http_success=False,
            api_success=False,
            status_code=response.status_code,
            error_message=[f"Invalid JSON response: {e}"],
            error_code=["API_INVALID_JSON"]
        )
    
    try:
        response_data = response.json()
    except Exception as e:
        return ApiResponse(
            http_success=True,
            api_success=False,
            status_code=response.status_code,
            error_message=[f"Invalid JSON response: {e}"],
            error_code=["API_INVALID_JSON"]
        )
    
    # 检查API业务是否成功
    api_success = _is_api_success(response_data)
    
    if api_success:
        # 成功响应，提取数据
        data = _extract_success_data(response_data)
        return ApiResponse(
            http_success=http_success,
            api_success=True,
            status_code=response.status_code,
            error_message=None,
            error_code=None,
            data=data,
            messages=None
        )
    else:
        # 失败响应，提取错误信息
        error_info = _extract_error_info(response_data)
        return ApiResponse(
            http_success=http_success,
            api_success=False,
            status_code=response.status_code,
            error_message=error_info.get("error_messages", []),
            error_code=error_info.get("error_codes", []),
            data=None,
            messages=error_info.get("messages", [])
        )


def _is_api_success(response_data: Dict[str, Any]) -> bool:
    """
    判断API业务是否成功
    
    Args:
        response_data: API响应数据
        
    Returns:
        bool: 是否成功
    """
    # 检查是否有错误
    errors = response_data.get("errors", None)
    if errors:
        return False
    
    # 检查是否有异常
    exc = response_data.get("exc", None)
    if exc:
        return False
    
    # 检查HTTP状态码
    http_status_code = response_data.get("http_status_code", None)
    if http_status_code is not None:
        return 200 <= http_status_code < 300
    
    # 默认认为有message或data字段就是成功
    return response_data.get("message", None) is not None or response_data.get("data", None) is not None


def _extract_success_data(response_data: Dict[str, Any]) -> Any:
    """
    从成功响应中提取数据
    优先从 data 字段获取，如果没有则从 messages 字段获取
    
    Args:
        response_data: API响应数据
        
    Returns:
        Any: 提取的数据，如果都没有则返回 None
    """
    # 优先从 data 字段获取
    data = response_data.get("data", None)
    if data is not None:
        return data
    
    # 如果 data 字段为空，尝试从 messages 字段获取
    messages = response_data.get("messages", None)
    if messages is not None:
        return messages
    
    # 都没有则返回 None
    return None


def _extract_error_info(response_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    从响应中提取错误信息
    返回所有错误信息的列表
    
    Args:
        response_data: API响应数据
        
    Returns:
        Dict[str, List[str]]: {"messages": 错误消息列表, "codes": 错误码列表}
    """
    error_messages = []
    error_codes = []
    
    # 处理errors字段
    errors = response_data.get("errors", None)
    if errors and isinstance(errors, list) and errors:
        for error in errors:
            if isinstance(error, dict):
                error_msg = error.get("message", "Unknown error")
                error_title = error.get("title", "UnknownError")
                
                error_messages.append(error_msg)
                error_codes.append(error_title)
                
                # 记录异常详情到日志
                exception = error.get("exception", None)
                if exception:
                    logger.error(f"API Error Exception: {error_title} - {exception}")
                
                # 记录其他错误信息到日志
                indicator = error.get("indicator", "")
                if indicator:
                    logger.error(f"API Error Details: {error_title} - Indicator: {indicator}")
    
    # 处理exc字段（V1 API格式）
    # exc = response_data.get("exc", None)
    # if exc:
    #     logger.error(f"API Exception: {exc}")
    #     error_messages.append(str(exc))
    #     error_codes.append("API_EXCEPTION")
    
    # 处理message字段中的错误
    messages = response_data.get("messages", [])
    logger.error(f"API Messages: {messages}")
    # if messages and isinstance(messages, list):
    #     for msg in messages:
    #         if isinstance(msg, dict):
    #             error_msg = msg.get("message", "Unknown error")
    #             # error_title = msg.get("title", "UnknownError")
    #             error_messages.append(error_msg)
                # error_codes.append(error_title)
    # if messages and isinstance(messages, str):
    #     # 检查是否是错误消息
    #     if any(keyword in messages.lower() for keyword in ["error", "failed", "invalid", "unauthorized"]):
    #         logger.error(f"API Error Message: {messages}")
    #         error_messages.append(str(messages))
    #         error_codes.append("API_ERROR")
    
    # 如果没有找到任何错误，返回默认错误
    # if not error_messages:
        # error_messages.append("Unknown error occurred")
        # error_codes.append("UnknownError")
    
    return {"error_messages": error_messages, "error_codes": error_codes, "messages": messages}


def is_auth_error(error_type: str) -> bool:
    """
    判断是否为认证相关错误
    
    Args:
        error_type: 错误类型
        
    Returns:
        bool: 是否为认证错误
    """
    auth_types = ["AuthenticationError", "PermissionError", "Unauthorized", "Forbidden"]
    return any(auth_type in error_type for auth_type in auth_types)


