"""
RHG Lattice: 3D Raussendorf-Harrington-Goyal Lattice Implementation
====================================================================

Implements the physical structure of 3D RHG lattice for fault-tolerant
measurement-based quantum computation (MBQC).

Key Features:
- Edge-based qubit positioning (Qx, Qy, Qz on cubic edges)
- Diamond connectivity pattern (4 neighbors per qubit)
- Open and Periodic boundary conditions
- Coordinate system: 4D tuple (x, y, z, axis) ↔ flat index

Reference:
    Raussendorf, R., Harrington, J., & Goyal, K. (2007).
    Topological fault-tolerance in cluster state quantum computation.
    New Journal of Physics, 9(6), 199.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, List, Optional, Dict, Set
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)


class Axis(IntEnum):
    """Qubit axis direction on cubic lattice edges."""
    X = 0  # Qx at (x+0.5, y, z)
    Y = 1  # Qy at (x, y+0.5, z)
    Z = 2  # Qz at (x, y, z+0.5)


class RHGLattice:
    """
    3D RHG (Raussendorf-Harrington-Goyal) Lattice Manager.
    
    Manages the coordinate system, connectivity, and stabilizer tracking
    for fault-tolerant quantum photonic simulations.
    
    Attributes:
        lx, ly, lz: Lattice dimensions (number of unit cells)
        boundary: 'open' or 'periodic'
        n_qubits: Total number of qubits in the lattice
        
    Example:
        >>> lattice = RHGLattice(4, 4, 4, boundary='periodic')
        >>> idx = lattice.coord_to_index(1, 2, 3, Axis.Z)
        >>> x, y, z, axis = lattice.index_to_coord(idx)
        >>> neighbors = lattice.get_neighbors(idx)
    """
    
    def __init__(self, lx: int, ly: int, lz: int, boundary: str = 'open'):
        """
        Initialize RHG lattice.
        
        Args:
            lx: Number of unit cells in x direction
            ly: Number of unit cells in y direction
            lz: Number of unit cells in z direction
            boundary: 'open' or 'periodic'
        """
        if boundary not in ('open', 'periodic'):
            raise ValueError(f"boundary must be 'open' or 'periodic', got '{boundary}'")
        
        self.lx = lx
        self.ly = ly
        self.lz = lz
        self.boundary = boundary
        
        # Calculate qubit counts per axis
        # For open boundary: Qx has (lx-1)*ly*lz, Qy has lx*(ly-1)*lz, Qz has lx*ly*(lz-1)
        # For periodic: each axis has lx*ly*lz
        if boundary == 'periodic':
            self.n_x = lx * ly * lz
            self.n_y = lx * ly * lz
            self.n_z = lx * ly * lz
        else:
            self.n_x = (lx - 1) * ly * lz if lx > 1 else 0
            self.n_y = lx * (ly - 1) * lz if ly > 1 else 0
            self.n_z = lx * ly * (lz - 1) if lz > 1 else 0
        
        self.n_qubits = self.n_x + self.n_y + self.n_z
        
        # Precompute axis offsets for flat indexing
        self._offset_x = 0
        self._offset_y = self.n_x
        self._offset_z = self.n_x + self.n_y
        
        # Cache for neighbor lookups (lazy initialization)
        self._neighbor_cache: Optional[Dict[int, List[int]]] = None
        
        logger.info(
            f"RHGLattice created: {lx}×{ly}×{lz}, {boundary} boundary, "
            f"{self.n_qubits} qubits (Qx:{self.n_x}, Qy:{self.n_y}, Qz:{self.n_z})"
        )
    
    # =========================================================================
    # Coordinate Transformation
    # =========================================================================
    
    def coord_to_index(self, x: int, y: int, z: int, axis: int) -> Optional[int]:
        """
        Convert 4D coordinate (x, y, z, axis) to flat index.
        
        Args:
            x, y, z: Unit cell coordinates
            axis: Qubit axis (0=X, 1=Y, 2=Z)
            
        Returns:
            Flat index, or None if coordinate is out of bounds
        """
        if axis == Axis.X:
            if self.boundary == 'periodic':
                if not (0 <= x < self.lx and 0 <= y < self.ly and 0 <= z < self.lz):
                    return None
                return self._offset_x + (z * self.ly + y) * self.lx + x
            else:
                if not (0 <= x < self.lx - 1 and 0 <= y < self.ly and 0 <= z < self.lz):
                    return None
                return self._offset_x + (z * self.ly + y) * (self.lx - 1) + x
                
        elif axis == Axis.Y:
            if self.boundary == 'periodic':
                if not (0 <= x < self.lx and 0 <= y < self.ly and 0 <= z < self.lz):
                    return None
                return self._offset_y + (z * self.ly + y) * self.lx + x
            else:
                if not (0 <= x < self.lx and 0 <= y < self.ly - 1 and 0 <= z < self.lz):
                    return None
                return self._offset_y + (z * (self.ly - 1) + y) * self.lx + x
                
        elif axis == Axis.Z:
            if self.boundary == 'periodic':
                if not (0 <= x < self.lx and 0 <= y < self.ly and 0 <= z < self.lz):
                    return None
                return self._offset_z + (z * self.ly + y) * self.lx + x
            else:
                if not (0 <= x < self.lx and 0 <= y < self.ly and 0 <= z < self.lz - 1):
                    return None
                return self._offset_z + (z * self.ly + y) * self.lx + x
        
        return None
    
    def index_to_coord(self, idx: int) -> Optional[Tuple[int, int, int, int]]:
        """
        Convert flat index to 4D coordinate (x, y, z, axis).
        
        Args:
            idx: Flat qubit index
            
        Returns:
            Tuple (x, y, z, axis), or None if index is invalid
        """
        if idx < 0 or idx >= self.n_qubits:
            return None
        
        if idx < self._offset_y:
            # Axis X
            local_idx = idx - self._offset_x
            if self.boundary == 'periodic':
                dim_x = self.lx
            else:
                dim_x = self.lx - 1
            
            x = local_idx % dim_x
            local_idx //= dim_x
            y = local_idx % self.ly
            z = local_idx // self.ly
            return (x, y, z, Axis.X)
            
        elif idx < self._offset_z:
            # Axis Y
            local_idx = idx - self._offset_y
            if self.boundary == 'periodic':
                dim_y = self.ly
            else:
                dim_y = self.ly - 1
            
            x = local_idx % self.lx
            local_idx //= self.lx
            y = local_idx % dim_y
            z = local_idx // dim_y
            return (x, y, z, Axis.Y)
            
        else:
            # Axis Z
            local_idx = idx - self._offset_z
            if self.boundary == 'periodic':
                dim_z = self.lz
            else:
                dim_z = self.lz - 1
            
            x = local_idx % self.lx
            local_idx //= self.lx
            y = local_idx % self.ly
            z = local_idx // self.ly
            return (x, y, z, Axis.Z)
    
    def get_physical_position(self, idx: int) -> Optional[Tuple[float, float, float]]:
        """
        Get the physical (half-integer) position of a qubit.
        
        Args:
            idx: Flat qubit index
            
        Returns:
            Physical coordinates (px, py, pz) where edges are at half-integers
        """
        coord = self.index_to_coord(idx)
        if coord is None:
            return None
        
        x, y, z, axis = coord
        
        if axis == Axis.X:
            return (x + 0.5, float(y), float(z))
        elif axis == Axis.Y:
            return (float(x), y + 0.5, float(z))
        else:  # Axis.Z
            return (float(x), float(y), z + 0.5)
    
    # =========================================================================
    # Connectivity (Diamond Pattern)
    # =========================================================================
    
    def get_neighbors(self, idx: int) -> List[int]:
        """
        Get the 4 neighbors of a qubit in the diamond pattern.
        
        Each qubit connects to 4 qubits of the other two axes
        that share the same face of the cubic lattice.
        
        Args:
            idx: Flat qubit index
            
        Returns:
            List of neighboring qubit indices (up to 4)
        """
        coord = self.index_to_coord(idx)
        if coord is None:
            return []
        
        x, y, z, axis = coord
        neighbors = []
        
        if axis == Axis.X:
            # Qx(x,y,z) connects to:
            # Qy(x,y,z), Qy(x+1,y,z), Qz(x,y,z), Qz(x+1,y,z)
            self._add_neighbor(neighbors, x, y, z, Axis.Y)
            self._add_neighbor(neighbors, x + 1, y, z, Axis.Y)
            self._add_neighbor(neighbors, x, y, z, Axis.Z)
            self._add_neighbor(neighbors, x + 1, y, z, Axis.Z)
            
        elif axis == Axis.Y:
            # Qy(x,y,z) connects to:
            # Qx(x,y,z), Qx(x,y+1,z), Qz(x,y,z), Qz(x,y+1,z)
            self._add_neighbor(neighbors, x, y, z, Axis.X)
            self._add_neighbor(neighbors, x, y + 1, z, Axis.X)
            self._add_neighbor(neighbors, x, y, z, Axis.Z)
            self._add_neighbor(neighbors, x, y + 1, z, Axis.Z)
            
        else:  # Axis.Z
            # Qz(x,y,z) connects to:
            # Qx(x,y,z), Qx(x,y,z+1), Qy(x,y,z), Qy(x,y,z+1)
            self._add_neighbor(neighbors, x, y, z, Axis.X)
            self._add_neighbor(neighbors, x, y, z + 1, Axis.X)
            self._add_neighbor(neighbors, x, y, z, Axis.Y)
            self._add_neighbor(neighbors, x, y, z + 1, Axis.Y)
        
        return neighbors
    
    def _add_neighbor(self, neighbors: List[int], x: int, y: int, z: int, axis: int) -> None:
        """Helper to add a neighbor with boundary wrapping."""
        if self.boundary == 'periodic':
            x = x % self.lx
            y = y % self.ly
            z = z % self.lz
        
        idx = self.coord_to_index(x, y, z, axis)
        if idx is not None:
            neighbors.append(idx)
    
    def generate_edges(self, engine) -> int:
        """
        Generate all edges in the RHG lattice and add them to the engine.
        
        Args:
            engine: GraphEngine instance to add edges to
            
        Returns:
            Number of edges added
        """
        edge_count = 0
        added_edges: Set[Tuple[int, int]] = set()
        
        for idx in range(self.n_qubits):
            neighbors = self.get_neighbors(idx)
            for neighbor in neighbors:
                # Avoid adding duplicate edges
                edge = (min(idx, neighbor), max(idx, neighbor))
                if edge not in added_edges:
                    engine.add_edge(idx, neighbor)
                    added_edges.add(edge)
                    edge_count += 1
        
        logger.info(f"Generated {edge_count} edges for RHG lattice")
        return edge_count
    
    # =========================================================================
    # Stabilizer and Syndrome Tracking
    # =========================================================================
    
    def get_stabilizer_coords(self, idx: int) -> Optional[Tuple[float, float, float]]:
        """
        Alias for get_physical_position for API consistency.
        
        Returns the stabilizer measurement location for a qubit.
        """
        return self.get_physical_position(idx)
    
    def get_face_qubits(self, x: int, y: int, z: int, face: str) -> List[int]:
        """
        Get the 4 qubits surrounding a face of the cubic lattice.
        
        Args:
            x, y, z: Unit cell coordinates
            face: 'xy', 'xz', or 'yz'
            
        Returns:
            List of 4 qubit indices forming the face
        """
        qubits = []
        
        if face == 'xy':
            self._add_neighbor(qubits, x, y, z, Axis.X)
            self._add_neighbor(qubits, x, y + 1, z, Axis.X)
            self._add_neighbor(qubits, x, y, z, Axis.Y)
            self._add_neighbor(qubits, x + 1, y, z, Axis.Y)
        elif face == 'xz':
            self._add_neighbor(qubits, x, y, z, Axis.X)
            self._add_neighbor(qubits, x, y, z + 1, Axis.X)
            self._add_neighbor(qubits, x, y, z, Axis.Z)
            self._add_neighbor(qubits, x + 1, y, z, Axis.Z)
        elif face == 'yz':
            self._add_neighbor(qubits, x, y, z, Axis.Y)
            self._add_neighbor(qubits, x, y, z + 1, Axis.Y)
            self._add_neighbor(qubits, x, y, z, Axis.Z)
            self._add_neighbor(qubits, x, y + 1, z, Axis.Z)
        
        return qubits
    
    def compute_syndrome(self, lost_nodes: np.ndarray) -> np.ndarray:
        """
        Compute the syndrome pattern from lost qubits.
        
        In RHG lattice, each face has a stabilizer. If an odd number
        of qubits around a face are lost, that face has a syndrome.
        
        Args:
            lost_nodes: Array of lost qubit indices
            
        Returns:
            Array of syndrome locations (face centers with odd parity)
        """
        lost_set = set(lost_nodes.tolist())
        syndrome_faces = []
        
        # Check all faces
        for z in range(self.lz):
            for y in range(self.ly):
                for x in range(self.lx):
                    for face in ['xy', 'xz', 'yz']:
                        face_qubits = self.get_face_qubits(x, y, z, face)
                        lost_count = sum(1 for q in face_qubits if q in lost_set)
                        
                        if lost_count % 2 == 1:
                            # Odd parity → syndrome
                            if face == 'xy':
                                syndrome_faces.append((x + 0.5, y + 0.5, z))
                            elif face == 'xz':
                                syndrome_faces.append((x + 0.5, y, z + 0.5))
                            else:  # yz
                                syndrome_faces.append((x, y + 0.5, z + 0.5))
        
        return np.array(syndrome_faces) if syndrome_faces else np.array([]).reshape(0, 3)
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_info(self) -> Dict:
        """Get lattice information."""
        return {
            'dimensions': (self.lx, self.ly, self.lz),
            'boundary': self.boundary,
            'n_qubits': self.n_qubits,
            'n_x': self.n_x,
            'n_y': self.n_y,
            'n_z': self.n_z,
        }
    
    def __repr__(self) -> str:
        return f"RHGLattice({self.lx}×{self.ly}×{self.lz}, {self.boundary}, {self.n_qubits} qubits)"
