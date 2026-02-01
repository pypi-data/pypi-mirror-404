# -- coding: utf-8 --
# Project: fiuai-world
# Created Date: 2025-12-06
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

from typing import Any


def escape_table_name(table_name: str) -> str:
    """
    转义 PostgreSQL 表名，处理大小写和空格
    
    PostgreSQL 中，如果表名包含大写字母、空格或特殊字符，需要用双引号包裹
    Frappe 的表名格式是 tab{doctype}，其中 doctype 可能包含大写字母和空格
    
    Args:
        table_name: 表名（如 "tabContract" 或 "tabA B"）
        
    Returns:
        str: 转义后的表名（如 '"tabContract"' 或 '"tabA B"'）
        
    Example:
        escape_table_name("tabContract")  # 返回: '"tabContract"'
        escape_table_name("tabA B")       # 返回: '"tabA B"'
        escape_table_name("tabcontract")  # 返回: '"tabcontract"' (统一加引号，确保安全)
    """
    if not table_name:
        raise ValueError("table_name 不能为空")
    
    # 确保是字符串类型
    if not isinstance(table_name, str):
        table_name = str(table_name)
    
    # 去除首尾空白
    table_name = table_name.strip()
    
    # 如果已经用双引号包裹，先去除
    if table_name.startswith('"') and table_name.endswith('"'):
        table_name = table_name[1:-1]
    
    # 转义双引号（如果表名中包含双引号）
    escaped = table_name.replace('"', '""')
    
    # 用双引号包裹（PostgreSQL 中双引号用于标识符，可以处理大小写和空格）
    return f'"{escaped}"'


def build_frappe_table_name(doctype: str) -> str:
    """
    构建 Frappe 格式的表名并转义
    
    Frappe 的表名格式是 tab{doctype}，其中 doctype 可能包含大写字母和空格
    
    Args:
        doctype: 文档类型名称（如 "Contract" 或 "A B"）
        
    Returns:
        str: 转义后的表名（如 '"tabContract"' 或 '"tabA B"'）
        
    Example:
        build_frappe_table_name("Contract")  # 返回: '"tabContract"'
        build_frappe_table_name("A B")      # 返回: '"tabA B"'
    """
    if not doctype:
        raise ValueError("doctype 不能为空")
    
    # 确保是字符串类型
    if not isinstance(doctype, str):
        doctype = str(doctype)
    
    # 构建 Frappe 表名格式
    table_name = f"tab{doctype}"
    
    # 转义表名
    return escape_table_name(table_name)

