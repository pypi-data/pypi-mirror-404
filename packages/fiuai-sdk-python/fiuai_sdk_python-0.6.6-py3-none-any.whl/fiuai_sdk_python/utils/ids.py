#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Project: FiuAI
Created Date: 2024-03-21
Author: liming
Email: lmlala@aliyun.com
Copyright (c) 2025 FiuAI
"""

import threading
import time
import os
import hashlib
from typing import Optional
from snowflake import SnowflakeGenerator


class SnowflakeIdGenerator:
    """
    雪花算法ID生成器
    使用 snowflake 包实现，支持多进程环境
    """
    _instance: Optional['SnowflakeIdGenerator'] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, instance: int = None):
        """
        初始化雪花算法ID生成器
        
        Args:
            instance: 实例ID (0-1023)，如果为None则自动生成
        """
        if hasattr(self, '_initialized'):
            return
            
        # 在初始化时获取一次进程信息并缓存
        self._process_id = os.getpid()
        self._start_time = self._get_process_start_time()
        self._object_id = id(self)
            
        # 自动生成实例ID，确保多进程环境下唯一性
        if instance is None:
            instance = self._generate_process_instance_id()
        elif not 0 <= instance <= 1023:
            raise ValueError("实例ID必须在0-1023之间")
            
        self.generator = SnowflakeGenerator(
            instance=instance
        )
        self._last_timestamp = 0
        self._instance_id = instance
        self._initialized = True

    def _get_process_start_time(self) -> float:
        """
        获取进程启动时间
        
        Returns:
            float: 进程启动时间
        """
        try:
            # 在Linux/macOS上使用更精确的时间
            if hasattr(os, 'times'):
                return os.times().elapsed
            else:
                return time.time()
        except:
            return time.time()

    def _generate_process_instance_id(self) -> int:
        """
        基于进程信息生成唯一的实例ID
        
        Returns:
            int: 0-1023之间的唯一实例ID
        """
        # 使用缓存的进程信息，避免重复调用
        process_info = f"{self._process_id}_{self._start_time}_{self._object_id}"
        hash_obj = hashlib.md5(process_info.encode())
        hash_int = int(hash_obj.hexdigest()[:8], 16)
        
        # 确保在0-1023范围内
        instance_id = hash_int % 1024
        
        return instance_id

    def next_id(self) -> int:
        """
        生成下一个ID
        
        Returns:
            int: 64位唯一ID
            
        Raises:
            OverflowError: 当时间戳达到最大值时抛出
            RuntimeError: 当检测到时间回退时抛出
        """
        try:
            result = next(self.generator)
            if result is None:
                raise ValueError("Generator returned None")
            
            # 检查时间回退（简单的时间戳检查）
            current_timestamp = int(time.time() * 1000)
            if current_timestamp < self._last_timestamp:
                raise RuntimeError(f"检测到时间回退: 当前时间 {current_timestamp} < 上次时间 {self._last_timestamp}")
            
            self._last_timestamp = current_timestamp
            return result
            
        except StopIteration:
            # 如果序列号达到最大值，重新初始化生成器
            with self._lock:
                self.generator = SnowflakeGenerator(instance=self._instance_id)
                result = next(self.generator)
                if result is None:
                    raise ValueError("Generator returned None")
                return result

    @property
    def instance_id(self) -> int:
        """获取当前实例ID"""
        return self._instance_id

    @property
    def process_id(self) -> int:
        """获取当前进程ID"""
        return self._process_id

    @property
    def start_time(self) -> float:
        """获取进程启动时间"""
        return self._start_time


# 全局单例实例和锁
_id_generator = None
_id_generator_lock = threading.Lock()


def gen_id() -> str:
    """
    获取下一个唯一ID
    
    Returns:
        str: 64位唯一ID字符串
        
    Raises:
        RuntimeError: 当ID生成失败时抛出
    """
    global _id_generator
    
    # 双重检查锁定模式，确保线程安全
    if _id_generator is None:
        with _id_generator_lock:
            if _id_generator is None:
                _id_generator = SnowflakeIdGenerator()
    
    try:
        return str(_id_generator.next_id())
    except Exception as e:
        # 记录错误并重新抛出
        raise RuntimeError(f"ID生成失败: {str(e)}") from e


def get_instance_info() -> dict:
    """
    获取当前ID生成器的实例信息
    
    Returns:
        dict: 包含进程ID和实例ID的信息
    """
    global _id_generator
    
    if _id_generator is None:
        return {"process_id": os.getpid(), "instance_id": None, "status": "not_initialized"}
    
    return {
        "process_id": _id_generator.process_id,
        "instance_id": _id_generator.instance_id,
        "start_time": _id_generator.start_time,
        "status": "initialized"
    }


def reset_id_generator():
    """
    重置ID生成器（主要用于测试或异常恢复）
    """
    global _id_generator
    with _id_generator_lock:
        _id_generator = None


def set_custom_instance_id(instance_id: int):
    """
    设置自定义实例ID（谨慎使用，确保多进程环境下唯一性）
    
    Args:
        instance_id: 自定义实例ID (0-1023)
        
    Raises:
        ValueError: 实例ID超出范围
        RuntimeError: 生成器已初始化
    """
    global _id_generator
    
    if not 0 <= instance_id <= 1023:
        raise ValueError("实例ID必须在0-1023之间")
    
    if _id_generator is not None:
        raise RuntimeError("生成器已初始化，无法修改实例ID")
    
    with _id_generator_lock:
        if _id_generator is None:
            _id_generator = SnowflakeIdGenerator(instance=instance_id)
        else:
            raise RuntimeError("生成器已初始化，无法修改实例ID")