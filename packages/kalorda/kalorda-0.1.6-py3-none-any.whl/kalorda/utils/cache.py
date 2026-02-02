import threading
from typing import Any, Optional

import cachetools

from kalorda.utils.logger import logger


class CacheManager:
    """线程安全的缓存管理器"""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CacheManager, cls).__new__(cls)
                # 初始化缓存实例
                cls._instance._cache = cachetools.TTLCache(maxsize=100, ttl=5 * 60)
                cls._instance._cache_lock = threading.RLock()
        return cls._instance

    def set(self, key: str, value: Any) -> None:
        """
        设置缓存项
        :param key: 缓存键
        :param value: 缓存值
        """
        with self._cache_lock:
            try:
                self._cache[key] = value
                logger.debug(f"Cache set: {key}")
            except Exception as e:
                logger.error(f"Error setting cache: {str(e)}")
                raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存项
        :param key: 缓存键
        :param default: 键不存在时返回的默认值
        :return: 缓存值或默认值
        """
        with self._cache_lock:
            try:
                value = self._cache.get(key, default)
                logger.debug(f"Cache get: {key}, found: {value is not default}")
                return value
            except Exception as e:
                logger.error(f"Error getting cache: {str(e)}")
                return default

    def delete(self, key: str) -> bool:
        """
        删除缓存项
        :param key: 缓存键
        :return: 是否成功删除
        """
        with self._cache_lock:
            try:
                if key in self._cache:
                    self._cache.pop(key)
                    logger.debug(f"Cache deleted: {key}")
                    return True
                return False
            except Exception as e:
                logger.error(f"Error deleting cache: {str(e)}")
                return False

    def clear(self, pattern: Optional[str] = None) -> None:
        """
        清空缓存或根据模式清空部分缓存
        :param pattern: 可选的键模式，支持简单的前缀匹配
        """
        with self._cache_lock:
            try:
                if pattern:
                    # 简单的前缀匹配
                    keys_to_remove = [k for k in self._cache if isinstance(k, str) and k.startswith(pattern)]
                    for key in keys_to_remove:
                        self._cache.pop(key)
                    logger.debug(f"Cache cleared with pattern '{pattern}', removed {len(keys_to_remove)} items")
                else:
                    self._cache.clear()
                    logger.debug("Cache completely cleared")
            except Exception as e:
                logger.error(f"Error clearing cache: {str(e)}")
                raise

    def size(self) -> int:
        """
        获取缓存当前大小
        :return: 缓存项数量
        """
        with self._cache_lock:
            return len(self._cache)

    def contains(self, key: str) -> bool:
        """
        检查缓存中是否存在指定键
        :param key: 缓存键
        :return: 是否存在
        """
        with self._cache_lock:
            return key in self._cache


# 创建全局缓存管理器实例
cache_manager = CacheManager()


# 保持原有接口以确保向后兼容性
def set_cache(key: str, value: Any) -> None:
    """设置缓存"""
    cache_manager.set(key, value)


def get_cache(key: str) -> Any:
    """获取缓存，不存在返回None"""
    return cache_manager.get(key)


def clear_cache(key: Optional[str] = None) -> None:
    """
    清除指定缓存项或全部缓存
    :param key: 可选的缓存键，不提供则清空全部缓存
    """
    if key:
        cache_manager.delete(key)
    else:
        cache_manager.clear()
