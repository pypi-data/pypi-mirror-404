# -- coding: utf-8 --
# Project: fiuai-world
# Created Date: 2025-01-27
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

import logging
import os
import sys




def init_logger(
    log_path: str = "logs/",
    log_level: str = "INFO",
    json_log: bool = False,
    caller: bool = True
):
    """初始化日志配置
    
    Args:
        log_path: 日志文件路径
        log_level: 日志级别
        json_log: 是否使用JSON格式日志
        caller: 是否显示调用者信息
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
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    # 添加 event_id 和 task_id 到日志格式中
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [trace_id:%(trace_id)s] - %(message)s'
    console_handler.setFormatter(logging.Formatter(log_format))
    # 添加上下文过滤器
    root_logger.addHandler(console_handler)
    
    # 如果指定了日志文件路径，添加文件处理器
    if log_path:
        file_handler = logging.FileHandler(
            os.path.join(log_path, "app.log"),
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        # 添加 event_id 和 task_id 到日志格式中
        file_handler.setFormatter(logging.Formatter(log_format))
        # 添加上下文过滤器
        root_logger.addHandler(file_handler)
    
    # 过滤第三方库的日志，只显示 ERROR 及以上级别
    # 这样可以减少不必要的 INFO、DEBUG 和 WARNING 日志输出
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


# 全局过滤器实例


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器
    
    自动添加 ContextFilter，从上下文中获取 event_id 和 task_id 并记录到日志中
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    logger = logging.getLogger(name)
    
    
    return logger
