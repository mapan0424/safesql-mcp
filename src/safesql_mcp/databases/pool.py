"""
数据库连接池管理
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """连接池配置"""
    min_size: int = 1
    max_size: int = 10
    max_idle_time: float = 300.0  # 5分钟
    max_lifetime: float = 3600.0  # 1小时
    timeout: float = 30.0  # 连接超时
    retry_attempts: int = 3
    retry_delay: float = 1.0


class ConnectionPool(ABC):
    """数据库连接池基类"""
    
    def __init__(self, config: PoolConfig):
        self.config = config
        self._pool: List[Any] = []
        self._in_use: Dict[int, Any] = {}
        self._created_at: Dict[int, float] = {}
        self._last_used: Dict[int, float] = {}
        self._lock = asyncio.Lock()
        self._closed = False
        
    @abstractmethod
    async def _create_connection(self) -> Any:
        """创建新连接"""
        pass
    
    @abstractmethod
    async def _close_connection(self, conn: Any) -> None:
        """关闭连接"""
        pass
    
    @abstractmethod
    async def _validate_connection(self, conn: Any) -> bool:
        """验证连接是否有效"""
        pass
    
    async def acquire(self) -> Any:
        """获取连接"""
        if self._closed:
            raise RuntimeError("Pool is closed")
        
        async with self._lock:
            # 尝试从池中获取空闲连接
            while self._pool:
                conn = self._pool.pop()
                conn_id = id(conn)
                
                # 检查连接是否过期
                if self._is_connection_expired(conn_id):
                    await self._close_connection(conn)
                    continue
                
                # 验证连接
                if await self._validate_connection(conn):
                    self._in_use[conn_id] = conn
                    self._last_used[conn_id] = time.time()
                    return conn
                else:
                    await self._close_connection(conn)
            
            # 如果池为空且未达到最大大小，创建新连接
            if len(self._in_use) < self.config.max_size:
                conn = await self._create_connection_with_retry()
                conn_id = id(conn)
                self._in_use[conn_id] = conn
                self._created_at[conn_id] = time.time()
                self._last_used[conn_id] = time.time()
                return conn
            
            # 等待连接释放
            raise RuntimeError("No available connections in pool")
    
    async def release(self, conn: Any) -> None:
        """释放连接"""
        async with self._lock:
            conn_id = id(conn)
            if conn_id in self._in_use:
                del self._in_use[conn_id]
                self._last_used[conn_id] = time.time()
                
                # 检查是否需要保持连接
                if len(self._pool) < self.config.min_size:
                    self._pool.append(conn)
                else:
                    await self._close_connection(conn)
    
    async def _create_connection_with_retry(self) -> Any:
        """带重试的连接创建"""
        last_error = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                return await self._create_connection()
            except Exception as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        raise last_error
    
    def _is_connection_expired(self, conn_id: int) -> bool:
        """检查连接是否过期"""
        now = time.time()
        
        # 检查最大生命周期
        if conn_id in self._created_at:
            if now - self._created_at[conn_id] > self.config.max_lifetime:
                return True
        
        # 检查空闲时间
        if conn_id in self._last_used:
            if now - self._last_used[conn_id] > self.config.max_idle_time:
                return True
        
        return False
    
    async def close(self) -> None:
        """关闭连接池"""
        async with self._lock:
            self._closed = True
            
            # 关闭所有空闲连接
            for conn in self._pool:
                await self._close_connection(conn)
            self._pool.clear()
            
            # 关闭所有使用中的连接
            for conn in self._in_use.values():
                await self._close_connection(conn)
            self._in_use.clear()
            
            self._created_at.clear()
            self._last_used.clear()
    
    @asynccontextmanager
    async def connection(self):
        """连接上下文管理器"""
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)
    
    @property
    def size(self) -> int:
        """当前池大小"""
        return len(self._pool) + len(self._in_use)
    
    @property
    def available(self) -> int:
        """可用连接数"""
        return len(self._pool)
    
    @property
    def in_use(self) -> int:
        """使用中的连接数"""
        return len(self._in_use)
    
    def stats(self) -> Dict[str, Any]:
        """获取池统计信息"""
        return {
            "total_size": self.size,
            "available": self.available,
            "in_use": self.in_use,
            "max_size": self.config.max_size,
            "min_size": self.config.min_size,
            "closed": self._closed
        }