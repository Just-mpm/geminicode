"""
Performance optimization utilities for Gemini Code.
"""

import asyncio
import time
import functools
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import pickle
import weakref


@dataclass
class PerformanceMetric:
    """Performance metric data."""
    function_name: str
    execution_time: float
    memory_usage: Optional[int]
    call_count: int
    timestamp: datetime


class CacheManager:
    """Smart caching manager with TTL and size limits."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = {}
        self._timestamps = {}
        self._access_count = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            if key in self._timestamps:
                age = time.time() - self._timestamps[key]
                if age > self.default_ttl:
                    self._remove(key)
                    return None
            
            # Update access count
            self._access_count[key] = self._access_count.get(key, 0) + 1
            return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        with self._lock:
            # Remove oldest entries if cache is full
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._access_count[key] = 1
    
    def _remove(self, key: str) -> None:
        """Remove key from cache."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_count.pop(key, None)
    
    def _evict_oldest(self) -> None:
        """Evict least recently used items."""
        if not self._timestamps:
            return
        
        # Find 10% oldest entries to remove
        entries_to_remove = max(1, len(self._cache) // 10)
        
        # Sort by access count and timestamp
        sorted_keys = sorted(
            self._timestamps.keys(),
            key=lambda k: (self._access_count.get(k, 0), self._timestamps[k])
        )
        
        for key in sorted_keys[:entries_to_remove]:
            self._remove(key)
    
    def clear(self) -> None:
        """Clear all cache."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._access_count.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': self._calculate_hit_rate(),
                'total_accesses': sum(self._access_count.values())
            }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_accesses = sum(self._access_count.values())
        if total_accesses == 0:
            return 0.0
        return len(self._cache) / total_accesses


class PerformanceMonitor:
    """Performance monitoring and profiling."""
    
    def __init__(self):
        self.metrics = []
        self.function_stats = {}
        self._lock = threading.RLock()
    
    def record_metric(self, metric: PerformanceMetric) -> None:
        """Record a performance metric."""
        with self._lock:
            self.metrics.append(metric)
            
            # Update function statistics
            if metric.function_name not in self.function_stats:
                self.function_stats[metric.function_name] = {
                    'total_time': 0,
                    'call_count': 0,
                    'avg_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0
                }
            
            stats = self.function_stats[metric.function_name]
            stats['total_time'] += metric.execution_time
            stats['call_count'] += 1
            stats['avg_time'] = stats['total_time'] / stats['call_count']
            stats['min_time'] = min(stats['min_time'], metric.execution_time)
            stats['max_time'] = max(stats['max_time'], metric.execution_time)
    
    def get_slow_functions(self, threshold: float = 1.0) -> List[Tuple[str, Dict]]:
        """Get functions slower than threshold."""
        with self._lock:
            slow_functions = []
            for func_name, stats in self.function_stats.items():
                if stats['avg_time'] > threshold:
                    slow_functions.append((func_name, stats))
            
            return sorted(slow_functions, key=lambda x: x[1]['avg_time'], reverse=True)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        with self._lock:
            if not self.function_stats:
                return {"message": "No performance data available"}
            
            total_functions = len(self.function_stats)
            total_calls = sum(stats['call_count'] for stats in self.function_stats.values())
            avg_execution_time = sum(stats['avg_time'] for stats in self.function_stats.values()) / total_functions
            
            # Find bottlenecks
            slowest_functions = sorted(
                self.function_stats.items(),
                key=lambda x: x[1]['avg_time'],
                reverse=True
            )[:5]
            
            most_called = sorted(
                self.function_stats.items(),
                key=lambda x: x[1]['call_count'],
                reverse=True
            )[:5]
            
            return {
                "summary": {
                    "total_functions_monitored": total_functions,
                    "total_function_calls": total_calls,
                    "average_execution_time": avg_execution_time
                },
                "slowest_functions": [
                    {"name": name, "avg_time": stats['avg_time'], "calls": stats['call_count']}
                    for name, stats in slowest_functions
                ],
                "most_called_functions": [
                    {"name": name, "calls": stats['call_count'], "avg_time": stats['avg_time']}
                    for name, stats in most_called
                ]
            }


# Global instances
cache_manager = CacheManager()
performance_monitor = PerformanceMonitor()


def cached(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """Caching decorator with TTL support."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        
        return wrapper
    
    return decorator


def async_cached(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """Async caching decorator."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        
        return wrapper
    
    return decorator


def timed(include_memory: bool = False):
    """Performance timing decorator."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Get memory usage if requested
            memory_before = None
            if include_memory:
                try:
                    import psutil
                    process = psutil.Process()
                    memory_before = process.memory_info().rss
                except ImportError:
                    pass
            
            # Execute function
            try:
                result = func(*args, **kwargs)
                
                # Record performance metric
                execution_time = time.time() - start_time
                memory_usage = None
                
                if include_memory and memory_before:
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_after = process.memory_info().rss
                        memory_usage = memory_after - memory_before
                    except ImportError:
                        pass
                
                metric = PerformanceMetric(
                    function_name=f"{func.__module__}.{func.__name__}",
                    execution_time=execution_time,
                    memory_usage=memory_usage,
                    call_count=1,
                    timestamp=datetime.now()
                )
                
                performance_monitor.record_metric(metric)
                return result
                
            except Exception as e:
                # Still record the timing even if function failed
                execution_time = time.time() - start_time
                metric = PerformanceMetric(
                    function_name=f"{func.__module__}.{func.__name__}",
                    execution_time=execution_time,
                    memory_usage=None,
                    call_count=1,
                    timestamp=datetime.now()
                )
                performance_monitor.record_metric(metric)
                raise
        
        return wrapper
    
    return decorator


def async_timed(include_memory: bool = False):
    """Async performance timing decorator."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Get memory usage if requested
            memory_before = None
            if include_memory:
                try:
                    import psutil
                    process = psutil.Process()
                    memory_before = process.memory_info().rss
                except ImportError:
                    pass
            
            # Execute function
            try:
                result = await func(*args, **kwargs)
                
                # Record performance metric
                execution_time = time.time() - start_time
                memory_usage = None
                
                if include_memory and memory_before:
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_after = process.memory_info().rss
                        memory_usage = memory_after - memory_before
                    except ImportError:
                        pass
                
                metric = PerformanceMetric(
                    function_name=f"{func.__module__}.{func.__name__}",
                    execution_time=execution_time,
                    memory_usage=memory_usage,
                    call_count=1,
                    timestamp=datetime.now()
                )
                
                performance_monitor.record_metric(metric)
                return result
                
            except Exception as e:
                # Still record the timing even if function failed
                execution_time = time.time() - start_time
                metric = PerformanceMetric(
                    function_name=f"{func.__module__}.{func.__name__}",
                    execution_time=execution_time,
                    memory_usage=None,
                    call_count=1,
                    timestamp=datetime.now()
                )
                performance_monitor.record_metric(metric)
                raise
        
        return wrapper
    
    return decorator


def batch_process(batch_size: int = 100, max_workers: Optional[int] = None):
    """Batch processing decorator for handling large datasets."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(items: List[Any], *args, **kwargs):
            if len(items) <= batch_size:
                return await func(items, *args, **kwargs)
            
            # Process in batches
            results = []
            semaphore = asyncio.Semaphore(max_workers or 10)
            
            async def process_batch(batch):
                async with semaphore:
                    return await func(batch, *args, **kwargs)
            
            # Create batches
            batches = [
                items[i:i + batch_size]
                for i in range(0, len(items), batch_size)
            ]
            
            # Process all batches concurrently
            batch_results = await asyncio.gather(*[
                process_batch(batch) for batch in batches
            ])
            
            # Combine results
            for batch_result in batch_results:
                if isinstance(batch_result, list):
                    results.extend(batch_result)
                else:
                    results.append(batch_result)
            
            return results
        
        return wrapper
    
    return decorator


def debounce(wait_seconds: float):
    """Debounce decorator to limit function calls."""
    
    def decorator(func: Callable) -> Callable:
        last_called = [0]
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if now - last_called[0] >= wait_seconds:
                last_called[0] = now
                return func(*args, **kwargs)
            return None
        
        return wrapper
    
    return decorator


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate cache key from function arguments."""
    try:
        # Create a hashable representation of arguments
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        
        # Serialize and hash
        serialized = pickle.dumps(key_data)
        return hashlib.md5(serialized).hexdigest()
        
    except (TypeError, AttributeError):
        # Fallback for non-serializable arguments
        return hashlib.md5(
            f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}".encode()
        ).hexdigest()


class FileCache:
    """File-based caching for persistent data."""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from file cache."""
        cache_file = self.cache_dir / f"{key}.cache"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            # Check TTL
            if 'ttl' in data and data['ttl'] < time.time():
                cache_file.unlink()
                return None
            
            return data['value']
            
        except (pickle.PickleError, FileNotFoundError, KeyError):
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in file cache."""
        cache_file = self.cache_dir / f"{key}.cache"
        
        data = {
            'value': value,
            'timestamp': time.time()
        }
        
        if ttl:
            data['ttl'] = time.time() + ttl
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except pickle.PickleError:
            pass  # Ignore serialization errors
    
    def clear(self) -> None:
        """Clear all file cache."""
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
            except OSError:
                pass


# File cache instance
file_cache = FileCache()


def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report."""
    return {
        "performance_metrics": performance_monitor.get_performance_report(),
        "cache_stats": cache_manager.get_stats(),
        "slow_functions": performance_monitor.get_slow_functions(0.5),
        "recommendations": _generate_performance_recommendations()
    }


def _generate_performance_recommendations() -> List[str]:
    """Generate performance improvement recommendations."""
    recommendations = []
    
    # Check cache hit rate
    cache_stats = cache_manager.get_stats()
    if cache_stats['hit_rate'] < 0.5:
        recommendations.append("🚀 Consider optimizing caching strategy - low hit rate detected")
    
    # Check for slow functions
    slow_functions = performance_monitor.get_slow_functions(1.0)
    if slow_functions:
        recommendations.append(f"⚡ Optimize {len(slow_functions)} slow functions (>1s execution time)")
    
    # Check function call patterns
    report = performance_monitor.get_performance_report()
    if report and 'most_called_functions' in report:
        most_called = report['most_called_functions']
        if most_called and most_called[0]['calls'] > 1000:
            recommendations.append("🔄 Consider caching for frequently called functions")
    
    if not recommendations:
        recommendations.append("✨ Performance looks good!")
    
    return recommendations