"""
Topologies: Standard Lattice Generators
========================================

Generates various graph state topologies for quantum photonic simulations:
- 3D RHG (Raussendorf-Harrington-Goyal) lattice for fault-tolerant MBQC
- 2D Cluster state for measurement-based quantum computation
- Linear cluster for one-way quantum computing
- GHZ state for entanglement distribution

Reference:
    Raussendorf, R., Harrington, J., & Goyal, K. (2007).
    Topological fault-tolerance in cluster state quantum computation.
    New Journal of Physics, 9(6), 199.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Optional, List, Dict, Any, Generator
from lagc.core.graph_engine import StabilizerGraph
import logging

logger = logging.getLogger(__name__)


class TopologyGenerator:
    """
    Generator for standard quantum graph state topologies.
    
    Creates various lattice structures commonly used in photonic
    quantum computing, particularly for measurement-based quantum
    computation (MBQC) and fault-tolerant schemes.
    
    Example:
        >>> gen = TopologyGenerator()
        >>> graph = gen.create_3d_rhg_lattice(10, 10, 10)
        >>> print(f"Created lattice with {graph.n_qubits} qubits")
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize topology generator.
        
        Args:
            seed: Random seed for any stochastic operations
        """
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
        
        logger.debug(f"TopologyGenerator initialized with seed={seed}")
    
    def create_3d_rhg_lattice(
        self,
        lx: int,
        ly: int,
        lz: int,
        periodic: bool = False
    ) -> StabilizerGraph:
        """
        Create a 3D RHG (Raussendorf-Harrington-Goyal) lattice.
        
        The RHG lattice is the fundamental structure for topological
        fault-tolerant quantum computation. Each unit cell contains
        multiple qubits connected in a specific pattern.
        
        Structure:
        - Primal lattice: cubic with qubits on edges
        - Dual lattice: face centers for syndrome measurement
        - Total qubits ≈ 3 * lx * ly * lz for edge qubits
        
        Args:
            lx: Lattice size in x direction
            ly: Lattice size in y direction
            lz: Lattice size in z direction
            periodic: Whether to use periodic boundary conditions
            
        Returns:
            StabilizerGraph representing the RHG lattice
        """
        # RHG lattice has qubits on edges of cubic lattice
        # Each vertex has 6 edges (in 3D), shared with neighbors
        # Total edges = 3 * lx * ly * lz for non-periodic
        
        # Calculate number of qubits
        if periodic:
            n_x_edges = lx * ly * lz
            n_y_edges = lx * ly * lz
            n_z_edges = lx * ly * lz
        else:
            n_x_edges = (lx - 1) * ly * lz
            n_y_edges = lx * (ly - 1) * lz
            n_z_edges = lx * ly * (lz - 1)
        
        n_edge_qubits = n_x_edges + n_y_edges + n_z_edges
        
        # Add face qubits for syndrome measurement (one per face)
        if periodic:
            n_faces = 3 * lx * ly * lz
        else:
            n_faces = (
                (lx - 1) * (ly - 1) * lz +  # xy faces
                (lx - 1) * ly * (lz - 1) +  # xz faces
                lx * (ly - 1) * (lz - 1)    # yz faces
            )
        
        n_qubits = n_edge_qubits + n_faces
        
        logger.info(f"Creating 3D RHG lattice: {lx}x{ly}x{lz}, {n_qubits} qubits")
        
        graph = StabilizerGraph(n_qubits)
        
        # Helper to get edge index
        def edge_index(x: int, y: int, z: int, direction: str) -> Optional[int]:
            """Get qubit index for edge at (x,y,z) in given direction."""
            if direction == 'x':
                if not periodic and x >= lx - 1:
                    return None
                idx = (x % lx) + (y * lx) + (z * lx * ly)
                return idx
            elif direction == 'y':
                if not periodic and y >= ly - 1:
                    return None
                idx = n_x_edges + (x + (y % ly) * lx + z * lx * ly)
                return idx
            elif direction == 'z':
                if not periodic and z >= lz - 1:
                    return None
                idx = n_x_edges + n_y_edges + (x + y * lx + (z % lz) * lx * ly)
                return idx
            return None
        
        # Connect edges that share a vertex
        for x in range(lx):
            for y in range(ly):
                for z in range(lz):
                    # Get all edges meeting at vertex (x, y, z)
                    edges_at_vertex = []
                    
                    # Outgoing edges
                    for d in ['x', 'y', 'z']:
                        idx = edge_index(x, y, z, d)
                        if idx is not None:
                            edges_at_vertex.append(idx)
                    
                    # Incoming edges
                    if x > 0 or periodic:
                        idx = edge_index((x - 1) % lx, y, z, 'x')
                        if idx is not None:
                            edges_at_vertex.append(idx)
                    if y > 0 or periodic:
                        idx = edge_index(x, (y - 1) % ly, z, 'y')
                        if idx is not None:
                            edges_at_vertex.append(idx)
                    if z > 0 or periodic:
                        idx = edge_index(x, y, (z - 1) % lz, 'z')
                        if idx is not None:
                            edges_at_vertex.append(idx)
                    
                    # Connect all edges at this vertex (graph state rule)
                    for i in range(len(edges_at_vertex)):
                        for j in range(i + 1, len(edges_at_vertex)):
                            graph.add_edge(edges_at_vertex[i], edges_at_vertex[j])
        
        graph._finalize()
        
        logger.info(f"3D RHG lattice created: {graph.get_edge_count()} edges")
        
        return graph
    
    def create_2d_cluster_state(
        self,
        rows: int,
        cols: int,
        periodic: bool = False
    ) -> StabilizerGraph:
        """
        Create a 2D cluster state (square lattice).
        
        The 2D cluster state is the canonical resource for
        measurement-based quantum computation.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            periodic: Whether to use periodic boundary conditions
            
        Returns:
            StabilizerGraph representing the 2D cluster
        """
        n_qubits = rows * cols
        
        logger.info(f"Creating 2D cluster state: {rows}x{cols}, {n_qubits} qubits")
        
        graph = StabilizerGraph(n_qubits)
        
        def qubit_index(r: int, c: int) -> int:
            return r * cols + c
        
        # Connect nearest neighbors
        for r in range(rows):
            for c in range(cols):
                idx = qubit_index(r, c)
                
                # Right neighbor
                if c < cols - 1:
                    graph.add_edge(idx, qubit_index(r, c + 1))
                elif periodic:
                    graph.add_edge(idx, qubit_index(r, 0))
                
                # Down neighbor
                if r < rows - 1:
                    graph.add_edge(idx, qubit_index(r + 1, c))
                elif periodic:
                    graph.add_edge(idx, qubit_index(0, c))
        
        graph._finalize()
        
        logger.info(f"2D cluster state created: {graph.get_edge_count()} edges")
        
        return graph
    
    def create_linear_cluster(self, n: int) -> StabilizerGraph:
        """
        Create a linear cluster state (1D chain).
        
        Args:
            n: Number of qubits
            
        Returns:
            StabilizerGraph representing the linear cluster
        """
        logger.info(f"Creating linear cluster: {n} qubits")
        
        graph = StabilizerGraph(n)
        
        for i in range(n - 1):
            graph.add_edge(i, i + 1)
        
        graph._finalize()
        
        return graph
    
    def create_ghz_state(self, n: int) -> StabilizerGraph:
        """
        Create a GHZ state graph (star topology).
        
        The GHZ state |000...0⟩ + |111...1⟩ can be represented
        as a graph state with star topology.
        
        Args:
            n: Number of qubits
            
        Returns:
            StabilizerGraph representing the GHZ state
        """
        logger.info(f"Creating GHZ state: {n} qubits")
        
        # GHZ state is a star graph with qubit 0 as center
        graph = StabilizerGraph(n)
        
        for i in range(1, n):
            graph.add_edge(0, i)
        
        graph._finalize()
        
        return graph
    
    def create_ring_cluster(self, n: int) -> StabilizerGraph:
        """
        Create a ring cluster state (circular chain).
        
        Args:
            n: Number of qubits
            
        Returns:
            StabilizerGraph representing the ring cluster
        """
        logger.info(f"Creating ring cluster: {n} qubits")
        
        graph = StabilizerGraph(n)
        
        for i in range(n):
            graph.add_edge(i, (i + 1) % n)
        
        graph._finalize()
        
        return graph
    
    def create_complete_graph(self, n: int) -> StabilizerGraph:
        """
        Create a complete graph (all-to-all connected).
        
        Args:
            n: Number of qubits
            
        Returns:
            StabilizerGraph with all possible edges
        """
        logger.info(f"Creating complete graph: {n} qubits")
        
        graph = StabilizerGraph(n)
        
        for i in range(n):
            for j in range(i + 1, n):
                graph.add_edge(i, j)
        
        graph._finalize()
        
        return graph
    
    def create_tree_graph(
        self,
        branching_factor: int,
        depth: int
    ) -> StabilizerGraph:
        """
        Create a tree graph state.
        
        Args:
            branching_factor: Number of children per node
            depth: Depth of the tree
            
        Returns:
            StabilizerGraph representing the tree
        """
        # Calculate total nodes: 1 + b + b^2 + ... + b^depth
        n_qubits = sum(branching_factor ** d for d in range(depth + 1))
        
        logger.info(
            f"Creating tree graph: branching={branching_factor}, "
            f"depth={depth}, {n_qubits} qubits"
        )
        
        graph = StabilizerGraph(n_qubits)
        
        # Build tree level by level
        current_idx = 0
        for level in range(depth):
            n_nodes_this_level = branching_factor ** level
            for node in range(n_nodes_this_level):
                parent_idx = current_idx + node
                first_child = current_idx + n_nodes_this_level + node * branching_factor
                
                for child in range(branching_factor):
                    child_idx = first_child + child
                    if child_idx < n_qubits:
                        graph.add_edge(parent_idx, child_idx)
            
            current_idx += n_nodes_this_level
        
        graph._finalize()
        
        return graph
    
    def create_custom_lattice(
        self,
        nodes: List[int],
        edges: List[Tuple[int, int]]
    ) -> StabilizerGraph:
        """
        Create a custom graph from explicit node and edge lists.
        
        Args:
            nodes: List of node indices
            edges: List of (i, j) edge tuples
            
        Returns:
            StabilizerGraph with the specified structure
        """
        n_qubits = max(nodes) + 1 if nodes else 0
        
        logger.info(f"Creating custom lattice: {n_qubits} qubits, {len(edges)} edges")
        
        graph = StabilizerGraph(n_qubits)
        
        for i, j in edges:
            graph.add_edge(i, j)
        
        graph._finalize()
        
        return graph
    
    @staticmethod
    def get_lattice_info(topology: str, *dims) -> Dict[str, Any]:
        """
        Get information about a lattice without creating it.
        
        Args:
            topology: Topology type ('3d_rhg', '2d_cluster', etc.)
            *dims: Dimension arguments
            
        Returns:
            Dictionary with lattice information
        """
        info = {'topology': topology}
        
        if topology == '3d_rhg':
            lx, ly, lz = dims[:3] if len(dims) >= 3 else (dims[0], dims[0], dims[0])
            n_edges = 3 * lx * ly * lz
            n_faces = 3 * (lx - 1) * (ly - 1) * (lz - 1)
            info.update({
                'dimensions': (lx, ly, lz),
                'n_qubits_approx': n_edges + n_faces,
                'description': '3D RHG lattice for fault-tolerant MBQC'
            })
        elif topology == '2d_cluster':
            rows, cols = dims[:2] if len(dims) >= 2 else (dims[0], dims[0])
            info.update({
                'dimensions': (rows, cols),
                'n_qubits': rows * cols,
                'n_edges': rows * (cols - 1) + (rows - 1) * cols,
                'description': '2D square lattice cluster state'
            })
        elif topology == 'linear':
            n = dims[0] if dims else 10
            info.update({
                'n_qubits': n,
                'n_edges': n - 1,
                'description': 'Linear chain cluster state'
            })
        elif topology == 'ghz':
            n = dims[0] if dims else 10
            info.update({
                'n_qubits': n,
                'n_edges': n - 1,
                'description': 'GHZ state (star graph)'
            })
        
        return info
    
    @staticmethod
    def list_topologies() -> List[str]:
        """List available topology types."""
        return [
            '3d_rhg',
            '2d_cluster',
            'linear',
            'ghz',
            'ring',
            'complete',
            'tree',
            'custom'
        ]
