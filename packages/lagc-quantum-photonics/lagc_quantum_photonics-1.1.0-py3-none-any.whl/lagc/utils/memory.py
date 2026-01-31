"""
Memory Management Utilities
============================

RAM usage monitoring and dynamic memory limit management.
Optimized for CPU-only tensor network simulations.
"""

from __future__ import annotations

import gc
import sys
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import psutil for accurate memory monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("psutil not available, memory monitoring will be limited")


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_bytes: int
    available_bytes: int
    used_bytes: int
    percent_used: float
    
    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024 ** 3)
    
    @property
    def available_gb(self) -> float:
        return self.available_bytes / (1024 ** 3)
    
    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024 ** 3)
    
    def __repr__(self) -> str:
        return (
            f"MemoryStats(total={self.total_gb:.1f}GB, "
            f"available={self.available_gb:.1f}GB, "
            f"used={self.percent_used:.1f}%)"
        )


def get_available_memory() -> int:
    """
    Get available system memory in bytes.
    
    Returns:
        Available memory in bytes
    """
    if HAS_PSUTIL:
        return psutil.virtual_memory().available
    else:
        # Fallback: assume 4 GB available
        return 4 * 1024 ** 3


def get_memory_stats() -> MemoryStats:
    """
    Get detailed memory statistics.
    
    Returns:
        MemoryStats object with current memory info
    """
    if HAS_PSUTIL:
        mem = psutil.virtual_memory()
        return MemoryStats(
            total_bytes=mem.total,
            available_bytes=mem.available,
            used_bytes=mem.used,
            percent_used=mem.percent
        )
    else:
        # Fallback with estimates
        return MemoryStats(
            total_bytes=8 * 1024 ** 3,
            available_bytes=4 * 1024 ** 3,
            used_bytes=4 * 1024 ** 3,
            percent_used=50.0
        )


def check_memory_limit(required_bytes: int, safety_factor: float = 0.8) -> bool:
    """
    Check if required memory is available.
    
    Args:
        required_bytes: Memory needed in bytes
        safety_factor: Fraction of available memory to consider usable
        
    Returns:
        True if enough memory is available
    """
    available = get_available_memory()
    usable = int(available * safety_factor)
    return required_bytes <= usable


def estimate_tensor_memory(
    shape: Tuple[int, ...],
    dtype_size: int = 16  # complex128
) -> int:
    """
    Estimate memory required for a tensor.
    
    Args:
        shape: Tensor shape
        dtype_size: Bytes per element
        
    Returns:
        Memory in bytes
    """
    import numpy as np
    n_elements = np.prod(shape)
    return int(n_elements * dtype_size)


class MemoryManager:
    """
    Memory manager for tensor network simulations.
    
    Monitors and controls memory usage to prevent out-of-memory errors
    and optimize cache utilization.
    
    Example:
        >>> mm = MemoryManager(limit_gb=8.0)
        >>> with mm.track():
        >>>     result = heavy_computation()
        >>> print(mm.get_peak_usage())
    """
    
    def __init__(
        self,
        limit_gb: Optional[float] = None,
        safety_factor: float = 0.8
    ):
        """
        Initialize memory manager.
        
        Args:
            limit_gb: Memory limit in GB (default: auto-detect)
            safety_factor: Fraction of available memory to use
        """
        if limit_gb is not None:
            self.limit_bytes = int(limit_gb * 1024 ** 3)
        else:
            self.limit_bytes = int(get_available_memory() * safety_factor)
        
        self.safety_factor = safety_factor
        self._peak_usage = 0
        self._tracking = False
        self._allocations: Dict[int, int] = {}
        
        logger.debug(f"MemoryManager initialized with limit {self.limit_gb:.1f} GB")
    
    @property
    def limit_gb(self) -> float:
        """Memory limit in gigabytes."""
        return self.limit_bytes / (1024 ** 3)
    
    def check_allocation(self, size_bytes: int) -> bool:
        """
        Check if allocation would exceed limit.
        
        Args:
            size_bytes: Size of proposed allocation
            
        Returns:
            True if allocation is safe
        """
        stats = get_memory_stats()
        projected_usage = stats.used_bytes + size_bytes
        return projected_usage < self.limit_bytes
    
    def request_allocation(self, size_bytes: int, force: bool = False) -> bool:
        """
        Request an allocation, triggering GC if needed.
        
        Args:
            size_bytes: Size of proposed allocation
            force: If True, try GC before checking
            
        Returns:
            True if allocation was approved
        """
        if force:
            self.trigger_gc()
        
        if self.check_allocation(size_bytes):
            return True
        
        # Try garbage collection
        self.trigger_gc()
        
        return self.check_allocation(size_bytes)
    
    def trigger_gc(self) -> int:
        """
        Trigger garbage collection.
        
        Returns:
            Number of objects collected
        """
        collected = gc.collect()
        logger.debug(f"GC collected {collected} objects")
        return collected
    
    def get_current_usage(self) -> MemoryStats:
        """Get current memory usage."""
        return get_memory_stats()
    
    def get_peak_usage(self) -> int:
        """Get peak memory usage during tracking."""
        return self._peak_usage
    
    def update_peak(self) -> None:
        """Update peak usage tracking."""
        if self._tracking:
            current = get_memory_stats().used_bytes
            self._peak_usage = max(self._peak_usage, current)
    
    def estimate_available(self) -> int:
        """Estimate available memory for computation."""
        stats = get_memory_stats()
        available = min(
            stats.available_bytes,
            self.limit_bytes - stats.used_bytes
        )
        return max(0, int(available * self.safety_factor))
    
    def suggest_slice_count(
        self,
        total_memory_bytes: int,
        overhead_factor: float = 1.5
    ) -> int:
        """
        Suggest number of slices to fit computation in memory.
        
        Args:
            total_memory_bytes: Total memory for full computation
            overhead_factor: Additional overhead multiplier
            
        Returns:
            Recommended number of slices
        """
        available = self.estimate_available()
        memory_per_slice = available / overhead_factor
        
        if memory_per_slice <= 0:
            return 1
        
        n_slices = int(total_memory_bytes / memory_per_slice)
        return max(1, n_slices)
    
    def track(self) -> 'MemoryTracker':
        """
        Context manager for tracking memory usage.
        
        Returns:
            MemoryTracker context manager
        """
        return MemoryTracker(self)
    
    def report(self) -> str:
        """Generate memory usage report."""
        stats = get_memory_stats()
        return f"""
Memory Report
=============
Total RAM:     {stats.total_gb:.1f} GB
Used:          {stats.used_gb:.1f} GB ({stats.percent_used:.1f}%)
Available:     {stats.available_gb:.1f} GB
Limit:         {self.limit_gb:.1f} GB
Peak (session):{self._peak_usage / 1e9:.1f} GB
"""


class MemoryTracker:
    """Context manager for memory tracking."""
    
    def __init__(self, manager: MemoryManager):
        self.manager = manager
        self._start_memory = 0
    
    def __enter__(self) -> 'MemoryTracker':
        self.manager._tracking = True
        self.manager._peak_usage = 0
        self._start_memory = get_memory_stats().used_bytes
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.manager._tracking = False
        self.manager.update_peak()
    
    @property
    def delta_bytes(self) -> int:
        """Memory change since tracking started."""
        current = get_memory_stats().used_bytes
        return current - self._start_memory
    
    @property
    def delta_gb(self) -> float:
        """Memory change in GB."""
        return self.delta_bytes / (1024 ** 3)


def format_bytes(n_bytes: int) -> str:
    """Format byte count as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(n_bytes) < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} PB"
