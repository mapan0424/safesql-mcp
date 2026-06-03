"""
查询缓存模块
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import OrderedDict
import threading

from cachetools import TTLCache


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    max_size: int = 1000
    ttl: int = 300  # 5分钟
    key_prefix: str = "safesql"


class QueryCache:
    """查询缓存"""
    
    def __init__(self, config: CacheConfig):
        """
        初始化缓存
        
        Args:
            config: 缓存配置
        """
        self.config = config
        self._cache: Optional[TTLCache] = None
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
        
        if config.enabled:
            self._cache = TTLCache(
                maxsize=config.max_size,
                ttl=config.ttl
            )
    
    def _generate_key(self, sql: str, params: Optional[Tuple] = None, database: str = "") -> str:
        """
        生成缓存键
        
        Args:
            sql: SQL 语句
            params: 查询参数
            database: 数据库名称
            
        Returns:
            str: 缓存键
        """
        # 构建键字符串
        key_parts = [database, sql]
        if params:
            key_parts.append(str(params))
        
        # 生成哈希
        key_string = ":".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{self.config.key_prefix}:{key_hash}"
    
    def get(self, sql: str, params: Optional[Tuple] = None, database: str = "") -> Optional[Any]:
        """
        获取缓存结果
        
        Args:
            sql: SQL 语句
            params: 查询参数
            database: 数据库名称
            
        Returns:
            Optional[Any]: 缓存的结果，如果不存在则返回 None
        """
        if not self.config.enabled or self._cache is None:
            return None
        
        key = self._generate_key(sql, params, database)
        
        with self._lock:
            result = self._cache.get(key)
            if result is not None:
                self._stats["hits"] += 1
                return result
            else:
                self._stats["misses"] += 1
                return None
    
    def set(self, sql: str, result: Any, params: Optional[Tuple] = None, database: str = "") -> None:
        """
        设置缓存结果
        
        Args:
            sql: SQL 语句
            result: 查询结果
            params: 查询参数
            database: 数据库名称
        """
        if not self.config.enabled or self._cache is None:
            return
        
        key = self._generate_key(sql, params, database)
        
        with self._lock:
            # 检查是否会导致驱逐
            if len(self._cache) >= self.config.max_size:
                self._stats["evictions"] += 1
            
            self._cache[key] = result
            self._stats["size"] = len(self._cache)
    
    def invalidate(self, sql: str, params: Optional[Tuple] = None, database: str = "") -> None:
        """
        使缓存失效
        
        Args:
            sql: SQL 语句
            params: 查询参数
            database: 数据库名称
        """
        if not self.config.enabled or self._cache is None:
            return
        
        key = self._generate_key(sql, params, database)
        
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["size"] = len(self._cache)
    
    def invalidate_all(self) -> None:
        """清空所有缓存"""
        if not self.config.enabled or self._cache is None:
            return
        
        with self._lock:
            self._cache.clear()
            self._stats["size"] = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 缓存统计信息
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "enabled": self.config.enabled,
                "max_size": self.config.max_size,
                "ttl": self.config.ttl,
                "current_size": self._stats["size"],
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate": round(hit_rate, 2),
                "total_requests": total_requests
            }
    
    def is_cacheable(self, sql: str) -> bool:
        """
        检查 SQL 是否可缓存
        
        Args:
            sql: SQL 语句
            
        Returns:
            bool: 是否可缓存
        """
        # 只缓存 SELECT 查询
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return False
        
        # 不缓存包含随机函数的查询
        random_functions = ["RANDOM()", "RAND()", "NEWID()", "UUID()"]
        for func in random_functions:
            if func in sql_upper:
                return False
        
        # 不缓存包含时间函数的查询
        time_functions = ["NOW()", "CURRENT_TIMESTAMP", "CURRENT_DATE", "GETDATE()"]
        for func in time_functions:
            if func in sql_upper:
                return False
        
        return True


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config: CacheConfig):
        """
        初始化缓存管理器
        
        Args:
            config: 缓存配置
        """
        self.config = config
        self._cache = QueryCache(config)
        self._invalidation_patterns: List[str] = []
    
    @property
    def cache(self) -> QueryCache:
        """获取缓存实例"""
        return self._cache
    
    def add_invalidation_pattern(self, pattern: str) -> None:
        """
        添加缓存失效模式
        
        Args:
            pattern: 表名或模式
        """
        self._invalidation_patterns.append(pattern)
    
    def should_invalidate(self, sql: str) -> bool:
        """
        检查是否应该使缓存失效
        
        Args:
            sql: SQL 语句
            
        Returns:
            bool: 是否应该失效
        """
        sql_upper = sql.strip().upper()
        
        # 检查是否是写操作
        write_operations = ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER"]
        for op in write_operations:
            if sql_upper.startswith(op):
                return True
        
        # 检查是否匹配失效模式
        for pattern in self._invalidation_patterns:
            if pattern.upper() in sql_upper:
                return True
        
        return False
    
    def invalidate_for_sql(self, sql: str) -> None:
        """
        根据 SQL 语句使缓存失效
        
        Args:
            sql: SQL 语句
        """
        if self.should_invalidate(sql):
            # 简单策略：清空所有缓存
            # 更复杂的策略可以只失效相关的缓存
            self._cache.invalidate_all()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 缓存统计信息
        """
        stats = self._cache.get_stats()
        stats["invalidation_patterns"] = self._invalidation_patterns
        return stats