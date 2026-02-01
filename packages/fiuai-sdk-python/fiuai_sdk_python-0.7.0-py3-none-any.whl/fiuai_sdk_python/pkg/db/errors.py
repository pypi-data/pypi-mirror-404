# -- coding: utf-8 --
# Project: fiuai-world
# Created Date: 2025-01-27
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI


class PostgresError(Exception):
    """PostgreSQL 基础错误类"""
    pass


class PostgresConnectionError(PostgresError):
    """PostgreSQL 连接错误"""
    pass


class PostgresQueryError(PostgresError):
    """PostgreSQL 查询错误"""
    pass


class PostgresPoolError(PostgresError):
    """PostgreSQL 连接池错误"""
    pass

