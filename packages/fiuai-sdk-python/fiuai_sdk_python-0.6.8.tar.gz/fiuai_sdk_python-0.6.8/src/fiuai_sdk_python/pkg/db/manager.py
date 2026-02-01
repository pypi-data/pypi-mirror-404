# -- coding: utf-8 --
# Project: fiuai-world
# Created Date: 2025-01-27
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

import time
import threading
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, DictCursor


from logging import getLogger
from .errors import (
    PostgresError,
    PostgresConnectionError,
    PostgresQueryError,
    PostgresPoolError,
)
from .config import PostgresConfig

logger = getLogger(__name__)


class PostgresManager:
    """PostgreSQL 连接池管理器单例类
    
    提供连接池管理、重连、重试等稳定性机制
    提供基础 CRUD 接口
    """
    _instance: Optional['PostgresManager'] = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._config: Optional[PostgresConfig] = None
        self._pool: Optional[pool.ThreadedConnectionPool] = None
        self._is_connected_ref = {'connected': False}
        self._initialized = True
    
    def initialize(self, config: PostgresConfig):
        """初始化 PostgreSQL 连接池
        
        Args:
            config: PostgreSQL 配置
            
        Raises:
            PostgresPoolError: 初始化失败时抛出
        """
        if self._is_connected_ref['connected']:
            logger.warning("PostgreSQL 已经初始化，跳过重复初始化")
            return
        
        self._config = config
        
        try:
            # 创建连接池
            self._pool = pool.ThreadedConnectionPool(
                minconn=config.pool_minconn,
                maxconn=config.pool_maxconn,
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.database,
                connect_timeout=config.connect_timeout,
            )
            
            # 测试连接
            test_conn = self._pool.getconn()
            if not test_conn:
                raise PostgresPoolError("无法从连接池获取连接")
            
            # 执行简单查询测试连接
            with test_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            self._pool.putconn(test_conn)
            self._is_connected_ref['connected'] = True
            
            logger.info(
                f"PostgreSQL 连接池初始化成功: {config.host}:{config.port}/{config.database}, "
                f"pool_size={config.pool_maxconn}"
            )
            
        except Exception as e:
            self._is_connected_ref['connected'] = False
            if self._pool:
                try:
                    self._pool.closeall()
                except Exception:
                    pass
                self._pool = None
            logger.error(f"PostgreSQL 初始化失败: {str(e)}")
            raise PostgresPoolError(f"初始化失败: {str(e)}")
    
    def _check_connection(self) -> bool:
        """检查连接是否有效
        
        Returns:
            bool: 连接是否有效
        """
        if not self._pool or not self._is_connected_ref.get('connected', False):
            return False
        
        try:
            conn = self._pool.getconn()
            if not conn:
                return False
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            self._pool.putconn(conn)
            return True
            
        except Exception as e:
            logger.warning(f"连接检查失败: {str(e)}")
            return False
    
    def _reconnect(self) -> bool:
        """重新连接
        
        Returns:
            bool: 重连是否成功
        """
        if not self._config:
            return False
        
        logger.info("尝试重新连接 PostgreSQL...")
        
        try:
            # 关闭旧连接池
            if self._pool:
                try:
                    self._pool.closeall()
                except Exception:
                    pass
                self._pool = None
            
            # 重新创建连接池
            self._pool = pool.ThreadedConnectionPool(
                minconn=self._config.pool_minconn,
                maxconn=self._config.pool_maxconn,
                host=self._config.host,
                port=self._config.port,
                user=self._config.user,
                password=self._config.password,
                database=self._config.database,
                connect_timeout=self._config.connect_timeout,
            )
            
            # 测试连接
            test_conn = self._pool.getconn()
            if not test_conn:
                raise PostgresPoolError("无法从连接池获取连接")
            
            with test_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            self._pool.putconn(test_conn)
            self._is_connected_ref['connected'] = True
            
            return True
            
        except Exception as e:
            logger.error(f"重连失败: {str(e)}")
            self._is_connected_ref['connected'] = False
            return False
    
    @contextmanager
    def _get_connection(self):
        """获取连接（带重连机制）
        
        Yields:
            connection: PostgreSQL 连接对象
            
        Raises:
            PostgresConnectionError: 获取连接失败时抛出
        """
        if not self._is_connected_ref['connected']:
            if not self._reconnect():
                raise PostgresConnectionError("无法连接到 PostgreSQL，请检查配置和网络")
        
        conn = None
        try:
            conn = self._pool.getconn()
            if not conn:
                # 尝试重连一次
                if self._reconnect():
                    conn = self._pool.getconn()
                
                if not conn:
                    raise PostgresConnectionError("无法从连接池获取连接")
            
            yield conn
            
        except psycopg2.Error as e:
            if conn:
                try:
                    self._pool.putconn(conn, close=True)
                except Exception:
                    pass
            self._is_connected_ref['connected'] = False
            raise PostgresConnectionError(f"数据库连接错误: {str(e)}")
        except Exception as e:
            if conn:
                try:
                    self._pool.putconn(conn)
                except Exception:
                    pass
            raise PostgresConnectionError(f"获取连接时发生错误: {str(e)}")
        finally:
            if conn:
                try:
                    self._pool.putconn(conn)
                except Exception:
                    pass
    
    def _execute_with_retry(
        self,
        query: str,
        params: Optional[tuple] = None,
        retry_count: Optional[int] = None,
        fetch: bool = True,
        fetch_one: bool = False,
        as_dict: bool = False,
    ) -> Optional[Union[List[Dict[str, Any]], List[tuple], int]]:
        """执行查询（带重试机制）
        
        Args:
            query: 查询语句
            params: 查询参数
            retry_count: 重试次数，None 则使用配置中的值
            fetch: 是否获取结果
            fetch_one: 是否只获取一条结果
            as_dict: 是否返回字典格式
            
        Returns:
            Optional[List[Dict[str, Any]]]: 查询结果，如果 fetch=False 则返回受影响的行数（int）
            
        Raises:
            PostgresQueryError: 执行失败时抛出
        """
        if retry_count is None:
            retry_count = self._config.retry_count if self._config else 3
        
        last_error = None
        for attempt in range(retry_count + 1):
            try:
                with self._get_connection() as conn:
                    cursor_factory = RealDictCursor if as_dict else None
                    with conn.cursor(cursor_factory=cursor_factory) as cursor:
                        logger.debug(f"[postgres-sql] {query}")
                        if params:
                            logger.debug(f"[postgres-params] {params}")
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)
                        
                        if not fetch:
                            rowcount = cursor.rowcount
                            conn.commit()
                            return rowcount
                        
                        if fetch_one:
                            row = cursor.fetchone()
                            if as_dict and row:
                                return [dict(row)]
                            return [row] if row else []
                        else:
                            rows = cursor.fetchall()
                            if as_dict:
                                return [dict(row) for row in rows]
                            return rows
                
            except psycopg2.Error as e:
                last_error = PostgresQueryError(f"数据库查询错误: {str(e)}")
                # 如果是连接相关错误，尝试重连
                error_msg = str(e).lower()
                if "connection" in error_msg or "timeout" in error_msg or "server closed" in error_msg:
                    self._is_connected_ref['connected'] = False
                    if attempt < retry_count:
                        time.sleep(self._config.retry_delay if self._config else 1)
                        continue
                
                if attempt < retry_count:
                    time.sleep(self._config.retry_delay if self._config else 1)
                    continue
                    
            except Exception as e:
                last_error = PostgresQueryError(f"执行查询时发生错误: {str(e)}")
                if attempt < retry_count:
                    time.sleep(self._config.retry_delay if self._config else 1)
                    continue
        
        raise last_error or PostgresQueryError("查询执行失败")
    
    def execute(
        self,
        query: str,
        params: Optional[tuple] = None,
        retry_count: Optional[int] = None,
    ) -> int:
        """执行 SQL 语句（不返回结果）
        
        Args:
            query: SQL 语句
            params: 查询参数
            retry_count: 重试次数
            
        Returns:
            int: 受影响的行数
            
        Raises:
            PostgresQueryError: 执行失败时抛出
        """
        if not self._is_connected_ref['connected']:
            raise PostgresQueryError("PostgreSQL 未初始化，请先调用 initialize()")
        
        result = self._execute_with_retry(query, params, retry_count, fetch=False)
        return result if result is not None else 0
    
    def query(
        self,
        query: str,
        params: Optional[tuple] = None,
        retry_count: Optional[int] = None,
        as_dict: bool = True,
    ) -> Union[List[Dict[str, Any]], List[tuple]]:
        """执行查询（返回结果）
        
        Args:
            query: 查询语句
            params: 查询参数
            retry_count: 重试次数
            as_dict: 是否返回字典格式
            
        Returns:
            Union[List[Dict[str, Any]], List[tuple]]: 查询结果列表，as_dict=True 时返回字典列表，否则返回元组列表
            
        Raises:
            PostgresQueryError: 执行失败时抛出
        """
        if not self._is_connected_ref['connected']:
            raise PostgresQueryError("PostgreSQL 未初始化，请先调用 initialize()")
        
        result = self._execute_with_retry(query, params, retry_count, fetch=True, as_dict=as_dict)
        return result or []
    
    def query_one(
        self,
        query: str,
        params: Optional[tuple] = None,
        retry_count: Optional[int] = None,
        as_dict: bool = True,
    ) -> Optional[Union[Dict[str, Any], tuple]]:
        """执行查询（返回单条结果）
        
        Args:
            query: 查询语句
            params: 查询参数
            retry_count: 重试次数
            as_dict: 是否返回字典格式
            
        Returns:
            Optional[Union[Dict[str, Any], tuple]]: 查询结果，as_dict=True 时返回字典，否则返回元组，如果不存在则返回 None
            
        Raises:
            PostgresQueryError: 执行失败时抛出
        """
        if not self._is_connected_ref['connected']:
            raise PostgresQueryError("PostgreSQL 未初始化，请先调用 initialize()")
        
        result = self._execute_with_retry(
            query, params, retry_count, fetch=True, fetch_one=True, as_dict=as_dict
        )
        return result[0] if result else None
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器
        
        Yields:
            connection: PostgreSQL 连接对象
            
        Raises:
            PostgresConnectionError: 获取连接失败时抛出
        """
        with self._get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise PostgresQueryError(f"事务执行失败: {str(e)}")
    
    def close(self):
        """关闭连接池"""
        if self._pool:
            try:
                self._pool.closeall()
            except Exception as e:
                logger.warning(f"关闭连接池时发生错误: {str(e)}")
            finally:
                self._pool = None
                self._is_connected_ref['connected'] = False
                logger.info("PostgreSQL 连接池已关闭")
    
    def is_connected(self) -> bool:
        """检查是否已连接
        
        Returns:
            bool: 是否已连接
        """
        return self._is_connected_ref['connected'] and self._check_connection()


# 创建全局单例实例
postgres_manager = PostgresManager()

