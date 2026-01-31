"""
Parallel Scheduler: CPU Multicore Processing
=============================================

Manages parallel execution of tensor network contractions
across multiple CPU cores using ProcessPoolExecutor.

Features:
- Dynamic CPU core detection
- Task dispatching and load balancing
- Result aggregation with weighted summation
- Memory-aware scheduling
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable, Union
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import multiprocessing
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """
    Result from a parallel task execution.
    
    Attributes:
        task_id: Unique identifier for the task
        result: The computed result
        execution_time: Time taken in seconds
        worker_id: ID of the worker that executed the task
        success: Whether execution was successful
        error: Error message if failed
    """
    task_id: int
    result: Any
    execution_time: float
    worker_id: int
    success: bool
    error: Optional[str] = None


@dataclass
class SchedulerStats:
    """Statistics from parallel execution."""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_time: float
    avg_task_time: float
    speedup: float
    efficiency: float


class ParallelScheduler:
    """
    CPU multicore parallel scheduler for tensor network contractions.
    
    Dispatches computation tasks to multiple CPU cores and aggregates
    results. Supports both process-based and thread-based parallelism.
    
    Example:
        >>> scheduler = ParallelScheduler(n_workers=4)
        >>> tasks = [lambda: heavy_computation(i) for i in range(10)]
        >>> results = scheduler.dispatch_tasks(tasks)
        >>> final = scheduler.aggregate_results(results)
    """
    
    def __init__(
        self,
        n_workers: Optional[int] = None,
        use_processes: bool = True,
        max_memory_per_worker_gb: float = 2.0
    ):
        """
        Initialize parallel scheduler.
        
        Args:
            n_workers: Number of parallel workers (default: all CPU cores)
            use_processes: Use processes (True) or threads (False)
            max_memory_per_worker_gb: Maximum memory per worker in GB
        """
        self.n_workers = n_workers or multiprocessing.cpu_count()
        self.use_processes = use_processes
        self.max_memory_per_worker = int(max_memory_per_worker_gb * 1024 ** 3)
        
        self._stats: Optional[SchedulerStats] = None
        
        logger.info(
            f"ParallelScheduler initialized: {self.n_workers} workers, "
            f"{'processes' if use_processes else 'threads'}"
        )
    
    def dispatch_tasks(
        self,
        tasks: List[Callable[[], Any]],
        timeout: Optional[float] = None
    ) -> List[TaskResult]:
        """
        Dispatch tasks to parallel workers.
        
        Args:
            tasks: List of callable tasks (no arguments)
            timeout: Optional timeout per task in seconds
            
        Returns:
            List of TaskResult objects
        """
        n_tasks = len(tasks)
        results = []
        start_time = time.time()
        
        if n_tasks == 0:
            return results
        
        logger.info(f"Dispatching {n_tasks} tasks to {self.n_workers} workers")
        
        ExecutorClass = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        
        with ExecutorClass(max_workers=min(self.n_workers, n_tasks)) as executor:
            # Submit all tasks
            future_to_id = {
                executor.submit(self._execute_task, task, i): i
                for i, task in enumerate(tasks)
            }
            
            # Collect results
            for future in as_completed(future_to_id, timeout=timeout):
                task_id = future_to_id[future]
                try:
                    result = future.result(timeout=timeout)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    results.append(TaskResult(
                        task_id=task_id,
                        result=None,
                        execution_time=0,
                        worker_id=-1,
                        success=False,
                        error=str(e)
                    ))
        
        total_time = time.time() - start_time
        self._update_stats(results, total_time)
        
        logger.info(f"Completed {len(results)} tasks in {total_time:.2f}s")
        
        return sorted(results, key=lambda r: r.task_id)
    
    def _execute_task(
        self,
        task: Callable[[], Any],
        task_id: int
    ) -> TaskResult:
        """Execute a single task and wrap result."""
        start = time.time()
        worker_id = multiprocessing.current_process().pid
        
        try:
            result = task()
            return TaskResult(
                task_id=task_id,
                result=result,
                execution_time=time.time() - start,
                worker_id=worker_id,
                success=True
            )
        except Exception as e:
            return TaskResult(
                task_id=task_id,
                result=None,
                execution_time=time.time() - start,
                worker_id=worker_id,
                success=False,
                error=str(e)
            )
    
    def dispatch_with_args(
        self,
        func: Callable,
        args_list: List[Tuple],
        timeout: Optional[float] = None
    ) -> List[TaskResult]:
        """
        Dispatch tasks with different arguments.
        
        Args:
            func: Function to call
            args_list: List of argument tuples
            timeout: Optional timeout per task
            
        Returns:
            List of TaskResult objects
        """
        tasks = [lambda args=args: func(*args) for args in args_list]
        return self.dispatch_tasks(tasks, timeout)
    
    def aggregate_results(
        self,
        results: List[TaskResult],
        weights: Optional[List[float]] = None,
        aggregation: str = 'sum'
    ) -> Any:
        """
        Aggregate results from parallel tasks.
        
        Args:
            results: List of TaskResult objects
            weights: Optional weights for weighted aggregation
            aggregation: 'sum', 'mean', 'product', or 'list'
            
        Returns:
            Aggregated result
        """
        # Filter successful results
        successful = [r for r in results if r.success]
        
        if not successful:
            logger.warning("No successful results to aggregate")
            return None
        
        values = [r.result for r in successful]
        
        if weights is not None:
            if len(weights) != len(results):
                raise ValueError("Weights must match number of results")
            # Filter weights for successful results
            weights = [w for r, w in zip(results, weights) if r.success]
        
        if aggregation == 'sum':
            if weights is not None:
                return sum(w * v for w, v in zip(weights, values))
            return sum(values)
        
        elif aggregation == 'mean':
            if weights is not None:
                total_weight = sum(weights)
                return sum(w * v for w, v in zip(weights, values)) / total_weight
            return sum(values) / len(values)
        
        elif aggregation == 'product':
            result = values[0]
            for v in values[1:]:
                result = result * v
            if weights is not None:
                # Apply weights as exponents (for numerical values)
                try:
                    result = np.prod([v ** w for v, w in zip(values, weights)])
                except:
                    pass
            return result
        
        elif aggregation == 'list':
            return values
        
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")
    
    def weighted_sum(
        self,
        results: List[TaskResult],
        weights: List[float]
    ) -> complex:
        """
        Compute weighted sum of complex results (for tensor slicing).
        
        Formula: Σ w_i × result_i
        
        Args:
            results: Task results (must be numeric)
            weights: Weights for each result
            
        Returns:
            Weighted sum as complex number
        """
        if len(results) != len(weights):
            raise ValueError("Results and weights must have same length")
        
        total = complex(0)
        for result, weight in zip(results, weights):
            if result.success:
                total += weight * complex(result.result)
        
        return total
    
    def map_reduce(
        self,
        map_func: Callable,
        reduce_func: Callable,
        items: List[Any]
    ) -> Any:
        """
        Parallel map-reduce operation.
        
        Args:
            map_func: Function to apply to each item
            reduce_func: Function to reduce results (takes 2 args)
            items: Items to process
            
        Returns:
            Final reduced result
        """
        # Map phase
        tasks = [lambda item=item: map_func(item) for item in items]
        results = self.dispatch_tasks(tasks)
        
        # Reduce phase
        values = [r.result for r in results if r.success]
        
        if not values:
            return None
        
        result = values[0]
        for value in values[1:]:
            result = reduce_func(result, value)
        
        return result
    
    def _update_stats(
        self,
        results: List[TaskResult],
        total_time: float
    ) -> None:
        """Update scheduler statistics."""
        n_total = len(results)
        n_completed = sum(1 for r in results if r.success)
        n_failed = n_total - n_completed
        
        if n_completed > 0:
            avg_time = sum(r.execution_time for r in results if r.success) / n_completed
            serial_time = sum(r.execution_time for r in results if r.success)
            speedup = serial_time / total_time if total_time > 0 else 1.0
            efficiency = speedup / self.n_workers
        else:
            avg_time = 0
            speedup = 1.0
            efficiency = 0
        
        self._stats = SchedulerStats(
            total_tasks=n_total,
            completed_tasks=n_completed,
            failed_tasks=n_failed,
            total_time=total_time,
            avg_task_time=avg_time,
            speedup=speedup,
            efficiency=efficiency
        )
    
    def get_stats(self) -> Optional[SchedulerStats]:
        """Get statistics from last execution."""
        return self._stats
    
    def get_available_cores(self) -> int:
        """Get number of available CPU cores."""
        return multiprocessing.cpu_count()
    
    def adjust_workers(self, n_workers: int) -> None:
        """
        Adjust number of workers.
        
        Args:
            n_workers: New number of workers
        """
        max_workers = multiprocessing.cpu_count()
        self.n_workers = min(max(1, n_workers), max_workers)
        logger.info(f"Adjusted to {self.n_workers} workers")
    
    def estimate_optimal_workers(
        self,
        task_memory_bytes: int,
        available_memory_bytes: Optional[int] = None
    ) -> int:
        """
        Estimate optimal number of workers based on memory.
        
        Args:
            task_memory_bytes: Memory required per task
            available_memory_bytes: Total available memory
            
        Returns:
            Recommended number of workers
        """
        if available_memory_bytes is None:
            try:
                import psutil
                available_memory_bytes = psutil.virtual_memory().available
            except ImportError:
                available_memory_bytes = 8 * 1024 ** 3  # Assume 8 GB
        
        memory_limited = available_memory_bytes // task_memory_bytes
        cpu_limited = multiprocessing.cpu_count()
        
        optimal = min(memory_limited, cpu_limited)
        return max(1, optimal)


# Standalone functions for use in process pools (must be picklable)
def _contract_slice(args: Tuple) -> complex:
    """Contract a sliced tensor network (for parallel execution)."""
    from lagc.core.tensor_slicer import TensorNetwork
    from lagc.simulation.contraction import TensorContractor
    
    tensor_data, contraction_string = args
    
    # Reconstruct tensors from serialized data
    tensors = [np.array(t) for t in tensor_data]
    
    contractor = TensorContractor()
    tn = TensorNetwork(
        tensors=tensors,
        edges=[],
        index_labels=[],
        contraction_string=contraction_string
    )
    
    result = contractor.contract(tn)
    return complex(result.amplitude) if np.isscalar(result.amplitude) else complex(0)


def parallel_contract_slices(
    sliced_networks: List[Tuple[List[np.ndarray], str]],
    n_workers: Optional[int] = None
) -> complex:
    """
    Contract multiple sliced tensor networks in parallel.
    
    Args:
        sliced_networks: List of (tensor_list, contraction_string) tuples
        n_workers: Number of parallel workers
        
    Returns:
        Sum of all slice contractions
    """
    scheduler = ParallelScheduler(n_workers=n_workers)
    
    # Serialize tensors for pickling
    serialized = [
        ([t.tolist() for t in tensors], string)
        for tensors, string in sliced_networks
    ]
    
    results = scheduler.dispatch_with_args(_contract_slice, [(s,) for s in serialized])
    
    return scheduler.weighted_sum(results, [1.0] * len(results))
