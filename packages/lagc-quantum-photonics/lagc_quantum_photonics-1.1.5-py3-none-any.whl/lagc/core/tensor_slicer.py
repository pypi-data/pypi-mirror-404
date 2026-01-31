"""
Tensor Slicer: CPU-Optimized Slicing Engine (Algorithm 2)
==========================================================

Implements recursive tensor network slicing for memory-efficient contraction.
Stays within RAM limits by dynamically partitioning computation.

Key Features:
- Memory estimation before contraction
- Automatic bond selection for slicing
- Recursive divide-and-conquer with parallel execution
- L3 cache and RAM optimization (no disk swap)

Algorithm:
1. Estimate memory requirement for contraction
2. If exceeds RAM limit:
   - Select highest-centrality bond for cutting
   - Branch into two independent tensor networks (index fixed to 0 and 1)
   - Dispatch branches to parallel CPU cores
3. Sum weighted results from all branches
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import logging
import psutil

try:
    import opt_einsum
    HAS_OPT_EINSUM = True
except ImportError:
    HAS_OPT_EINSUM = False

logger = logging.getLogger(__name__)


@dataclass
class TensorNetwork:
    """
    Represents a tensor network for contraction.
    
    Attributes:
        tensors: List of numpy arrays representing individual tensors
        edges: List of (tensor_i, tensor_j, bond_dim) tuples
        index_labels: List of string labels for each tensor's indices
        contraction_string: Einstein summation string for contraction
    """
    tensors: List[np.ndarray]
    edges: List[Tuple[int, int, int]]
    index_labels: List[List[str]]
    contraction_string: str = ""
    
    def __post_init__(self):
        if not self.contraction_string:
            self.contraction_string = self._build_contraction_string()
    
    def _build_contraction_string(self) -> str:
        """Build Einstein summation string from tensor structure."""
        if not self.index_labels:
            return ""
        return ",".join(["".join(labels) for labels in self.index_labels]) + "->"
    
    @property
    def n_tensors(self) -> int:
        return len(self.tensors)
    
    def copy(self) -> 'TensorNetwork':
        return TensorNetwork(
            tensors=[t.copy() for t in self.tensors],
            edges=self.edges.copy(),
            index_labels=[labels.copy() for labels in self.index_labels],
            contraction_string=self.contraction_string
        )


class TensorSlicer:
    """
    CPU-optimized tensor network slicer for memory-efficient contraction.
    
    Uses recursive slicing to stay within RAM limits while maximizing
    parallelization across CPU cores.
    
    Attributes:
        ram_limit_bytes: Maximum RAM to use for intermediate tensors
        n_workers: Number of parallel workers (CPU cores)
        dtype_size: Bytes per element (8 for float64, 4 for float32)
    """
    
    def __init__(
        self,
        ram_limit_gb: float = 8.0,
        n_workers: Optional[int] = None,
        dtype: np.dtype = np.complex128
    ):
        """
        Initialize the tensor slicer.
        
        Args:
            ram_limit_gb: RAM limit in gigabytes
            n_workers: Number of parallel workers (default: all CPU cores)
            dtype: Data type for tensors
        """
        self.ram_limit_bytes = int(ram_limit_gb * (1024 ** 3))
        self.n_workers = n_workers or multiprocessing.cpu_count()
        self.dtype = dtype
        self.dtype_size = np.dtype(dtype).itemsize
        
        # Track slicing statistics
        self._slice_count = 0
        self._total_contractions = 0
        
        logger.info(
            f"TensorSlicer initialized: RAM limit={ram_limit_gb:.1f}GB, "
            f"workers={self.n_workers}, dtype={dtype}"
        )
    
    def estimate_memory(
        self,
        tensors: List[np.ndarray],
        path: Optional[List[Tuple[int, int]]] = None
    ) -> int:
        """
        Estimate peak memory usage for tensor contraction.
        
        Calculates the maximum intermediate tensor size along the contraction path.
        Formula: S = Π d_i × dtype_size
        
        Args:
            tensors: List of tensors to contract
            path: Contraction path (pairs of tensor indices)
            
        Returns:
            Estimated peak memory in bytes
        """
        if not tensors:
            return 0
        
        # Simple estimation: sum of all tensor sizes plus largest possible intermediate
        total_size = sum(t.nbytes for t in tensors)
        
        # Estimate largest intermediate: product of unique dimensions
        all_shapes = [t.shape for t in tensors]
        max_dim_product = 1
        
        for shape in all_shapes:
            dim_product = np.prod(shape) if shape else 1
            max_dim_product = max(max_dim_product, dim_product)
        
        # Intermediate can be at most n^2 larger in worst case
        estimated_intermediate = max_dim_product * self.dtype_size * len(tensors)
        
        return total_size + estimated_intermediate
    
    def identify_heavy_bond(
        self,
        tensor_network: TensorNetwork
    ) -> Tuple[int, int, str]:
        """
        Identify the bond (edge) with highest centrality for slicing.
        
        Selects the bond that, when cut, most evenly divides the network
        and has the largest dimension (most memory savings).
        
        Args:
            tensor_network: The tensor network to analyze
            
        Returns:
            Tuple of (tensor_index, bond_index_in_tensor, bond_label)
        """
        if not tensor_network.edges:
            # No edges, find largest dimension across tensors
            max_dim = 0
            best_tensor = 0
            best_bond = 0
            
            for t_idx, tensor in enumerate(tensor_network.tensors):
                for b_idx, dim in enumerate(tensor.shape):
                    if dim > max_dim:
                        max_dim = dim
                        best_tensor = t_idx
                        best_bond = b_idx
            
            label = tensor_network.index_labels[best_tensor][best_bond] if tensor_network.index_labels else f"i{best_bond}"
            return (best_tensor, best_bond, label)
        
        # Find edge with largest bond dimension
        max_bond_dim = 0
        best_edge = tensor_network.edges[0]
        
        for edge in tensor_network.edges:
            t1, t2, bond_dim = edge
            if bond_dim > max_bond_dim:
                max_bond_dim = bond_dim
                best_edge = edge
        
        t1, t2, _ = best_edge
        
        # Find the shared index label
        if tensor_network.index_labels:
            labels1 = set(tensor_network.index_labels[t1])
            labels2 = set(tensor_network.index_labels[t2])
            shared = labels1 & labels2
            label = shared.pop() if shared else f"bond_{t1}_{t2}"
        else:
            label = f"bond_{t1}_{t2}"
        
        return (t1, 0, label)
    
    def project(
        self,
        tensor_network: TensorNetwork,
        tensor_idx: int,
        bond_idx: int,
        value: int
    ) -> TensorNetwork:
        """
        Project (fix) a bond index to a specific value (0 or 1).
        
        Creates a new tensor network where the specified index is fixed,
        effectively slicing the tensor along that dimension.
        
        Args:
            tensor_network: Original tensor network
            tensor_idx: Index of tensor containing the bond
            bond_idx: Index of the bond dimension within the tensor
            value: Value to fix the index to (0 or 1)
            
        Returns:
            New TensorNetwork with the index fixed
        """
        new_tensors = []
        new_labels = []
        
        for t_idx, tensor in enumerate(tensor_network.tensors):
            if t_idx == tensor_idx:
                # Slice this tensor
                slices = [slice(None)] * tensor.ndim
                slices[bond_idx] = value
                new_tensor = tensor[tuple(slices)]
                new_tensors.append(new_tensor)
                
                # Update labels
                if tensor_network.index_labels:
                    labels = tensor_network.index_labels[t_idx].copy()
                    labels.pop(bond_idx)
                    new_labels.append(labels)
            else:
                new_tensors.append(tensor.copy())
                if tensor_network.index_labels:
                    new_labels.append(tensor_network.index_labels[t_idx].copy())
        
        # Update edges (remove edges involving the sliced bond)
        new_edges = []
        for edge in tensor_network.edges:
            t1, t2, bond_dim = edge
            if t1 != tensor_idx and t2 != tensor_idx:
                new_edges.append(edge)
        
        return TensorNetwork(
            tensors=new_tensors,
            edges=new_edges,
            index_labels=new_labels if new_labels else []
        )
    
    def contract_directly(
        self,
        tensors: List[np.ndarray],
        contraction_string: str = "",
        path: str = "auto"
    ) -> np.ndarray:
        """
        Contract tensors directly using opt_einsum.
        
        Args:
            tensors: List of tensors to contract
            contraction_string: Einstein summation notation
            path: Contraction path strategy
            
        Returns:
            Contracted result tensor
        """
        self._total_contractions += 1
        
        if not tensors:
            return np.array(1.0, dtype=self.dtype)
        
        if len(tensors) == 1:
            return tensors[0].copy()
        
        if HAS_OPT_EINSUM and contraction_string:
            try:
                return opt_einsum.contract(contraction_string, *tensors, optimize=path)
            except Exception as e:
                logger.warning(f"opt_einsum failed: {e}, falling back to numpy")
        
        # Fallback: sequential pairwise contraction
        result = tensors[0]
        for tensor in tensors[1:]:
            result = np.tensordot(result, tensor, axes=0)
        
        return result
    
    def recursive_slice_contract(
        self,
        tensor_network: TensorNetwork,
        path: str = "auto",
        depth: int = 0
    ) -> np.ndarray:
        """
        Recursively slice and contract tensor network within memory limits.
        
        Algorithm:
        1. Check if current tensors fit in RAM
        2. If yes, contract directly
        3. If no:
           a. Find heaviest bond to cut
           b. Create two branches (index=0 and index=1)
           c. Recursively contract each branch
           d. Sum results
        
        Args:
            tensor_network: Tensor network to contract
            path: Contraction path strategy
            depth: Current recursion depth
            
        Returns:
            Contracted result
        """
        current_mem = self.estimate_memory(tensor_network.tensors)
        
        logger.debug(f"Depth {depth}: memory estimate = {current_mem / 1e9:.2f} GB")
        
        if current_mem < self.ram_limit_bytes:
            # Can contract directly
            return self.contract_directly(
                tensor_network.tensors,
                tensor_network.contraction_string,
                path
            )
        
        # Need to slice
        self._slice_count += 1
        
        # Find bond to cut
        tensor_idx, bond_idx, label = self.identify_heavy_bond(tensor_network)
        
        logger.debug(f"Slicing bond '{label}' at tensor {tensor_idx}, index {bond_idx}")
        
        # Get dimension of the bond
        bond_dim = tensor_network.tensors[tensor_idx].shape[bond_idx]
        
        # Create branches for each value of the sliced index
        results = []
        for value in range(bond_dim):
            projected = self.project(tensor_network, tensor_idx, bond_idx, value)
            result = self.recursive_slice_contract(projected, path, depth + 1)
            results.append(result)
        
        # Sum all branches
        return sum(results)
    
    def parallel_slice_contract(
        self,
        tensor_network: TensorNetwork,
        path: str = "auto"
    ) -> np.ndarray:
        """
        Parallel version of recursive slice contraction.
        
        Uses ProcessPoolExecutor to dispatch branches to multiple CPU cores.
        
        Args:
            tensor_network: Tensor network to contract
            path: Contraction path strategy
            
        Returns:
            Contracted result
        """
        current_mem = self.estimate_memory(tensor_network.tensors)
        
        if current_mem < self.ram_limit_bytes:
            return self.contract_directly(
                tensor_network.tensors,
                tensor_network.contraction_string,
                path
            )
        
        # Slice at top level for parallelization
        tensor_idx, bond_idx, label = self.identify_heavy_bond(tensor_network)
        bond_dim = tensor_network.tensors[tensor_idx].shape[bond_idx]
        
        logger.info(f"Parallel slicing: bond '{label}' with dim={bond_dim}")
        
        # Create all branches
        branches = []
        for value in range(bond_dim):
            projected = self.project(tensor_network, tensor_idx, bond_idx, value)
            branches.append(projected)
        
        # Dispatch to parallel workers
        results = []
        
        with ProcessPoolExecutor(max_workers=min(self.n_workers, bond_dim)) as executor:
            futures = {
                executor.submit(
                    self._contract_branch,
                    branch,
                    path
                ): i for i, branch in enumerate(branches)
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Branch contraction failed: {e}")
                    raise
        
        return sum(results)
    
    def _contract_branch(
        self,
        tensor_network: TensorNetwork,
        path: str
    ) -> np.ndarray:
        """Contract a single branch (for parallel execution)."""
        return self.recursive_slice_contract(tensor_network, path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get slicing statistics."""
        return {
            'slice_count': self._slice_count,
            'total_contractions': self._total_contractions,
            'ram_limit_gb': self.ram_limit_bytes / (1024 ** 3),
            'n_workers': self.n_workers
        }
    
    def reset_statistics(self) -> None:
        """Reset slicing statistics."""
        self._slice_count = 0
        self._total_contractions = 0
    
    def get_available_memory(self) -> int:
        """Get currently available system memory in bytes."""
        return psutil.virtual_memory().available
    
    def adjust_ram_limit_dynamic(self, safety_factor: float = 0.8) -> None:
        """
        Dynamically adjust RAM limit based on available memory.
        
        Args:
            safety_factor: Fraction of available memory to use (0-1)
        """
        available = self.get_available_memory()
        self.ram_limit_bytes = int(available * safety_factor)
        logger.info(f"Adjusted RAM limit to {self.ram_limit_bytes / 1e9:.2f} GB")
