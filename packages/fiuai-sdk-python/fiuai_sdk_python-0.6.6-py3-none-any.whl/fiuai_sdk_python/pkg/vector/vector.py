# -- coding: utf-8 --
# Project: fiuai-world
# Created Date: 2025-01-27
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

import os
import time
import threading
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    CollectionStatus,
    UpdateStatus,
)
from qdrant_client.http import exceptions as qdrant_exceptions

from utils import get_logger
from utils.errors import FiuaiBaseError

logger = get_logger(__name__)


class QdrantError(FiuaiBaseError):
    """Qdrant 相关错误"""
    pass


@dataclass
class QdrantConfig:
    """Qdrant 配置"""
    host: str
    port: int = 6333
    api_key: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: int = 1
    prefer_grpc: bool = False
    https: bool = False
    url: Optional[str] = None  # 如果提供 url，则优先使用 url
    
    @classmethod
    def from_env(cls, host: Optional[str] = None, port: Optional[int] = None) -> 'QdrantConfig':
        """从环境变量创建配置
        
        Args:
            host: Qdrant 主机，如果为 None 则从环境变量 QDRANT_HOST 读取，默认为 127.0.0.1
            port: Qdrant 端口，如果为 None 则从环境变量 QDRANT_PORT 读取，默认为 6333
            
        Returns:
            QdrantConfig: 配置对象
        """
        return cls(
            host=host or os.getenv('QDRANT_HOST', '127.0.0.1'),
            port=port or int(os.getenv('QDRANT_PORT', '6333')),
            api_key=os.getenv('QDRANT_API_KEY'),
            timeout=int(os.getenv('QDRANT_TIMEOUT', '30')),
            retry_count=int(os.getenv('QDRANT_RETRY_COUNT', '3')),
            retry_delay=int(os.getenv('QDRANT_RETRY_DELAY', '1')),
            prefer_grpc=os.getenv('QDRANT_PREFER_GRPC', 'false').lower() == 'true',
            https=os.getenv('QDRANT_HTTPS', 'false').lower() == 'true',
            url=os.getenv('QDRANT_URL'),
        )


class QdrantManager:
    """Qdrant 客户端管理器单例类
    
    提供连接管理、重连、重试等稳定性机制
    提供基础 CRUD 接口和 hook 机制
    """
    _instance: Optional['QdrantManager'] = None
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
        
        self._config: Optional[QdrantConfig] = None
        self._client: Optional[QdrantClient] = None
        self._is_connected = False
        self._last_check_time = 0
        self._check_interval = 30  # 连接检查间隔（秒）
        self._hooks: Dict[str, List[Callable]] = {
            'before_query': [],
            'after_query': [],
            'before_create_collection': [],
            'after_create_collection': [],
            'before_delete_collection': [],
            'after_delete_collection': [],
        }
        self._initialized = True
    
    def initialize(self, config: QdrantConfig):
        """初始化 Qdrant 客户端
        
        Args:
            config: Qdrant 配置
            
        Raises:
            QdrantError: 初始化失败时抛出
        """
        if self._is_connected:
            logger.warning("Qdrant 已经初始化，跳过重复初始化")
            return
        
        self._config = config
        
        try:
            # 临时清除代理环境变量，强制禁用代理
            proxy_env_vars = [
                'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
                'ALL_PROXY', 'all_proxy', 'SOCKS_PROXY', 'socks_proxy',
                'NO_PROXY', 'no_proxy'
            ]
            saved_proxy_vars = {}
            for var in proxy_env_vars:
                if var in os.environ:
                    saved_proxy_vars[var] = os.environ.pop(var)
            
            try:
                # 创建客户端
                if config.url:
                    # 使用 URL 连接
                    self._client = QdrantClient(
                        url=config.url,
                        api_key=config.api_key,
                        timeout=config.timeout,
                        prefer_grpc=config.prefer_grpc,
                    )
                else:
                    # 使用 host:port 连接
                    self._client = QdrantClient(
                        host=config.host,
                        port=config.port,
                        api_key=config.api_key,
                        timeout=config.timeout,
                        prefer_grpc=config.prefer_grpc,
                        https=config.https,
                    )
                
                # 测试连接
                self._client.get_collections()
                
                self._is_connected = True
                self._last_check_time = time.time()
                
                logger.info(f"Qdrant 客户端初始化成功: {config.url or f'{config.host}:{config.port}'}")
            finally:
                # 恢复代理环境变量
                for var, value in saved_proxy_vars.items():
                    os.environ[var] = value
            
        except qdrant_exceptions.UnexpectedResponse as e:
            self._is_connected = False
            self._client = None
            logger.error(f"Qdrant 初始化失败 - 响应错误: {str(e)}")
            raise QdrantError(f"初始化失败 - 响应错误: {str(e)}")
        except qdrant_exceptions.ResponseHandlingException as e:
            self._is_connected = False
            self._client = None
            logger.error(f"Qdrant 初始化失败 - 响应处理错误: {str(e)}")
            raise QdrantError(f"初始化失败 - 响应处理错误: {str(e)}")
        except Exception as e:
            self._is_connected = False
            self._client = None
            logger.error(f"Qdrant 初始化失败: {str(e)}")
            raise QdrantError(f"初始化失败: {str(e)}")
    
    def _check_connection(self) -> bool:
        """检查连接是否有效
        
        Returns:
            bool: 连接是否有效
        """
        if not self._client or not self._is_connected:
            return False
        
        # 避免频繁检查
        current_time = time.time()
        if current_time - self._last_check_time < self._check_interval:
            return True
        
        try:
            # 执行简单查询测试连接
            self._client.get_collections()
            self._last_check_time = current_time
            return True
            
        except Exception as e:
            logger.warning(f"连接检查失败: {str(e)}")
            self._is_connected = False
            return False
    
    def _reconnect(self) -> bool:
        """重新连接
        
        Returns:
            bool: 重连是否成功
        """
        if not self._config:
            return False
        
        logger.info("尝试重新连接 Qdrant...")
        
        try:
            # 关闭旧连接
            if self._client:
                self._client = None
            
            # 重新初始化
            self.initialize(self._config)
            return True
            
        except Exception as e:
            logger.error(f"重连失败: {str(e)}")
            return False
    
    def _get_client(self) -> QdrantClient:
        """获取客户端（带重连机制）
        
        Returns:
            QdrantClient: Qdrant 客户端对象
            
        Raises:
            QdrantError: 获取客户端失败时抛出
        """
        if not self._check_connection():
            if not self._reconnect():
                raise QdrantError("无法连接到 Qdrant，请检查配置和网络")
        
        return self._client
    
    def _execute_with_retry(self, func: Callable, *args, retry_count: Optional[int] = None, **kwargs) -> Any:
        """执行操作（带重试机制）
        
        Args:
            func: 要执行的函数
            *args: 函数位置参数
            retry_count: 重试次数，None 则使用配置中的值
            **kwargs: 函数关键字参数
            
        Returns:
            Any: 函数执行结果
            
        Raises:
            QdrantError: 执行失败时抛出
        """
        if retry_count is None:
            retry_count = self._config.retry_count if self._config else 3
        
        last_error = None
        for attempt in range(retry_count + 1):
            try:
                client = self._get_client()
                result = func(client, *args, **kwargs)
                return result
                
            except qdrant_exceptions.UnexpectedResponse as e:
                last_error = QdrantError(f"响应错误: {str(e)}")
                if attempt < retry_count:
                    time.sleep(self._config.retry_delay if self._config else 1)
                    self._is_connected = False
                    continue
                    
            except qdrant_exceptions.ResponseHandlingException as e:
                last_error = QdrantError(f"响应处理错误: {str(e)}")
                if attempt < retry_count:
                    time.sleep(self._config.retry_delay if self._config else 1)
                    self._is_connected = False
                    continue
                    
            except Exception as e:
                last_error = QdrantError(f"执行操作时发生错误: {str(e)}")
                # 如果是连接相关错误，尝试重连
                error_msg = str(e).lower()
                if "connection" in error_msg or "timeout" in error_msg or "network" in error_msg:
                    self._is_connected = False
                    if attempt < retry_count:
                        time.sleep(self._config.retry_delay if self._config else 1)
                        continue
                elif attempt < retry_count:
                    time.sleep(self._config.retry_delay if self._config else 1)
                    continue
        
        raise last_error or QdrantError("操作执行失败")
    
    def register_hook(self, event: str, hook: Callable):
        """注册 hook
        
        Args:
            event: 事件名称
            hook: hook 函数
        """
        if event not in self._hooks:
            raise ValueError(f"未知的事件类型: {event}")
        
        self._hooks[event].append(hook)
        logger.debug(f"注册 hook: {event}")
    
    def unregister_hook(self, event: str, hook: Callable):
        """取消注册 hook
        
        Args:
            event: 事件名称
            hook: hook 函数
        """
        if event in self._hooks and hook in self._hooks[event]:
            self._hooks[event].remove(hook)
            logger.debug(f"取消注册 hook: {event}")
    
    def get_collections(self) -> List[str]:
        """获取所有集合名称
        
        Returns:
            List[str]: 集合名称列表
        """
        if not self._is_connected:
            raise QdrantError("Qdrant 未初始化，请先调用 initialize()")
        
        def _get_collections(client):
            collections = client.get_collections()
            return [col.name for col in collections.collections]
        
        return self._execute_with_retry(_get_collections)
    
    def create_collection(
        self,
        collection_name: str,
        vectors_config: Union[VectorParams, Dict[str, Any]],
        **kwargs
    ) -> bool:
        """创建集合
        
        Args:
            collection_name: 集合名称
            vectors_config: 向量配置
            **kwargs: 其他参数
            
        Returns:
            bool: 是否创建成功
        """
        if not self._is_connected:
            raise QdrantError("Qdrant 未初始化，请先调用 initialize()")
        
        # 执行 hook
        for hook in self._hooks.get('before_create_collection', []):
            hook(collection_name, vectors_config, **kwargs)
        
        def _create_collection(client, name, config, **kw):
            client.create_collection(
                collection_name=name,
                vectors_config=config,
                **kw
            )
            return True
        
        result = self._execute_with_retry(_create_collection, collection_name, vectors_config, **kwargs)
        
        # 执行 hook
        for hook in self._hooks.get('after_create_collection', []):
            hook(collection_name, result)
        
        return result
    
    def delete_collection(self, collection_name: str) -> bool:
        """删除集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 是否删除成功
        """
        if not self._is_connected:
            raise QdrantError("Qdrant 未初始化，请先调用 initialize()")
        
        # 执行 hook
        for hook in self._hooks.get('before_delete_collection', []):
            hook(collection_name)
        
        def _delete_collection(client, name):
            client.delete_collection(collection_name=name)
            return True
        
        result = self._execute_with_retry(_delete_collection, collection_name)
        
        # 执行 hook
        for hook in self._hooks.get('after_delete_collection', []):
            hook(collection_name, result)
        
        return result
    
    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 集合是否存在
        """
        if not self._is_connected:
            raise QdrantError("Qdrant 未初始化，请先调用 initialize()")
        
        def _collection_exists(client, name):
            try:
                client.get_collection(name)
                return True
            except qdrant_exceptions.UnexpectedResponse:
                return False
        
        return self._execute_with_retry(_collection_exists, collection_name)
    
    def upsert_points(
        self,
        collection_name: str,
        points: List[PointStruct],
        **kwargs
    ) -> UpdateStatus:
        """插入或更新点
        
        Args:
            collection_name: 集合名称
            points: 点列表
            **kwargs: 其他参数
            
        Returns:
            UpdateStatus: 更新状态
        """
        if not self._is_connected:
            raise QdrantError("Qdrant 未初始化，请先调用 initialize()")
        
        def _upsert_points(client, name, pts, **kw):
            return client.upsert(
                collection_name=name,
                points=pts,
                **kw
            )
        
        return self._execute_with_retry(_upsert_points, collection_name, points, **kwargs)
    
    def search_points(
        self,
        collection_name: str,
        query_vector: Union[List[float], str],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter: Optional[Filter] = None,
        **kwargs
    ) -> List[Any]:
        """搜索点
        
        Args:
            collection_name: 集合名称
            query_vector: 查询向量或命名向量
            limit: 返回结果数量
            score_threshold: 分数阈值
            filter: 过滤条件
            **kwargs: 其他参数
            
        Returns:
            List[Any]: 搜索结果列表
        """
        if not self._is_connected:
            raise QdrantError("Qdrant 未初始化，请先调用 initialize()")
        
        # 执行 hook
        for hook in self._hooks.get('before_query', []):
            query_vector = hook(collection_name, query_vector) or query_vector
        
        def _search_points(client, name, qv, lim, st, flt, **kw):
            return client.search(
                collection_name=name,
                query_vector=qv,
                limit=lim,
                score_threshold=st,
                query_filter=flt,
                **kw
            )
        
        result = self._execute_with_retry(
            _search_points,
            collection_name,
            query_vector,
            limit,
            score_threshold,
            filter,
            **kwargs
        )
        
        # 执行 hook
        for hook in self._hooks.get('after_query', []):
            hook(collection_name, query_vector, result)
        
        return result
    
    def delete_points(
        self,
        collection_name: str,
        points_selector: Union[List[int], Filter],
        **kwargs
    ) -> UpdateStatus:
        """删除点
        
        Args:
            collection_name: 集合名称
            points_selector: 点选择器（ID列表或过滤条件）
            **kwargs: 其他参数
            
        Returns:
            UpdateStatus: 更新状态
        """
        if not self._is_connected:
            raise QdrantError("Qdrant 未初始化，请先调用 initialize()")
        
        def _delete_points(client, name, selector, **kw):
            return client.delete(
                collection_name=name,
                points_selector=selector,
                **kw
            )
        
        return self._execute_with_retry(_delete_points, collection_name, points_selector, **kwargs)
    
    def get_point(self, collection_name: str, point_id: Union[int, str], **kwargs) -> Optional[Any]:
        """获取单个点
        
        Args:
            collection_name: 集合名称
            point_id: 点ID
            **kwargs: 其他参数
            
        Returns:
            Optional[Any]: 点对象，不存在则返回 None
        """
        if not self._is_connected:
            raise QdrantError("Qdrant 未初始化，请先调用 initialize()")
        
        def _get_point(client, name, pid, **kw):
            result = client.retrieve(
                collection_name=name,
                ids=[pid],
                **kw
            )
            return result[0] if result else None
        
        return self._execute_with_retry(_get_point, collection_name, point_id, **kwargs)
    
    def close(self):
        """关闭客户端连接"""
        if self._client:
            # QdrantClient 没有显式的 close 方法，设置为 None 即可
            self._client = None
            self._is_connected = False
            logger.info("Qdrant 客户端已关闭")
    
    def is_connected(self) -> bool:
        """检查是否已连接
        
        Returns:
            bool: 是否已连接
        """
        return self._is_connected and self._check_connection()


# 创建全局单例实例
qdrant_manager = QdrantManager()


class ContextAwareQdrantManager:
    """支持从 context 自动获取 tenant 和 company 的 Qdrant 管理器包装类
    
    在查询和更新操作时自动添加 tenant 和 company 过滤条件
    支持手动指定 tenant 和 company（覆盖 context 中的值）
    """
    
    def __init__(
        self,
        manager: QdrantManager,
        auth_tenant_id: Optional[str] = None,
        auth_company_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """初始化 ContextAwareQdrantManager
        
        Args:
            manager: QdrantManager 实例
            auth_tenant_id: 租户ID，如果为 None 则从 context 获取
            auth_company_id: 公司ID，如果为 None 则从 context 获取
            user_id: 用户ID，如果为 None 则从 context 获取（可选，用于记录）
        """
        self._manager = manager
        self._auth_tenant_id = auth_tenant_id
        self._auth_company_id = auth_company_id
        self._user_id = user_id
    
    def _get_auth_context(self) -> Dict[str, Optional[str]]:
        """从 context 获取认证信息
        
        Returns:
            Dict[str, Optional[str]]: 包含 auth_tenant_id, auth_company_id, user_id 的字典
        """
        try:
            from pkg.context import get_auth_data
            auth_data = get_auth_data()
            if auth_data:
                return {
                    'auth_tenant_id': auth_data.auth_tenant_id,
                    'auth_company_id': auth_data.current_company,
                    'user_id': auth_data.user_id,
                }
        except Exception as e:
            logger.warning(f"Failed to get auth context: {e}")
        
        return {
            'auth_tenant_id': None,
            'auth_company_id': None,
            'user_id': None,
        }
    
    def _get_tenant_id(self) -> Optional[str]:
        """获取租户ID，优先使用手动指定的，否则从 context 获取"""
        if self._auth_tenant_id:
            return self._auth_tenant_id
        context = self._get_auth_context()
        return context.get('auth_tenant_id')
    
    def _get_company_id(self) -> Optional[str]:
        """获取公司ID，优先使用手动指定的，否则从 context 获取"""
        if self._auth_company_id:
            return self._auth_company_id
        context = self._get_auth_context()
        return context.get('auth_company_id')
    
    def _get_user_id(self) -> Optional[str]:
        """获取用户ID，优先使用手动指定的，否则从 context 获取"""
        if self._user_id:
            return self._user_id
        context = self._get_auth_context()
        return context.get('user_id')
    
    def _build_context_filter(self, existing_filter: Optional[Filter] = None) -> Optional[Filter]:
        """构建包含 tenant 和 company 的过滤条件
        
        Args:
            existing_filter: 已存在的过滤条件
            
        Returns:
            Optional[Filter]: 合并后的过滤条件
        """
        tenant_id = self._get_tenant_id()
        company_id = self._get_company_id()
        
        if not tenant_id and not company_id:
            # 如果没有 tenant 和 company，返回原有过滤条件
            return existing_filter
        
        conditions = []
        
        if tenant_id:
            conditions.append(
                FieldCondition(
                    key="auth_tenant_id",
                    match=MatchValue(value=tenant_id)
                )
            )
        
        if company_id:
            conditions.append(
                FieldCondition(
                    key="auth_company_id",
                    match=MatchValue(value=company_id)
                )
            )
        
        if not conditions:
            return existing_filter
        
        # 如果有多个条件，使用 must 组合
        if len(conditions) == 1:
            context_filter = Filter(must=[conditions[0]])
        else:
            context_filter = Filter(must=conditions)
        
        # 如果已有过滤条件，需要合并
        if existing_filter:
            if existing_filter.must:
                # 合并 must 条件
                combined_must = existing_filter.must + context_filter.must
                return Filter(
                    must=combined_must,
                    must_not=existing_filter.must_not,
                    should=existing_filter.should,
                )
            else:
                # 如果原过滤条件没有 must，则创建新的 must 列表
                return Filter(
                    must=context_filter.must,
                    must_not=existing_filter.must_not,
                    should=existing_filter.should,
                )
        
        return context_filter
    
    def _ensure_context_in_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """确保 payload 中包含 tenant 和 company 信息
        
        Args:
            payload: 点的 payload 字典
            
        Returns:
            Dict[str, Any]: 包含 tenant 和 company 的 payload
        """
        if not isinstance(payload, dict):
            payload = {}
        
        tenant_id = self._get_tenant_id()
        company_id = self._get_company_id()
        user_id = self._get_user_id()
        
        if tenant_id:
            payload['auth_tenant_id'] = tenant_id
        if company_id:
            payload['auth_company_id'] = company_id
        if user_id:
            payload['auth_user_id'] = user_id
        
        return payload
    
    # 代理 QdrantManager 的所有方法，并在需要时添加 context 过滤
    
    def get_collections(self) -> List[str]:
        """获取所有集合名称"""
        return self._manager.get_collections()
    
    def create_collection(
        self,
        collection_name: str,
        vectors_config: Union[VectorParams, Dict[str, Any]],
        **kwargs
    ) -> bool:
        """创建集合"""
        return self._manager.create_collection(collection_name, vectors_config, **kwargs)
    
    def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        return self._manager.delete_collection(collection_name)
    
    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        return self._manager.collection_exists(collection_name)
    
    def upsert_points(
        self,
        collection_name: str,
        points: List[PointStruct],
        **kwargs
    ) -> UpdateStatus:
        """插入或更新点（自动添加 tenant 和 company 信息）"""
        # 确保每个点的 payload 都包含 tenant 和 company
        updated_points = []
        for point in points:
            # 获取现有 payload 或创建新字典
            existing_payload = point.payload if point.payload else {}
            # 确保包含 context 信息
            updated_payload = self._ensure_context_in_payload(
                existing_payload.copy() if isinstance(existing_payload, dict) else {}
            )
            # 创建新的 PointStruct 对象
            updated_point = PointStruct(
                id=point.id,
                vector=point.vector,
                payload=updated_payload,
            )
            updated_points.append(updated_point)
        
        return self._manager.upsert_points(collection_name, updated_points, **kwargs)
    
    def search_points(
        self,
        collection_name: str,
        query_vector: Union[List[float], str],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter: Optional[Filter] = None,
        **kwargs
    ) -> List[Any]:
        """搜索点（自动添加 tenant 和 company 过滤条件）"""
        # 构建包含 context 的过滤条件
        context_filter = self._build_context_filter(filter)
        return self._manager.search_points(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filter=context_filter,
            **kwargs
        )
    
    def delete_points(
        self,
        collection_name: str,
        points_selector: Union[List[int], Filter],
        **kwargs
    ) -> UpdateStatus:
        """删除点（自动添加 tenant 和 company 过滤条件）"""
        # 如果 points_selector 是 Filter，需要添加 context 过滤
        if isinstance(points_selector, Filter):
            context_filter = self._build_context_filter(points_selector)
            return self._manager.delete_points(collection_name, context_filter, **kwargs)
        else:
            # 如果是 ID 列表，无法添加过滤条件，直接删除
            # 注意：这种情况下不会自动过滤，需要确保调用者知道自己在做什么
            return self._manager.delete_points(collection_name, points_selector, **kwargs)
    
    def get_point(self, collection_name: str, point_id: Union[int, str], **kwargs) -> Optional[Any]:
        """获取单个点"""
        return self._manager.get_point(collection_name, point_id, **kwargs)
    
    def close(self):
        """关闭客户端连接"""
        self._manager.close()
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._manager.is_connected()
    
    def register_hook(self, event: str, hook: Callable):
        """注册 hook"""
        self._manager.register_hook(event, hook)
    
    def unregister_hook(self, event: str, hook: Callable):
        """取消注册 hook"""
        self._manager.unregister_hook(event, hook)

