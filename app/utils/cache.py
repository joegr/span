"""
Simple in-memory cache with LRU eviction
"""
from collections import OrderedDict
from typing import Any, Optional
import time
import threading

class Cache:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """Initialize cache with max size and TTL (in seconds)."""
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.Lock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if it exists and is not expired."""
        with self.lock:
            if key not in self.cache:
                return None
                
            # Check if expired
            if time.time() - self.timestamps[key] > self.ttl:
                self.cache.pop(key)
                self.timestamps.pop(key)
                return None
                
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
            
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with TTL."""
        with self.lock:
            # If key exists, update it
            if key in self.cache:
                self.cache.move_to_end(key)
                self.cache[key] = value
                self.timestamps[key] = time.time()
                return
                
            # If cache is full, remove oldest item
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
                oldest_key = next(iter(self.timestamps))
                self.timestamps.pop(oldest_key)
                
            # Add new item
            self.cache[key] = value
            self.timestamps[key] = time.time()
            
    def clear(self) -> None:
        """Clear all items from cache."""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            
    def remove(self, key: str) -> None:
        """Remove specific key from cache."""
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
                self.timestamps.pop(key)
                
    def cleanup_expired(self) -> None:
        """Remove all expired items from cache."""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                k for k, t in self.timestamps.items()
                if current_time - t > self.ttl
            ]
            for key in expired_keys:
                self.cache.pop(key)
                self.timestamps.pop(key)
                
    def get_size(self) -> int:
        """Get current number of items in cache."""
        return len(self.cache) 