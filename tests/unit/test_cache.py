"""
缓存模块测试
"""

import pytest
import time
from unittest.mock import MagicMock

from safesql_mcp.utils.cache import CacheConfig, QueryCache, CacheManager


class TestCacheConfig:
    """CacheConfig 测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = CacheConfig()
        
        assert config.enabled is True
        assert config.max_size == 1000
        assert config.ttl == 300
        assert config.key_prefix == "safesql"
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = CacheConfig(
            enabled=False,
            max_size=500,
            ttl=60,
            key_prefix="test"
        )
        
        assert config.enabled is False
        assert config.max_size == 500
        assert config.ttl == 60
        assert config.key_prefix == "test"


class TestQueryCache:
    """QueryCache 测试"""
    
    def test_cache_disabled(self):
        """测试禁用缓存"""
        config = CacheConfig(enabled=False)
        cache = QueryCache(config)
        
        # 设置和获取应该返回 None
        cache.set("SELECT 1", {"result": "value"})
        result = cache.get("SELECT 1")
        
        assert result is None
    
    def test_cache_enabled(self):
        """测试启用缓存"""
        config = CacheConfig(enabled=True, max_size=10, ttl=60)
        cache = QueryCache(config)
        
        # 设置和获取
        cache.set("SELECT 1", {"result": "value"})
        result = cache.get("SELECT 1")
        
        assert result == {"result": "value"}
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        config = CacheConfig(enabled=True)
        cache = QueryCache(config)
        
        result = cache.get("SELECT 1")
        assert result is None
    
    def test_cache_invalidate(self):
        """测试缓存失效"""
        config = CacheConfig(enabled=True)
        cache = QueryCache(config)
        
        cache.set("SELECT 1", {"result": "value"})
        cache.invalidate("SELECT 1")
        
        result = cache.get("SELECT 1")
        assert result is None
    
    def test_cache_invalidate_all(self):
        """测试清空所有缓存"""
        config = CacheConfig(enabled=True)
        cache = QueryCache(config)
        
        cache.set("SELECT 1", {"result": "value1"})
        cache.set("SELECT 2", {"result": "value2"})
        cache.invalidate_all()
        
        assert cache.get("SELECT 1") is None
        assert cache.get("SELECT 2") is None
    
    def test_cache_stats(self):
        """测试缓存统计"""
        config = CacheConfig(enabled=True, max_size=10)
        cache = QueryCache(config)
        
        # 生成一些缓存操作
        cache.set("SELECT 1", {"result": "value1"})
        cache.get("SELECT 1")  # 命中
        cache.get("SELECT 2")  # 未命中
        
        stats = cache.get_stats()
        
        assert stats["enabled"] is True
        assert stats["max_size"] == 10
        assert stats["current_size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0
    
    def test_cache_is_cacheable(self):
        """测试可缓存性检查"""
        config = CacheConfig(enabled=True)
        cache = QueryCache(config)
        
        # SELECT 查询应该可缓存
        assert cache.is_cacheable("SELECT * FROM users") is True
        
        # INSERT 查询不应该可缓存
        assert cache.is_cacheable("INSERT INTO users VALUES (1)") is False
        
        # UPDATE 查询不应该可缓存
        assert cache.is_cacheable("UPDATE users SET name = 'test'") is False
        
        # DELETE 查询不应该可缓存
        assert cache.is_cacheable("DELETE FROM users") is False
        
        # 包含随机函数的查询不应该可缓存
        assert cache.is_cacheable("SELECT RANDOM()") is False
        
        # 包含时间函数的查询不应该可缓存
        assert cache.is_cacheable("SELECT NOW()") is False


class TestCacheManager:
    """CacheManager 测试"""
    
    def test_cache_manager_init(self):
        """测试缓存管理器初始化"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        assert manager.cache is not None
        assert len(manager._invalidation_patterns) == 0
    
    def test_add_invalidation_pattern(self):
        """测试添加失效模式"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        manager.add_invalidation_pattern("users")
        assert "users" in manager._invalidation_patterns
    
    def test_should_invalidate_write_operations(self):
        """测试写操作应该失效缓存"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 写操作应该失效缓存
        assert manager.should_invalidate("INSERT INTO users VALUES (1)") is True
        assert manager.should_invalidate("UPDATE users SET name = 'test'") is True
        assert manager.should_invalidate("DELETE FROM users") is True
        assert manager.should_invalidate("DROP TABLE users") is True
        
        # SELECT 查询不应该失效缓存
        assert manager.should_invalidate("SELECT * FROM users") is False
    
    def test_should_invalidate_with_patterns(self):
        """测试带模式的缓存失效"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        manager.add_invalidation_pattern("users")
        
        # 匹配模式的查询应该失效缓存
        assert manager.should_invalidate("SELECT * FROM users") is True
        
        # 不匹配模式的查询不应该失效缓存
        assert manager.should_invalidate("SELECT * FROM orders") is False
    
    def test_invalidate_for_sql(self):
        """测试根据 SQL 失效缓存"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 设置缓存
        manager.cache.set("SELECT * FROM users", {"result": "value"})
        
        # 使缓存失效
        manager.invalidate_for_sql("INSERT INTO users VALUES (1)")
        
        # 缓存应该被清空
        assert manager.cache.get("SELECT * FROM users") is None
    
    def test_get_stats(self):
        """测试获取统计信息"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        stats = manager.get_stats()
        
        assert "enabled" in stats
        assert "max_size" in stats
        assert "ttl" in stats
        assert "invalidation_patterns" in stats