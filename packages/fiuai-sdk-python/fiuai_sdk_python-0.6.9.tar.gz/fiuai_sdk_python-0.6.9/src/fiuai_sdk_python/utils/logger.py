# -- coding: utf-8 --
# Project: fiuai-world
# Created Date: 2025-01-27
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

import logging
import os
import sys
from typing import Any, Callable, Dict, Optional


def _make_context_filter(
    context_injector: Optional[Callable[[], Optional[Dict[str, Any]]]],
) -> logging.Filter:
    """根据 context_injector 构建过滤器：非 None 时注入返回值到 record，否则仅设置默认 trace_id。"""

    class _InjectorFilter(logging.Filter):
        def __init__(self, injector: Optional[Callable[[], Optional[Dict[str, Any]]]]) -> None:
            super().__init__()
            self._injector = injector

        def filter(self, record: logging.LogRecord) -> bool:
            if self._injector is not None:
                try:
                    ctx = self._injector()
                    if ctx:
                        for k, v in ctx.items():
                            setattr(record, k, v)
                except Exception:
                    pass
            if not getattr(record, "trace_id", None):
                record.trace_id = "-"
            return True

    return _InjectorFilter(context_injector)


def init_logger(
    log_path: str = "logs/",
    log_level: str = "INFO",
    json_log: bool = False,
    caller: bool = True,
    context_injector: Optional[Callable[[], Optional[Dict[str, Any]]]] = None,
):
    """初始化日志配置

    Args:
        log_path: 日志文件路径
        log_level: 日志级别
        json_log: 是否使用JSON格式日志
        caller: 是否显示调用者信息
        context_injector: 可选，无参可调用对象，返回 dict（如 {"trace_id": "xxx"}），
            非 None 时会将返回的键值注入到每条日志记录中。
    """
    # 创建日志目录
    if log_path and not os.path.exists(log_path):
        os.makedirs(log_path)

    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)

    # 获取根日志记录器
    root_logger = logging.getLogger()

    # 设置根日志记录器的级别
    root_logger.setLevel(level)

    # 清除现有的处理器（避免重复添加）
    root_logger.handlers.clear()

    context_filter = _make_context_filter(context_injector)
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [trace_id:%(trace_id)s] - %(message)s'

    # 配置控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))
    console_handler.addFilter(context_filter)
    root_logger.addHandler(console_handler)

    # 如果指定了日志文件路径，添加文件处理器
    if log_path:
        file_handler = logging.FileHandler(
            os.path.join(log_path, "app.log"),
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.addFilter(context_filter)
        root_logger.addHandler(file_handler)

    # 过滤第三方库的日志，只显示 ERROR 及以上级别
    third_party_loggers = [
        'nebula3.logger',
        'nebula3',
        'urllib3',
        'httpx',
        'httpcore',
    ]
    for logger_name in third_party_loggers:
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)
