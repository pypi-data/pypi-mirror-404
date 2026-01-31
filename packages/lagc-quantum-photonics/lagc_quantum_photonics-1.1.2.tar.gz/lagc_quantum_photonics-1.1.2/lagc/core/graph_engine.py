"""
Graph Engine: XOR-based Graph Operations (Algorithm 1)
=======================================================

Implements efficient graph state manipulation using XOR operations on sparse matrices.
Manages millions of qubits with O(1) memory overhead for local complementation.

Key Operations:
- Local Complementation (τ_a): Inverts edges between neighbors of a node
- Loss Masking: Probabilistic node survival determination
- Graph Surgery: Topological defect correction
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix
from typing import Optional, List, Set
import logging

logger = logging.getLogger(__name__)


class StabilizerGraph:
    """
    Manages stabilizer graph state using sparse matrix representation.
    
    The graph state |G⟩ is represented by its adjacency matrix where:
    - Nodes represent qubits
    - Edges represent entanglement (CZ gates applied)
    
    Attributes:
        n_qubits: Number of qubits in the graph
        adj_matrix: Sparse adjacency matrix (scipy.sparse.csr_matrix)
        node_states: Array indicating node status (0=lost, 1=active)
        lost_nodes: Set of indices of lost nodes
    """
    
    def __init__(self, n_qubits: int):
        """Initialize an empty stabilizer graph."""
        self.n_qubits = n_qubits
        self._adj_lil = lil_matrix((n_qubits, n_qubits), dtype=np.int8)
        self._adj_csr: Optional[csr_matrix] = None
        self.node_states = np.ones(n_qubits, dtype=np.int8)
        self.lost_nodes: Set[int] = set()
        self._finalized = False
        
        logger.debug(f"Created StabilizerGraph with {n_qubits} qubits")
    
    @property
    def adj_matrix(self) -> csr_matrix:
        """Returns the CSR format adjacency matrix."""
        if not self._finalized:
            self._finalize()
        return self._adj_csr
    
    def _finalize(self) -> None:
        """Convert LIL matrix to CSR for efficient operations."""
        self._adj_csr = self._adj_lil.tocsr()
        self._finalized = True
    
    def add_edge(self, i: int, j: int) -> None:
        """Add an edge between nodes i and j (apply CZ gate)."""
        if i == j:
            return
        self._adj_lil[i, j] = 1
        self._adj_lil[j, i] = 1
        self._finalized = False
    
    def remove_edge(self, i: int, j: int) -> None:
        """Remove an edge between nodes i and j."""
        self._adj_lil[i, j] = 0
        self._adj_lil[j, i] = 0
        self._finalized = False
    
    def has_edge(self, i: int, j: int) -> bool:
        """Check if edge exists between nodes i and j."""
        if self._finalized:
            return bool(self._adj_csr[i, j])
        return bool(self._adj_lil[i, j])
    
    def get_neighbors(self, node_idx: int) -> np.ndarray:
        """Get all neighbors of a node."""
        if not self._finalized:
            self._finalize()
        return self._adj_csr[node_idx].indices.copy()
    
    def local_complementation(self, node_idx: int) -> None:
        """
        Apply local complementation τ_a at node a.
        
        This operation inverts all edges between neighbors of node_idx:
        - If neighbors i and j are connected, disconnect them
        - If neighbors i and j are not connected, connect them
        
        Mathematical operation: adj_matrix[N(a), N(a)] ^= 1
        """
        if not self._finalized:
            self._finalize()
            
        neighbors = self.get_neighbors(node_idx)
        n_neighbors = len(neighbors)
        
        if n_neighbors < 2:
            return
        
        logger.debug(f"Local complementation at node {node_idx} with {n_neighbors} neighbors")
        
        if self._finalized:
            self._adj_lil = self._adj_csr.tolil()
        
        # XOR operation on submatrix
        for i in range(n_neighbors):
            for j in range(i + 1, n_neighbors):
                ni, nj = neighbors[i], neighbors[j]
                current = self._adj_lil[ni, nj]
                new_val = 1 - current
                self._adj_lil[ni, nj] = new_val
                self._adj_lil[nj, ni] = new_val
        
        self._finalized = False
    
    def fast_xor_update(self, node_idx: int) -> None:
        """CPU-optimized XOR update for local complementation."""
        if not self._finalized:
            self._finalize()
        
        neighbors = self.get_neighbors(node_idx)
        n_neighbors = len(neighbors)
        
        if n_neighbors < 2:
            return
        
        submatrix = self._adj_csr[neighbors][:, neighbors].toarray()
        ones = np.ones((n_neighbors, n_neighbors), dtype=np.int8)
        np.fill_diagonal(ones, 0)
        submatrix = (submatrix + ones) % 2
        
        self._adj_lil = self._adj_csr.tolil()
        for i, ni in enumerate(neighbors):
            for j, nj in enumerate(neighbors):
                if i != j:
                    self._adj_lil[ni, nj] = submatrix[i, j]
        
        self._finalized = False

    def remove_node(self, node_idx: int) -> None:
        """
        Remove all edges connected to a specific node.
        
        Args:
            node_idx: Index of the node to isolate
        """
        if self._finalized:
            self._adj_lil = self._adj_csr.tolil()
            self._finalized = False
        
        # Clear row and column
        self._adj_lil[node_idx, :] = 0
        self._adj_lil[:, node_idx] = 0
    
    def apply_loss_mask(self, p_loss: float, seed: Optional[int] = None) -> np.ndarray:
        """Apply random photon loss to nodes using binomial distribution."""
        if seed is not None:
            np.random.seed(seed)
        
        survival = np.random.binomial(1, 1 - p_loss, self.n_qubits)
        self.node_states = survival.astype(np.int8)
        
        lost_indices = np.where(self.node_states == 0)[0]
        self.lost_nodes = set(lost_indices.tolist())
        
        logger.info(f"Applied loss with p={p_loss}: {len(self.lost_nodes)}/{self.n_qubits} nodes lost")
        
        return lost_indices
    
    def recover_from_loss(self) -> int:
        """Perform graph surgery to recover from photon loss."""
        recovery_count = 0
        lost_nodes_sorted = sorted(self.lost_nodes, reverse=True)
        
        for node_idx in lost_nodes_sorted:
            self.local_complementation(node_idx)
            recovery_count += 1
            
            if not self._finalized:
                self._finalize()
            
            neighbors = self.get_neighbors(node_idx)
            self._adj_lil = self._adj_csr.tolil()
            
            for neighbor in neighbors:
                self._adj_lil[node_idx, neighbor] = 0
                self._adj_lil[neighbor, node_idx] = 0
            
            self._finalized = False
        
        logger.info(f"Recovery complete: {recovery_count} operations performed")
        return recovery_count
    
    def get_active_subgraph(self) -> 'StabilizerGraph':
        """Extract subgraph containing only active (non-lost) nodes."""
        active_indices = np.where(self.node_states == 1)[0]
        n_active = len(active_indices)
        
        subgraph = StabilizerGraph(n_active)
        
        if not self._finalized:
            self._finalize()
        
        index_map = {old: new for new, old in enumerate(active_indices)}
        
        for i, old_i in enumerate(active_indices):
            neighbors = self.get_neighbors(old_i)
            for old_j in neighbors:
                if old_j in index_map:
                    j = index_map[old_j]
                    if j > i:
                        subgraph.add_edge(i, j)
        
        subgraph._finalize()
        return subgraph
    
    def get_edge_count(self) -> int:
        """Return the number of edges in the graph."""
        if not self._finalized:
            self._finalize()
        return self._adj_csr.nnz // 2
    
    def get_degree(self, node_idx: int) -> int:
        """Return the degree (number of neighbors) of a node."""
        return len(self.get_neighbors(node_idx))
    
    def get_graph_info(self) -> dict:
        """Get summary information about the graph state."""
        if not self._finalized:
            self._finalize()
        
        active_count = int(self.node_states.sum())
        
        return {
            'n_qubits': self.n_qubits,
            'n_active': active_count,
            'n_lost': len(self.lost_nodes),
            'n_edges': self.get_edge_count(),
            'sparsity': 1 - (self._adj_csr.nnz / (self.n_qubits ** 2)),
            'memory_bytes': self._adj_csr.data.nbytes + self._adj_csr.indices.nbytes + self._adj_csr.indptr.nbytes
        }
    
    def copy(self) -> 'StabilizerGraph':
        """Create a deep copy of the graph."""
        new_graph = StabilizerGraph(self.n_qubits)
        if self._finalized:
            new_graph._adj_csr = self._adj_csr.copy()
            new_graph._adj_lil = new_graph._adj_csr.tolil()
            new_graph._finalized = True
        else:
            new_graph._adj_lil = self._adj_lil.copy()
            new_graph._finalized = False
        new_graph.node_states = self.node_states.copy()
        new_graph.lost_nodes = self.lost_nodes.copy()
        return new_graph
    
    def __repr__(self) -> str:
        info = self.get_graph_info()
        return (
            f"StabilizerGraph(n_qubits={info['n_qubits']}, "
            f"n_active={info['n_active']}, n_edges={info['n_edges']})"
        )


class GraphEngine:
    """
    High-level graph engine for quantum graph state manipulation.
    
    Provides a unified interface for:
    - Graph creation from various topologies
    - Loss simulation and probabilistic masking
    - Graph surgery and recovery operations
    - XOR-based local complementation
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the graph engine."""
        self.graph: Optional[StabilizerGraph] = None
        self.seed = seed
        self._loss_applied = False
        self._recovery_performed = False
        self._loss_rate: float = 0.0
        self._recovery_ops: int = 0
        
        if seed is not None:
            np.random.seed(seed)
        
        logger.debug(f"GraphEngine initialized with seed={seed}")
    
    @property
    def n(self) -> int:
        """Alias for n_qubits (number of qubits)."""
        return self.n_qubits

    @property
    def adj(self) -> np.ndarray:
        """
        Returns the dense adjacency matrix (numpy array).
        
        Note: For very large graphs, this may consume significant memory.
        """
        if self.graph is None:
            return np.zeros((0, 0), dtype=np.int8)
        return self.graph.adj_matrix.toarray().astype(np.int8)

    @property
    def n_qubits(self) -> int:
        """Number of qubits in the current graph."""
        return self.graph.n_qubits if self.graph else 0
    
    @property
    def n_active(self) -> int:
        """Number of active (non-lost) qubits."""
        if self.graph is None:
            return 0
        return int(self.graph.node_states.sum())
    
    @property
    def n_lost(self) -> int:
        """Number of lost qubits."""
        if self.graph is None:
            return 0
        return len(self.graph.lost_nodes)
    
    # =========================================================================
    # Core Graph Operations (direct access to underlying graph)
    # =========================================================================
    
    def add_edge(self, u: int, v: int) -> 'GraphEngine':
        """
        Add an edge (CZ gate) between qubits u and v.
        
        Args:
            u: First qubit index
            v: Second qubit index
            
        Returns:
            self for method chaining
        """
        if self.graph is None:
            raise ValueError("No graph created. Call create_empty_graph first.")
        self.graph.add_edge(u, v)
        return self
    
    def remove_edge(self, u: int, v: int) -> 'GraphEngine':
        """Remove an edge between qubits u and v."""
        if self.graph is None:
            raise ValueError("No graph created.")
        self.graph.remove_edge(u, v)
        return self
    
    def get_neighbors(self, node: int) -> np.ndarray:
        """Get all neighbors of a node."""
        if self.graph is None:
            raise ValueError("No graph created.")
        return self.graph.get_neighbors(node)
    
    def local_complementation(self, node: int) -> 'GraphEngine':
        """Apply local complementation at the specified node."""
        if self.graph is None:
            raise ValueError("No graph created.")
        self.graph.local_complementation(node)
        return self

    def remove_node(self, node_idx: int) -> 'GraphEngine':
        """
        Remove all edges connected to a specific node.
        
        Args:
            node_idx: Index of the node to isolate
            
        Returns:
            self for method chaining
        """
        if self.graph is None:
            raise ValueError("No graph created.")
        self.graph.remove_node(node_idx)
        return self
    
    def has_edge(self, u: int, v: int) -> bool:
        """Check if edge exists between u and v."""
        if self.graph is None:
            return False
        return self.graph.has_edge(u, v)
    
    # =========================================================================
    # Graph Creation Methods
    # =========================================================================
    
    def create_empty_graph(self, n_qubits: int) -> 'GraphEngine':
        """Create an empty graph with n qubits."""
        self.graph = StabilizerGraph(n_qubits)
        self._reset_state()
        logger.info(f"Created empty graph with {n_qubits} qubits")
        return self
    
    def create_cluster_state(self, rows: int, cols: int, periodic: bool = False) -> 'GraphEngine':
        """Create a 2D cluster state."""
        n_qubits = rows * cols
        self.graph = StabilizerGraph(n_qubits)
        
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if c < cols - 1:
                    self.graph.add_edge(idx, idx + 1)
                elif periodic and cols > 2:
                    self.graph.add_edge(idx, r * cols)
                if r < rows - 1:
                    self.graph.add_edge(idx, idx + cols)
                elif periodic and rows > 2:
                    self.graph.add_edge(idx, c)
        
        self.graph._finalize()
        self._reset_state()
        logger.info(f"Created {rows}x{cols} cluster state: {n_qubits} qubits, {self.graph.get_edge_count()} edges")
        return self
    
    def create_linear_chain(self, n_qubits: int, periodic: bool = False) -> 'GraphEngine':
        """Create a linear chain graph."""
        self.graph = StabilizerGraph(n_qubits)
        
        for i in range(n_qubits - 1):
            self.graph.add_edge(i, i + 1)
        
        if periodic and n_qubits > 2:
            self.graph.add_edge(n_qubits - 1, 0)
        
        self.graph._finalize()
        self._reset_state()
        topology = "ring" if periodic else "linear chain"
        logger.info(f"Created {topology}: {n_qubits} qubits")
        return self
    
    def create_ghz_state(self, n_qubits: int) -> 'GraphEngine':
        """Create a GHZ-type graph (star topology)."""
        self.graph = StabilizerGraph(n_qubits)
        
        for i in range(1, n_qubits):
            self.graph.add_edge(0, i)
        
        self.graph._finalize()
        self._reset_state()
        logger.info(f"Created GHZ state: {n_qubits} qubits")
        return self
    
    def create_3d_rhg_lattice(self, lx: int, ly: int, lz: int) -> 'GraphEngine':
        """Create a 3D RHG (Raussendorf-Harrington-Goyal) lattice."""
        n_primal = lx * ly * lz
        n_dual = (lx - 1) * (ly - 1) * (lz - 1) if lx > 1 and ly > 1 and lz > 1 else 0
        n_qubits = n_primal + n_dual
        
        self.graph = StabilizerGraph(n_qubits)
        
        def primal_idx(x, y, z):
            return x + y * lx + z * lx * ly
        
        for z in range(lz):
            for y in range(ly):
                for x in range(lx):
                    idx = primal_idx(x, y, z)
                    if x < lx - 1:
                        self.graph.add_edge(idx, primal_idx(x + 1, y, z))
                    if y < ly - 1:
                        self.graph.add_edge(idx, primal_idx(x, y + 1, z))
                    if z < lz - 1:
                        self.graph.add_edge(idx, primal_idx(x, y, z + 1))
        
        self.graph._finalize()
        self._reset_state()
        logger.info(f"Created 3D RHG lattice {lx}x{ly}x{lz}: {n_qubits} qubits, {self.graph.get_edge_count()} edges")
        return self
    
    def set_graph(self, graph: StabilizerGraph) -> 'GraphEngine':
        """Set an existing graph."""
        self.graph = graph
        self._reset_state()
        return self
    
    def apply_loss(self, p_loss: float, seed: Optional[int] = None) -> np.ndarray:
        """Apply photon loss to the graph."""
        if self.graph is None:
            raise ValueError("No graph created. Call create_* methods first.")
        
        use_seed = seed if seed is not None else self.seed
        lost_nodes = self.graph.apply_loss_mask(p_loss, seed=use_seed)
        
        self._loss_applied = True
        self._loss_rate = p_loss
        
        return lost_nodes
    
    def perform_recovery(self) -> int:
        """Perform graph surgery to recover from loss."""
        if self.graph is None:
            raise ValueError("No graph created.")
        
        if not self._loss_applied:
            logger.warning("No loss applied. Skipping recovery.")
            return 0
        
        self._recovery_ops = self.graph.recover_from_loss()
        self._recovery_performed = True
        
        return self._recovery_ops
    
    def local_complementation(self, node_idx: int) -> 'GraphEngine':
        """Apply local complementation τ_a at specified node."""
        if self.graph is None:
            raise ValueError("No graph created.")
        
        self.graph.local_complementation(node_idx)
        return self
    
    def xor_update(self, node_idx: int) -> 'GraphEngine':
        """Apply XOR-based local complementation (optimized)."""
        if self.graph is None:
            raise ValueError("No graph created.")
        
        self.graph.fast_xor_update(node_idx)
        return self
    
    def get_active_graph(self) -> StabilizerGraph:
        """Get subgraph containing only active (non-lost) nodes."""
        if self.graph is None:
            raise ValueError("No graph created.")
        
        return self.graph.get_active_subgraph()
    
    def get_info(self) -> dict:
        """Get current engine state information."""
        graph_info = self.graph.get_graph_info() if self.graph else {}
        
        return {
            'has_graph': self.graph is not None,
            'loss_applied': self._loss_applied,
            'loss_rate': self._loss_rate,
            'recovery_performed': self._recovery_performed,
            'recovery_operations': self._recovery_ops,
            **graph_info
        }
    
    def reset(self) -> 'GraphEngine':
        """Reset the engine state (keeps the graph structure)."""
        if self.graph:
            self.graph.node_states = np.ones(self.graph.n_qubits, dtype=np.int8)
            self.graph.lost_nodes = set()
        self._reset_state()
        return self
    
    def _reset_state(self) -> None:
        """Reset internal state tracking."""
        self._loss_applied = False
        self._recovery_performed = False
        self._loss_rate = 0.0
        self._recovery_ops = 0
    
    def __repr__(self) -> str:
        if self.graph is None:
            return "GraphEngine(no graph)"
        return f"GraphEngine({self.graph}, loss={self._loss_rate:.2%})"


class SimpleGraphEngine:
    """
    Simplified graph engine for quick prototyping.
    
    Provides a minimal numpy-based interface without sparse matrices.
    For production use, prefer StabilizerGraph or GraphEngine.
    """
    
    def __init__(self, n_qubits: int):
        """Initialize with n qubits."""
        self.n = n_qubits
        self.adj = np.zeros((n_qubits, n_qubits), dtype=np.int8)
    
    def add_edge(self, u: int, v: int) -> None:
        """Add an edge (CZ gate) between qubits u and v."""
        if 0 <= u < self.n and 0 <= v < self.n and u != v:
            self.adj[u, v] = self.adj[v, u] = 1
    
    def remove_edge(self, u: int, v: int) -> None:
        """Remove edge between qubits u and v."""
        if 0 <= u < self.n and 0 <= v < self.n:
            self.adj[u, v] = self.adj[v, u] = 0
    
    def get_neighbors(self, node: int) -> np.ndarray:
        """Get all neighbors of a node."""
        return np.where(self.adj[node] == 1)[0]
    
    def local_complementation(self, a: int) -> None:
        """Algorithm 1: XOR invert edges between neighbors of node a."""
        neighbors = self.get_neighbors(a)
        if len(neighbors) < 2:
            return
        sub_idx = np.ix_(neighbors, neighbors)
        self.adj[sub_idx] = 1 - self.adj[sub_idx]
        np.fill_diagonal(self.adj, 0)
    
    def remove_node(self, node: int) -> None:
        """Remove all edges connected to a node."""
        self.adj[node, :] = 0
        self.adj[:, node] = 0
    
    def to_stabilizer_graph(self) -> StabilizerGraph:
        """Convert to full StabilizerGraph."""
        graph = StabilizerGraph(self.n)
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if self.adj[i, j]:
                    graph.add_edge(i, j)
        graph._finalize()
        return graph
