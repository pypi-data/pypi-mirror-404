"""
Syndrome Analyzer: Loss Recovery Analysis for RHG Lattice
==========================================================

Analyzes the topological connectivity and computes logical error rates
after photon loss and recovery operations.

Key Features:
- Percolation checking for topological connectivity
- Logical error rate estimation via Monte Carlo
- Syndrome pattern visualization data
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from scipy.ndimage import label as connected_components
import logging

if TYPE_CHECKING:
    from lagc.core.rhg_lattice import RHGLattice
    from lagc.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)


class SyndromeAnalyzer:
    """
    Analyzer for loss recovery outcomes in RHG lattice.
    
    Determines whether the lattice maintains topological connectivity
    after photon losses, enabling fault-tolerant quantum computation.
    
    Example:
        >>> analyzer = SyndromeAnalyzer(lattice)
        >>> result = analyzer.analyze(engine, lost_nodes)
        >>> print(f"Percolates: {result['percolates']}")
    """
    
    def __init__(self, lattice: 'RHGLattice'):
        """
        Initialize syndrome analyzer.
        
        Args:
            lattice: RHGLattice instance to analyze
        """
        self.lattice = lattice
    
    def analyze(
        self,
        engine: 'GraphEngine',
        lost_nodes: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Perform full analysis of lattice state after loss.
        
        Args:
            engine: GraphEngine with current graph state
            lost_nodes: Array of lost qubit indices (optional)
            
        Returns:
            Dictionary with analysis results:
            - percolates: bool, whether topological path exists
            - syndrome_count: int, number of syndrome defects
            - active_qubits: int, remaining active qubits
            - connectivity_ratio: float, fraction of lattice connected
        """
        if lost_nodes is None:
            lost_nodes = np.array([], dtype=np.int64)
        
        # Compute syndrome
        syndrome = self.lattice.compute_syndrome(lost_nodes)
        
        # Check percolation
        percolates = self.check_percolation(engine, lost_nodes)
        
        # Calculate connectivity
        active_count = self.lattice.n_qubits - len(lost_nodes)
        connectivity_ratio = self._compute_connectivity_ratio(engine, lost_nodes)
        
        result = {
            'percolates': percolates,
            'syndrome_count': len(syndrome),
            'syndrome_positions': syndrome,
            'active_qubits': active_count,
            'lost_qubits': len(lost_nodes),
            'connectivity_ratio': connectivity_ratio,
            'is_correctable': percolates and len(syndrome) % 2 == 0,
        }
        
        logger.info(
            f"Syndrome analysis: {len(syndrome)} defects, "
            f"percolates={percolates}, correctable={result['is_correctable']}"
        )
        
        return result
    
    def check_percolation(
        self,
        engine: 'GraphEngine',
        lost_nodes: Optional[np.ndarray] = None
    ) -> bool:
        """
        Check if the lattice percolates (has a spanning path).
        
        For fault-tolerant operation, there must exist a connected path
        from one boundary to the opposite boundary in each direction.
        
        Args:
            engine: GraphEngine with current graph state
            lost_nodes: Array of lost qubit indices
            
        Returns:
            True if spanning path exists in at least one direction
        """
        if lost_nodes is None:
            lost_nodes = np.array([], dtype=np.int64)
        
        lost_set = set(lost_nodes.tolist())
        
        # Build active adjacency for connected component analysis
        active_nodes = [i for i in range(self.lattice.n_qubits) if i not in lost_set]
        
        if len(active_nodes) == 0:
            return False
        
        # Check connectivity using BFS from boundary nodes
        # Simplified: check if there's a path across z-direction
        
        # Find nodes on z=0 face
        start_nodes = []
        for idx in active_nodes:
            coord = self.lattice.index_to_coord(idx)
            if coord and coord[2] == 0:  # z = 0
                start_nodes.append(idx)
        
        if not start_nodes:
            return False
        
        # Find nodes on z=max face
        max_z = self.lattice.lz - 2 if self.lattice.boundary == 'open' else self.lattice.lz - 1
        end_nodes = set()
        for idx in active_nodes:
            coord = self.lattice.index_to_coord(idx)
            if coord and coord[2] >= max_z:
                end_nodes.add(idx)
        
        if not end_nodes:
            return False
        
        # BFS to check connectivity
        visited = set()
        queue = list(start_nodes)
        
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            
            if node in end_nodes:
                return True
            
            # Get neighbors from adjacency matrix
            neighbors = np.where(engine.adj[node] == 1)[0]
            for neighbor in neighbors:
                if neighbor not in visited and neighbor not in lost_set:
                    queue.append(neighbor)
        
        return False
    
    def _compute_connectivity_ratio(
        self,
        engine: 'GraphEngine',
        lost_nodes: np.ndarray
    ) -> float:
        """Compute the fraction of nodes in the largest connected component."""
        lost_set = set(lost_nodes.tolist())
        active_nodes = [i for i in range(self.lattice.n_qubits) if i not in lost_set]
        
        if len(active_nodes) == 0:
            return 0.0
        
        # Find largest connected component via BFS
        visited = set()
        largest_component = 0
        
        for start in active_nodes:
            if start in visited:
                continue
            
            # BFS from this node
            component_size = 0
            queue = [start]
            
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                component_size += 1
                
                neighbors = np.where(engine.adj[node] == 1)[0]
                for neighbor in neighbors:
                    if neighbor not in visited and neighbor not in lost_set:
                        queue.append(neighbor)
            
            largest_component = max(largest_component, component_size)
        
        return largest_component / len(active_nodes)
    
    def compute_logical_error_rate(
        self,
        engine_factory,
        p_loss: float,
        n_trials: int = 1000,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Estimate logical error rate via Monte Carlo simulation.
        
        Args:
            engine_factory: Callable that returns (engine, lattice) tuple
            p_loss: Photon loss probability
            n_trials: Number of Monte Carlo trials
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary with:
            - logical_error_rate: float, fraction of failed trials
            - percolation_rate: float, fraction that percolated
            - avg_syndrome_count: float, average syndrome defects
        """
        if seed is not None:
            np.random.seed(seed)
        
        success_count = 0
        percolation_count = 0
        total_syndrome = 0
        
        for trial in range(n_trials):
            # Create fresh lattice and engine
            engine, lattice = engine_factory()
            
            # Apply random loss
            survival = np.random.binomial(1, 1 - p_loss, lattice.n_qubits)
            lost_nodes = np.where(survival == 0)[0]
            
            # Analyze
            self.lattice = lattice
            result = self.analyze(engine, lost_nodes)
            
            if result['percolates']:
                percolation_count += 1
            if result['is_correctable']:
                success_count += 1
            total_syndrome += result['syndrome_count']
        
        logical_error_rate = 1 - (success_count / n_trials)
        percolation_rate = percolation_count / n_trials
        avg_syndrome = total_syndrome / n_trials
        
        logger.info(
            f"Monte Carlo ({n_trials} trials, p_loss={p_loss}): "
            f"logical_error_rate={logical_error_rate:.4f}, "
            f"percolation_rate={percolation_rate:.4f}"
        )
        
        return {
            'logical_error_rate': logical_error_rate,
            'percolation_rate': percolation_rate,
            'avg_syndrome_count': avg_syndrome,
            'n_trials': n_trials,
            'p_loss': p_loss,
        }
    
    def get_syndrome_visualization_data(
        self,
        engine: 'GraphEngine',
        lost_nodes: np.ndarray
    ) -> Dict:
        """
        Get data for 3D visualization of syndrome pattern.
        
        Returns:
            Dictionary with positions and types for visualization:
            - active_positions: array of active qubit positions
            - lost_positions: array of lost qubit positions
            - syndrome_positions: array of syndrome defect positions
        """
        lost_set = set(lost_nodes.tolist())
        
        active_positions = []
        lost_positions = []
        
        for idx in range(self.lattice.n_qubits):
            pos = self.lattice.get_physical_position(idx)
            if pos:
                if idx in lost_set:
                    lost_positions.append(pos)
                else:
                    active_positions.append(pos)
        
        syndrome = self.lattice.compute_syndrome(lost_nodes)
        
        return {
            'active_positions': np.array(active_positions),
            'lost_positions': np.array(lost_positions),
            'syndrome_positions': syndrome,
        }
