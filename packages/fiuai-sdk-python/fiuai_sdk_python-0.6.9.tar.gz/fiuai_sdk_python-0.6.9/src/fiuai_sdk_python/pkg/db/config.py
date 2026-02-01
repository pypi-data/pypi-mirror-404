# -- coding: utf-8 --
# Project: fiuai-world
# Created Date: 2025-01-27
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

from dataclasses import dataclass


@dataclass
class PostgresConfig:
    """PostgreSQL 配置"""
    host: str
    port: int
    user: str
    password: str
    database: str
    pool_minconn: int = 1  # 连接池最小连接数
    pool_maxconn: int = 10  # 连接池最大连接数
    pool_timeout: int = 30  # 获取连接超时时间（秒）
    connect_timeout: int = 10  # 连接超时时间（秒）
    retry_count: int = 3  # 重试次数
    retry_delay: int = 1  # 重试延迟（秒）

