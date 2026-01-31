"""
Topologies: Standard Lattice Generators
========================================
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Optional, List, Dict, Any, Generator
from lagc.core.graph_engine import StabilizerGraph, GraphEngine
from lagc.core.rhg_lattice import RHGLattice
import logging

logger = logging.getLogger(__name__)


class TopologyGenerator:
    """Generator for standard quantum graph state topologies."""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
    
    def create_3d_rhg_lattice(
        self, 
        lx: int, 
        ly: int, 
        lz: int, 
        boundary: str = 'open'
    ) -> Tuple[GraphEngine, RHGLattice]:
        """
        Create a physically accurate 3D RHG lattice.
        
        Args:
            lx, ly, lz: Lattice dimensions (unit cells)
            boundary: 'open' or 'periodic'
            
        Returns:
            Tuple of (GraphEngine, RHGLattice) for graph + metadata
        """
        # Create lattice structure
        lattice = RHGLattice(lx, ly, lz, boundary)
        
        # Create engine and generate edges
        engine = GraphEngine(lattice.n_qubits)
        lattice.generate_edges(engine)
        
        logger.info(f"Created 3D RHG lattice: {lx}×{ly}×{lz}, {lattice.n_qubits} qubits")
        return engine, lattice

    def create_2d_cluster_state(self, rows: int, cols: int, periodic: bool = False) -> GraphEngine:
        """Create a 2D cluster state."""
        n_qubits = rows * cols
        graph = GraphEngine(n_qubits)
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if c < cols - 1: graph.add_edge(idx, idx + 1)
                if r < rows - 1: graph.add_edge(idx, idx + cols)
        return graph
    
    def create_linear_cluster(self, n: int) -> GraphEngine:
        """Create a linear cluster state."""
        graph = GraphEngine(n)
        for i in range(n - 1):
            graph.add_edge(i, i + 1)
        return graph
    
    def create_ghz_state(self, n: int) -> GraphEngine:
        """Create a GHZ state (star topology)."""
        graph = GraphEngine(n)
        for i in range(1, n):
            graph.add_edge(0, i)
        return graph

    def create_ring_cluster(self, n: int) -> GraphEngine:
        """Create a ring cluster state."""
        graph = GraphEngine(n)
        for i in range(n):
            graph.add_edge(i, (i + 1) % n)
        return graph

    def create_complete_graph(self, n: int) -> GraphEngine:
        """Create a complete graph."""
        graph = GraphEngine(n)
        for i in range(n):
            for j in range(i + 1, n):
                graph.add_edge(i, j)
        return graph

    @staticmethod
    def list_topologies() -> List[str]:
        return ['3d_rhg', '2d_cluster', 'linear', 'ghz', 'ring', 'complete']
