"""
Project: fiuai-agent
Created Date: 2024-03-21
Author: liming
Email: lmlala@aliyun.com
Copyright (c) 2025 FiuAI
"""

from typing import Dict, Optional, List, Union, Tuple
from redis.asyncio import Redis as AsyncRedis, ConnectionPool as AsyncConnectionPool
from redis import Redis as SyncRedis, ConnectionPool as SyncConnectionPool
from langgraph.checkpoint.redis import RedisSaver, AsyncRedisSaver
from pydantic import BaseModel, Field
from ...utils.text import safe_str

class RedisDBConfig(BaseModel):
    name: str = Field(description="连接名称")
    host: str = Field(description="Redis主机")
    port: int = Field(description="Redis端口")
    password: str = Field(description="Redis密码")
    db: int = Field(description="Redis数据库编号")
    pool_size: int = Field(description="Redis连接池大小", default=20)
    ttl: int = Field(description="Redis TTL", default=86400)

class RedisManager:
    """Redis连接池管理器单例类
    
    用于管理多个Redis连接池，每个连接池对应不同的数据库
    支持同步和异步两种模式
    """
    _instance = None
    _async_pools: Dict[str, AsyncConnectionPool] = {}
    _sync_pools: Dict[str, SyncConnectionPool] = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = False
    
    async def initialize(
        self,
        async_dbs: List[RedisDBConfig] = [],
        sync_dbs: List[RedisDBConfig] = []
    ):
        """初始化Redis连接池
        
        Args:
            async_dbs: 需要初始化的异步数据库列表
            sync_dbs: 需要初始化的同步数据库列表
        """
        if self._initialized:
            return
            
        # 初始化异步连接池
        for db in async_dbs:
            await self.get_async_pool(db)
            # await self._init_async_index(db)
            
        # 初始化同步连接池
        for db in sync_dbs:
            self.get_sync_pool(db)
            # self._init_sync_index(db)
        self._initialized = True
    
    def _init_sync_index(self, db: RedisDBConfig) -> SyncConnectionPool:
        """初始化索引"""
        _client = SyncRedis(connection_pool=self._sync_pools[db.name])
        with RedisSaver.from_conn_string(
            redis_client=_client
        ) as c:
            c.setup()

    async def _init_async_index(self, db: RedisDBConfig) -> AsyncConnectionPool:
        """初始化索引"""
        _client = AsyncRedis(connection_pool=self._async_pools[db.name])
        async with AsyncRedisSaver.from_conn_string(
            redis_client=_client
        ) as c:
            await c.asetup()

    async def get_async_pool(self, db: RedisDBConfig) -> AsyncConnectionPool:
        """获取指定数据库的异步连接池
        
        Args:
            db: RedisDBConfig
            
        Returns:
            AsyncConnectionPool: Redis异步连接池实例
        """
        
        if db.name not in self._async_pools:
            self._async_pools[db.name] = AsyncConnectionPool.from_url(
                f"redis://:{safe_str(db.password)}@{db.host}:{db.port}/{db.db}",
                db=db.db,
                decode_responses=True,
                max_connections=db.pool_size
            )
            
        return self._async_pools[db.name]
    
    def get_sync_pool(self, db: RedisDBConfig) -> SyncConnectionPool:
        """获取指定数据库的同步连接池
        
        Args:
            db: RedisDBConfig
            
        Returns:
            SyncConnectionPool: Redis同步连接池实例
        """
        if db.name not in self._sync_pools:
            self._sync_pools[db.name] = SyncConnectionPool.from_url(
                f"redis://:{safe_str(db.password)}@{db.host}:{db.port}/{db.db}",
                db=db.db,
                decode_responses=True,
                max_connections=db.pool_size
            )
        
        # 初始化
        with RedisSaver.from_conn_string(
            redis_client=self._sync_pools[db.name]
        ) as c:
            c.setup()

        return self._sync_pools[db.name]
    
    def get_async_client(self, db_name: str) -> AsyncRedis:
        """获取指定数据库的异步Redis客户端
        
        Args:
            db_name: 数据库名称
            
        Returns:
            AsyncRedis: Redis异步客户端实例
            
        Raises:
            RuntimeError: 如果Redis连接池未初始化
        """
        if not self._initialized:
            raise RuntimeError("pool not initialized")
            
        if db_name not in self._async_pools:
            raise RuntimeError(f"pool not found: {db_name}")
        
        pool = self._async_pools[db_name]
        return AsyncRedis(connection_pool=pool)
    
    def get_sync_client(self, db_name: str) -> SyncRedis:
        """获取指定数据库的同步Redis客户端
        
        Args:
            db_name: 数据库名称
            
        Returns:
            SyncRedis: Redis同步客户端实例
            
        Raises:
            RuntimeError: 如果Redis连接池未初始化
        """
        if not self._initialized:
            raise RuntimeError("pool not initialized")
            
        if db_name not in self._sync_pools:
            raise RuntimeError(f"pool not found: {db_name}")
        
        pool = self._sync_pools[db_name]
        return SyncRedis(connection_pool=pool)
    
    async def close_all(self):
        """关闭所有连接池"""
        # 关闭异步连接池
        for pool in self._async_pools.values():
            await pool.disconnect()
        self._async_pools.clear()
        
        # 关闭同步连接池
        for pool in self._sync_pools.values():
            pool.disconnect()
        self._sync_pools.clear()
        
        self._initialized = False

# 创建全局单例实例
redis_manager = RedisManager() 