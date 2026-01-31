"""
Graph Engine: XOR-based Graph Operations (Algorithm 1)
=======================================================

Implements efficient graph state manipulation using XOR operations.
Optimized for quantum photonics loss recovery.
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
        """Add an edge between nodes i and j."""
        if i == j: return
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
        """Apply local complementation τ_a at node a."""
        neighbors = self.get_neighbors(node_idx)
        if len(neighbors) < 2: return
        
        if self._finalized:
            self._adj_lil = self._adj_csr.tolil()
        
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                ni, nj = neighbors[i], neighbors[j]
                val = 1 - self._adj_lil[ni, nj]
                self._adj_lil[ni, nj] = val
                self._adj_lil[nj, ni] = val
        self._finalized = False

    def remove_node(self, node_idx: int) -> None:
        """Remove all edges connected to a specific node."""
        if self._finalized:
            self._adj_lil = self._adj_csr.tolil()
            self._finalized = False
        self._adj_lil[node_idx, :] = 0
        self._adj_lil[:, node_idx] = 0


class GraphEngine:
    """XOR 기반 고속 퀀텀 그래프 연산 엔진 (LAGC Core)"""
    def __init__(self, n_qubits: int = 0):
        self.n = n_qubits
        self.adj = np.zeros((n_qubits, n_qubits), dtype=np.int8)

    def add_edge(self, u, v):
        """[핵심] 두 큐비트 사이에 CZ 게이트(얽힘) 적용"""
        if 0 <= u < self.n and 0 <= v < self.n and u != v:
            self.adj[u, v] = self.adj[v, u] = 1
        return self

    def get_neighbors(self, node):
        """특정 노드에 연결된 이웃 반환"""
        if 0 <= node < self.n:
            return np.where(self.adj[node] == 1)[0]
        return np.array([], dtype=np.intp)

    def local_complementation(self, a):
        """Algorithm 1: 그래프 토폴로지 변환 (이웃 간 연결 XOR 반전)"""
        neighbors = self.get_neighbors(a)
        if len(neighbors) < 2: return self
        sub_idx = np.ix_(neighbors, neighbors)
        self.adj[sub_idx] = 1 - self.adj[sub_idx]
        np.fill_diagonal(self.adj, 0)
        return self

    def create_empty_graph(self, n_qubits):
        self.n = n_qubits
        self.adj = np.zeros((n_qubits, n_qubits), dtype=np.int8)
        return self

    def remove_node(self, node_idx):
        if 0 <= node_idx < self.n:
            self.adj[node_idx, :] = 0
            self.adj[:, node_idx] = 0
        return self

    # === Alias Properties for Compatibility ===
    @property
    def n_qubits(self): return self.n
    
    def has_edge(self, u, v):
        return bool(self.adj[u, v]) if 0 <= u < self.n and 0 <= v < self.n else False

    def __repr__(self):
        return f"GraphEngine(n={self.n}, edges={int(np.sum(self.adj)//2)})"


# 별칭 설정
StabilizerGraph = GraphEngine
SimpleGraphEngine = GraphEngine
