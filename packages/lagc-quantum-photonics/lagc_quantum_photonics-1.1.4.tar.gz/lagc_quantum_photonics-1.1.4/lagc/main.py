"""
LAGC: LossAware-GraphCompiler Main API
=======================================

The primary user interface for quantum photonics simulation.
Integrates all components for end-to-end simulation workflow.

Features:
- Lattice creation and loss modeling
- Automatic graph surgery for loss recovery
- Memory-efficient tensor network contraction
- Hardware-aware error mitigation

Example:
    >>> from lagc import LAGC
    >>> 
    >>> # Create simulator
    >>> sim = LAGC(ram_limit_gb=8)
    >>> 
    >>> # Build 3D RHG lattice
    >>> sim.create_lattice('3d_rhg', 10, 10, 10)
    >>> 
    >>> # Apply 5% photon loss and recover
    >>> sim.apply_loss(p_loss=0.05)
    >>> 
    >>> # Run simulation
    >>> result = sim.run_simulation()
    >>> 
    >>> # Get results
    >>> print(f"Fidelity: {result['fidelity']:.4f}")
    >>> print(f"Active qubits: {result['n_active']}")
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass
import time
import logging

from lagc.core.graph_engine import StabilizerGraph, GraphEngine
from lagc.core.tensor_slicer import TensorSlicer, TensorNetwork
from lagc.core.recovery import LossRecovery
from lagc.models.hardware import HardwareModel, HardwareParams
from lagc.models.topologies import TopologyGenerator
from lagc.simulation.contraction import TensorContractor, ContractionResult
from lagc.simulation.scheduler import ParallelScheduler
from lagc.utils.memory import MemoryManager, get_memory_stats

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@dataclass
class SimulationResult:
    """
    Complete simulation result container.
    
    Attributes:
        amplitude: Final quantum state amplitude
        fidelity: Estimated output fidelity
        n_qubits: Total number of qubits
        n_active: Number of active (not lost) qubits
        n_lost: Number of lost qubits
        n_edges: Number of edges in final graph
        execution_time: Total simulation time in seconds
        memory_peak_gb: Peak memory usage in GB
        metadata: Additional simulation information
    """
    amplitude: complex
    fidelity: float
    n_qubits: int
    n_active: int
    n_lost: int
    n_edges: int
    execution_time: float
    memory_peak_gb: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'amplitude': complex(self.amplitude),
            'probability': abs(self.amplitude) ** 2,
            'fidelity': self.fidelity,
            'n_qubits': self.n_qubits,
            'n_active': self.n_active,
            'n_lost': self.n_lost,
            'n_edges': self.n_edges,
            'execution_time': self.execution_time,
            'memory_peak_gb': self.memory_peak_gb,
            **self.metadata
        }
    
    def __repr__(self) -> str:
        return (
            f"SimulationResult(\n"
            f"  fidelity={self.fidelity:.4f},\n"
            f"  qubits={self.n_qubits} (active={self.n_active}, lost={self.n_lost}),\n"
            f"  edges={self.n_edges},\n"
            f"  time={self.execution_time:.2f}s,\n"
            f"  memory={self.memory_peak_gb:.2f}GB\n"
            f")"
        )


class LAGC:
    """
    LossAware-GraphCompiler: Main simulation interface.
    
    A high-performance quantum photonics simulation library that:
    1. Creates graph state lattices (3D RHG, 2D Cluster, etc.)
    2. Models realistic photon loss
    3. Performs graph surgery to correct topological defects
    4. Contracts tensor networks with memory-efficient slicing
    5. Applies hardware-aware error mitigation
    
    Architecture:
    - Stabilizer Graph (Symbolic): scipy.sparse.csr_matrix for efficient graph operations
    - Sliced Tensor Network (Numerical): List[numpy.ndarray] for amplitude calculation
    
    Attributes:
        n_qubits: Current number of qubits
        graph: StabilizerGraph representing the current state
        hardware: HardwareModel for error characterization
        ram_limit_gb: Maximum RAM usage
    """
    
    def __init__(
        self,
        n_qubits: Optional[int] = None,
        ram_limit_gb: float = 8.0,
        hardware: Optional[Union[str, HardwareModel]] = None,
        n_workers: Optional[int] = None,
        seed: Optional[int] = None
    ):
        """
        Initialize LAGC simulator.
        
        Args:
            n_qubits: Initial number of qubits (optional, set by create_lattice)
            ram_limit_gb: RAM limit in GB for tensor operations
            hardware: Hardware model name ('ideal', 'realistic', etc.) or HardwareModel
            n_workers: Number of parallel workers (default: all CPU cores)
            seed: Random seed for reproducibility
        """
        self.n_qubits = n_qubits or 0
        self.ram_limit_gb = ram_limit_gb
        self.seed = seed
        
        # Core components
        self.engine = GraphEngine(self.n_qubits)
        self.graph = self.engine # Alias for backward compatibility
        self._tensor_network: Optional[TensorNetwork] = None
        
        # Hardware model
        if hardware is None:
            self.hardware = HardwareModel.from_preset('realistic')
        elif isinstance(hardware, str):
            self.hardware = HardwareModel.from_preset(hardware)
        else:
            self.hardware = hardware
        
        # Processing components
        self.tensor_slicer = TensorSlicer(
            ram_limit_gb=ram_limit_gb,
            n_workers=n_workers
        )
        self.contractor = TensorContractor()
        self.scheduler = ParallelScheduler(n_workers=n_workers)
        self.recovery = LossRecovery(engine=self.engine)
        self.memory = MemoryManager(limit_gb=ram_limit_gb)
        self.topology_gen = TopologyGenerator(seed=seed)
        
        # State tracking
        self._loss_applied = False
        self._recovery_performed = False
        self._simulation_run = False
        self._last_result: Optional[SimulationResult] = None
        
        if seed is not None:
            np.random.seed(seed)
        
        logger.info(
            f"LAGC initialized: RAM limit={ram_limit_gb}GB, "
            f"hardware={type(self.hardware).__name__}"
        )
    
    # =========================================================================
    # Convenience Properties
    # =========================================================================
    
    @property
    def n_active(self) -> int:
        """Number of active (non-lost) qubits."""
        n_lost = len(self._lost_indices) if hasattr(self, '_lost_indices') else 0
        return self.engine.n - n_lost
    
    @property
    def n_lost(self) -> int:
        """Number of lost qubits."""
        return len(self._lost_indices) if hasattr(self, '_lost_indices') else 0
    
    @property
    def n_edges(self) -> int:
        """Number of edges in the current graph."""
        return int(np.sum(self.engine.adj) // 2)
    
    def create_lattice(
        self,
        topology: str,
        *dims,
        periodic: bool = False
    ) -> 'LAGC':
        """
        Create a quantum lattice/graph state.
        
        Available topologies:
        - '3d_rhg': 3D RHG lattice (lx, ly, lz)
        - '2d_cluster': 2D cluster state (rows, cols)
        - 'linear': Linear chain (n)
        - 'ghz': GHZ state (n)
        - 'ring': Ring cluster (n)
        - 'complete': Complete graph (n)
        
        Args:
            topology: Topology type
            *dims: Dimension arguments
            periodic: Use periodic boundary conditions
            
        Returns:
            self for method chaining
            
        Example:
            >>> sim = LAGC().create_lattice('3d_rhg', 10, 10, 10)
        """
        logger.info(f"Creating lattice: {topology} {dims}")
        
        # Clear previous lattice metadata
        self.rhg_lattice = None
        
        if topology == '3d_rhg':
            lx, ly, lz = dims[:3] if len(dims) >= 3 else (dims[0], dims[0], dims[0])
            boundary = 'periodic' if periodic else 'open'
            self.graph, self.rhg_lattice = self.topology_gen.create_3d_rhg_lattice(lx, ly, lz, boundary)
        
        elif topology == '2d_cluster':
            rows, cols = dims[:2] if len(dims) >= 2 else (dims[0], dims[0])
            self.graph = self.topology_gen.create_2d_cluster_state(rows, cols, periodic)
        
        elif topology == 'linear':
            n = dims[0] if dims else 10
            self.graph = self.topology_gen.create_linear_cluster(n)
        
        elif topology == 'ghz':
            n = dims[0] if dims else 10
            self.graph = self.topology_gen.create_ghz_state(n)
        
        elif topology == 'ring':
            n = dims[0] if dims else 10
            self.graph = self.topology_gen.create_ring_cluster(n)
        
        elif topology == 'complete':
            n = dims[0] if dims else 10
            self.graph = self.topology_gen.create_complete_graph(n)
        
        else:
            available = self.topology_gen.list_topologies()
            raise ValueError(f"Unknown topology '{topology}'. Available: {available}")
        
        self.n_qubits = self.graph.n_qubits
        self.engine = self.graph
        self.recovery.engine = self.engine
        self._loss_applied = False
        self._recovery_performed = False
        self._simulation_run = False
        self._tensor_network = None
        self._lost_indices = np.array([], dtype=np.int64)
        
        logger.info(
            f"Lattice created: {self.n_qubits} qubits, {self.n_edges} edges"
        )
        
        return self
    
    def apply_loss(
        self,
        p_loss: float,
        seed: Optional[int] = None,
        auto_recover: bool = True
    ) -> 'LAGC':
        """
        Apply photon loss to the lattice.
        
        Simulates random photon loss using binomial distribution.
        Optionally performs automatic graph surgery for recovery.
        
        Args:
            p_loss: Probability of losing each photon (0 to 1)
            seed: Random seed for reproducibility
            auto_recover: Automatically perform loss recovery
            
        Returns:
            self for method chaining
            
        Example:
            >>> sim.apply_loss(p_loss=0.05)
        """
        if self.engine is None or self.engine.n == 0:
            raise RuntimeError("No lattice created.")
        
        rng = np.random.default_rng(seed or self.seed)
        survival = rng.binomial(1, 1 - p_loss, self.engine.n)
        lost_indices = np.where(survival == 0)[0]
        
        self._lost_indices = lost_indices
        self._loss_applied = True
        
        if auto_recover and len(lost_indices) > 0:
            self.recover_from_loss()
        
        return self
    
    def recover_from_loss(self) -> 'LAGC':
        """Perform graph surgery using the simplified recovery module."""
        if not hasattr(self, '_lost_indices') or len(self._lost_indices) == 0:
            return self
        
        for node in self._lost_indices:
            self.recovery.handle_loss(node)
        
        self._recovery_performed = True
        return self
    
    # =========================================================================
    # RHG Lattice Specific APIs
    # =========================================================================
    
    def get_stabilizer_coords(self, index: int) -> Optional[Tuple[float, float, float]]:
        """
        Get the physical position of a qubit in the RHG lattice.
        
        Args:
            index: Flat qubit index
            
        Returns:
            Physical (x, y, z) coordinates, or None if not RHG lattice
        """
        if self.rhg_lattice is None:
            logger.warning("get_stabilizer_coords requires RHG lattice. Use create_lattice('3d_rhg', ...)")
            return None
        return self.rhg_lattice.get_stabilizer_coords(index)
    
    def analyze_syndrome(self) -> Optional[Dict]:
        """
        Analyze syndrome pattern after loss recovery.
        
        Computes syndrome defects, percolation status, and logical error estimation.
        Only available for RHG lattice.
        
        Returns:
            Analysis dictionary with 'percolates', 'syndrome_count', etc.
        """
        if self.rhg_lattice is None:
            logger.warning("analyze_syndrome requires RHG lattice.")
            return None
        
        from lagc.analysis.syndrome import SyndromeAnalyzer
        analyzer = SyndromeAnalyzer(self.rhg_lattice)
        return analyzer.analyze(self.engine, self._lost_indices)
    
    def convert_to_tensor_network(self) -> TensorNetwork:
        """
        Convert current graph state to tensor network representation.
        
        This is the numerical representation used for amplitude calculation.
        
        Returns:
            TensorNetwork ready for contraction
        """
        if self.graph is None:
            raise RuntimeError("No lattice created. Call create_lattice() first.")
        
        logger.info("Converting graph state to tensor network")
        
        # Use active subgraph if loss was applied
        if self._loss_applied:
            active_graph = self.graph.get_active_subgraph()
        else:
            active_graph = self.graph
        
        self._tensor_network = self.contractor.graph_to_tensor_network(active_graph)
        
        logger.info(f"Tensor network created: {self._tensor_network.n_tensors} tensors")
        
        return self._tensor_network
    
    def run_simulation(
        self,
        use_slicing: bool = True,
        parallel: bool = True
    ) -> SimulationResult:
        """
        Run the complete simulation workflow.
        
        Workflow:
        1. Convert graph to tensor network (if not already done)
        2. Estimate memory requirements
        3. Contract tensor network (with slicing if needed)
        4. Apply error mitigation
        5. Return results
        
        Args:
            use_slicing: Enable memory-efficient slicing
            parallel: Enable parallel processing
            
        Returns:
            SimulationResult with amplitude, fidelity, and metadata
        """
        if self.graph is None:
            raise RuntimeError("No lattice created. Call create_lattice() first.")
        
        logger.info("Starting simulation")
        start_time = time.time()
        
        # Track memory
        with self.memory.track() as mem_tracker:
            # Convert to tensor network if needed
            if self._tensor_network is None:
                self.convert_to_tensor_network()
            
            # Estimate memory
            estimated_mem = self.tensor_slicer.estimate_memory(
                self._tensor_network.tensors
            )
            
            logger.info(f"Estimated memory: {estimated_mem / 1e9:.2f} GB")
            
            # Choose contraction strategy
            if use_slicing and estimated_mem > self.tensor_slicer.ram_limit_bytes:
                logger.info("Using recursive slicing for memory efficiency")
                
                if parallel:
                    amplitude = self.tensor_slicer.parallel_slice_contract(
                        self._tensor_network
                    )
                else:
                    amplitude = self.tensor_slicer.recursive_slice_contract(
                        self._tensor_network
                    )
            else:
                # Direct contraction
                result = self.contractor.contract(self._tensor_network)
                amplitude = result.amplitude
        
        execution_time = time.time() - start_time
        
        # Apply error mitigation
        if isinstance(amplitude, np.ndarray):
            amplitude = complex(amplitude.flat[0]) if amplitude.size > 0 else 0j
        else:
            amplitude = complex(amplitude)
        
        recovery_result = self.recovery.mitigate_errors(
            amplitude,
            n_qubits=self.n_qubits,
            loss_rate=len(self.graph.lost_nodes) / self.n_qubits if self.n_qubits > 0 else 0
        )
        
        # Get graph info
        graph_info = self.graph.get_graph_info()
        
        # Build result
        result = SimulationResult(
            amplitude=recovery_result.corrected_amplitude,
            fidelity=recovery_result.fidelity,
            n_qubits=self.n_qubits,
            n_active=graph_info['n_active'],
            n_lost=graph_info['n_lost'],
            n_edges=graph_info['n_edges'],
            execution_time=execution_time,
            memory_peak_gb=self.memory.get_peak_usage() / 1e9,
            metadata={
                'raw_amplitude': amplitude,
                'log_probability': recovery_result.log_probability,
                'n_corrections': recovery_result.n_corrections,
                'slicing_stats': self.tensor_slicer.get_statistics(),
                'hardware': self.hardware.params.to_dict(),
            }
        )
        
        self._simulation_run = True
        self._last_result = result
        
        logger.info(f"Simulation complete: fidelity={result.fidelity:.4f}, time={execution_time:.2f}s")
        
        return result
    
    def get_fidelity(self) -> float:
        """
        Get the fidelity of the current state.
        
        If simulation hasn't been run, estimates fidelity from
        hardware model and loss information.
        
        Returns:
            Estimated fidelity (0 to 1)
        """
        if self._last_result is not None:
            return self._last_result.fidelity
        
        # Estimate without full simulation
        return self.recovery.estimate_fidelity(n_qubits=self.n_qubits)
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        Get current state information.
        
        Returns:
            Dictionary with graph and simulation state
        """
        info = {
            'n_qubits': self.n_qubits,
            'lattice_created': self.graph is not None,
            'loss_applied': self._loss_applied,
            'recovery_performed': self._recovery_performed,
            'simulation_run': self._simulation_run,
            'ram_limit_gb': self.ram_limit_gb,
        }
        
        if self.graph is not None:
            info.update(self.graph.get_graph_info())
        
        if self._last_result is not None:
            info['last_result'] = self._last_result.to_dict()
        
        return info
    
    def reset(self) -> 'LAGC':
        """
        Reset simulation state while keeping configuration.
        
        Returns:
            self for method chaining
        """
        self.graph = None
        self._tensor_network = None
        self._loss_applied = False
        self._recovery_performed = False
        self._simulation_run = False
        self._last_result = None
        self.recovery.reset()
        self.tensor_slicer.reset_statistics()
        
        logger.info("Simulation state reset")
        
        return self
    
    def scan_loss_rates(
        self,
        loss_rates: List[float],
        topology: str = '2d_cluster',
        dims: Tuple = (10, 10),
        n_samples: int = 1
    ) -> Dict[str, List]:
        """
        Scan fidelity across multiple loss rates.
        
        Useful for characterizing loss tolerance of different topologies.
        
        Args:
            loss_rates: List of loss probabilities to test
            topology: Lattice topology
            dims: Lattice dimensions
            n_samples: Number of samples per loss rate
            
        Returns:
            Dictionary with loss_rates and fidelities lists
        """
        results = {
            'loss_rates': [],
            'fidelities': [],
            'n_active': [],
            'execution_times': []
        }
        
        for p_loss in loss_rates:
            sample_fidelities = []
            
            for sample in range(n_samples):
                self.reset()
                self.create_lattice(topology, *dims)
                self.apply_loss(p_loss, seed=self.seed + sample if self.seed else None)
                result = self.run_simulation()
                sample_fidelities.append(result.fidelity)
            
            avg_fidelity = np.mean(sample_fidelities)
            results['loss_rates'].append(p_loss)
            results['fidelities'].append(avg_fidelity)
            results['n_active'].append(self._last_result.n_active)
            results['execution_times'].append(self._last_result.execution_time)
            
            logger.info(f"Loss rate {p_loss:.3f}: fidelity={avg_fidelity:.4f}")
        
        return results
    
    def __repr__(self) -> str:
        status = "ready" if self.graph is not None else "uninitialized"
        return (
            f"LAGC(n_qubits={self.n_qubits}, "
            f"ram_limit={self.ram_limit_gb}GB, "
            f"status={status})"
        )


# Convenience function for quick simulations
def quick_simulation(
    topology: str,
    dims: Tuple,
    p_loss: float = 0.0,
    hardware: str = 'realistic',
    ram_limit_gb: float = 8.0
) -> SimulationResult:
    """
    Run a quick simulation with minimal setup.
    
    Args:
        topology: Lattice topology
        dims: Lattice dimensions
        p_loss: Loss probability
        hardware: Hardware model name
        ram_limit_gb: RAM limit
        
    Returns:
        SimulationResult
        
    Example:
        >>> result = quick_simulation('2d_cluster', (10, 10), p_loss=0.05)
        >>> print(f"Fidelity: {result.fidelity:.4f}")
    """
    sim = LAGC(ram_limit_gb=ram_limit_gb, hardware=hardware)
    sim.create_lattice(topology, *dims)
    
    if p_loss > 0:
        sim.apply_loss(p_loss)
    
    return sim.run_simulation()
