"""
LAGC Tests: Core Module Tests
==============================

Unit tests for LAGC core functionality.
"""

import pytest
import numpy as np
from scipy.sparse import csr_matrix

# Import LAGC modules
from lagc.core.graph_engine import StabilizerGraph
from lagc.core.tensor_slicer import TensorSlicer, TensorNetwork
from lagc.core.recovery import LossRecovery


class TestStabilizerGraph:
    """Tests for StabilizerGraph class."""
    
    def test_creation(self):
        """Test graph creation."""
        graph = StabilizerGraph(10)
        assert graph.n_qubits == 10
        assert graph.get_edge_count() == 0
    
    def test_add_edge(self):
        """Test edge addition."""
        graph = StabilizerGraph(5)
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        
        assert graph.has_edge(0, 1)
        assert graph.has_edge(1, 0)  # Symmetric
        assert graph.has_edge(1, 2)
        assert not graph.has_edge(0, 2)
        assert graph.get_edge_count() == 2
    
    def test_remove_edge(self):
        """Test edge removal."""
        graph = StabilizerGraph(3)
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        
        graph.remove_edge(0, 1)
        
        assert not graph.has_edge(0, 1)
        assert graph.has_edge(1, 2)
        assert graph.get_edge_count() == 1
    
    def test_neighbors(self):
        """Test neighbor retrieval."""
        graph = StabilizerGraph(5)
        graph.add_edge(0, 1)
        graph.add_edge(0, 2)
        graph.add_edge(0, 3)
        
        neighbors = graph.get_neighbors(0)
        
        assert len(neighbors) == 3
        assert set(neighbors) == {1, 2, 3}
    
    def test_local_complementation(self):
        """Test local complementation (τ_a operation)."""
        # Create triangle: 0-1, 1-2, 0-2
        graph = StabilizerGraph(3)
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        graph.add_edge(0, 2)
        
        # τ_0 on node 0: inverts edge between neighbors 1 and 2
        graph.local_complementation(0)
        
        # Edge 1-2 should be removed (was present, now inverted)
        assert not graph.has_edge(1, 2)
        assert graph.has_edge(0, 1)  # These remain
        assert graph.has_edge(0, 2)
    
    def test_xor_update(self):
        """Test fast XOR update (alias for local complementation)."""
        graph = StabilizerGraph(4)
        graph.add_edge(0, 1)
        graph.add_edge(0, 2)
        graph.add_edge(0, 3)
        # No edges between 1, 2, 3
        
        graph.fast_xor_update(0)
        
        # After τ_0: all edges between neighbors added
        assert graph.has_edge(1, 2)
        assert graph.has_edge(1, 3)
        assert graph.has_edge(2, 3)
    
    def test_loss_mask(self):
        """Test loss mask application."""
        graph = StabilizerGraph(100)
        
        # Add some edges
        for i in range(99):
            graph.add_edge(i, i + 1)
        
        # Apply 50% loss
        lost = graph.apply_loss_mask(0.5, seed=42)
        
        # Should lose approximately half
        assert 30 < len(lost) < 70
        assert len(graph.lost_nodes) == len(lost)
        
        # Check node states
        for i in lost:
            assert graph.node_states[i] == 0
            assert i in graph.lost_nodes
    
    def test_recovery(self):
        """Test recovery from loss."""
        graph = StabilizerGraph(10)
        for i in range(9):
            graph.add_edge(i, i + 1)
        
        # Apply loss
        graph.apply_loss_mask(0.3, seed=42)
        
        # Recover
        n_recoveries = graph.recover_from_loss()
        
        assert n_recoveries == len(graph.lost_nodes)
    
    def test_active_subgraph(self):
        """Test active subgraph extraction."""
        graph = StabilizerGraph(10)
        for i in range(9):
            graph.add_edge(i, i + 1)
        
        # Manually mark some as lost
        graph.node_states[3] = 0
        graph.node_states[7] = 0
        graph.lost_nodes = {3, 7}
        
        subgraph = graph.get_active_subgraph()
        
        assert subgraph.n_qubits == 8
    
    def test_copy(self):
        """Test graph copying."""
        graph = StabilizerGraph(5)
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        
        copy = graph.copy()
        
        assert copy.n_qubits == graph.n_qubits
        assert copy.get_edge_count() == graph.get_edge_count()
        
        # Modifying copy shouldn't affect original
        copy.add_edge(2, 3)
        assert not graph.has_edge(2, 3)


class TestTensorSlicer:
    """Tests for TensorSlicer class."""
    
    def test_creation(self):
        """Test slicer creation."""
        slicer = TensorSlicer(ram_limit_gb=4.0, n_workers=2)
        
        assert slicer.ram_limit_bytes == 4 * 1024 ** 3
        assert slicer.n_workers == 2
    
    def test_memory_estimation(self):
        """Test memory estimation."""
        slicer = TensorSlicer()
        
        tensors = [
            np.random.randn(10, 10).astype(np.complex128),
            np.random.randn(10, 10).astype(np.complex128)
        ]
        
        mem = slicer.estimate_memory(tensors)
        
        # Should be at least the size of input tensors
        assert mem >= sum(t.nbytes for t in tensors)
    
    def test_direct_contraction(self):
        """Test direct tensor contraction."""
        slicer = TensorSlicer()
        
        # Simple contraction: matrix multiplication
        A = np.random.randn(3, 4).astype(np.complex128)
        B = np.random.randn(4, 5).astype(np.complex128)
        
        result = slicer.contract_directly([A, B], "ij,jk->ik")
        expected = A @ B
        
        np.testing.assert_allclose(result, expected, rtol=1e-10)
    
    def test_tensor_network_creation(self):
        """Test TensorNetwork creation."""
        tensors = [np.random.randn(2, 2) for _ in range(3)]
        edges = [(0, 1, 2), (1, 2, 2)]
        labels = [['a', 'b'], ['b', 'c'], ['c', 'd']]
        
        tn = TensorNetwork(tensors=tensors, edges=edges, index_labels=labels)
        
        assert tn.n_tensors == 3
    
    def test_projection(self):
        """Test tensor projection (slicing)."""
        slicer = TensorSlicer()
        
        tensor = np.random.randn(2, 3, 4)
        tn = TensorNetwork(
            tensors=[tensor],
            edges=[],
            index_labels=[['a', 'b', 'c']]
        )
        
        projected = slicer.project(tn, 0, 1, 0)
        
        # After projecting index 1 to value 0
        assert projected.tensors[0].shape == (2, 4)
        np.testing.assert_array_equal(projected.tensors[0], tensor[:, 0, :])


class TestLossRecovery:
    """Tests for LossRecovery class."""
    
    def test_creation(self):
        """Test recovery module creation."""
        recovery = LossRecovery(p_gate=0.01, p_detection=0.05)
        
        assert recovery.p_gate == 0.01
        assert recovery.p_detection == 0.05
    
    def test_fidelity_estimation(self):
        """Test fidelity estimation."""
        recovery = LossRecovery(p_gate=0.01)
        
        # No operations: fidelity should be close to 1
        recovery.n_gates = 0
        fidelity = recovery.estimate_fidelity()
        assert fidelity > 0.9
        
        # Many gates: fidelity decreases
        recovery.n_gates = 100
        fidelity = recovery.estimate_fidelity()
        assert fidelity < 0.5
    
    def test_log_weighting(self):
        """Test log probability weighting."""
        recovery = LossRecovery()
        
        amplitudes = np.array([0.5, 0.5, 0.5, 0.5])
        loss_probs = np.array([0.1, 0.1, 0.1, 0.1])
        
        log_probs, normalized = recovery.apply_log_weighting(amplitudes, loss_probs)
        
        # Check normalization
        norm = np.sum(np.abs(normalized) ** 2)
        np.testing.assert_almost_equal(norm, 1.0, decimal=5)
    
    def test_error_mitigation(self):
        """Test full error mitigation pipeline."""
        recovery = LossRecovery(p_gate=0.01)
        
        raw_result = 0.9 + 0.1j
        result = recovery.mitigate_errors(raw_result, n_qubits=10, loss_rate=0.05)
        
        assert result.fidelity > 0
        assert result.fidelity <= 1
        assert result.n_corrections > 0
    
    def test_zero_noise_extrapolation(self):
        """Test zero-noise extrapolation."""
        recovery = LossRecovery()
        
        # Simulated results at different noise levels
        results = [
            (0.1, 0.9 + 0.0j),
            (0.2, 0.8 + 0.0j),
            (0.3, 0.7 + 0.0j)
        ]
        
        zero_noise = recovery.zero_noise_extrapolation(results)
        
        # Should extrapolate to approximately 1.0
        assert abs(zero_noise.real - 1.0) < 0.1


class TestIntegration:
    """Integration tests for LAGC components."""
    
    def test_graph_to_tensor_network(self):
        """Test full pipeline: graph -> tensor network -> contraction."""
        from lagc.simulation.contraction import TensorContractor
        from lagc.models.topologies import TopologyGenerator
        
        gen = TopologyGenerator()
        graph = gen.create_2d_cluster_state(3, 3)
        
        contractor = TensorContractor()
        tn = contractor.graph_to_tensor_network(graph)
        
        assert tn.n_tensors == 9
        
        result = contractor.contract(tn)
        
        # Result should be valid
        assert result.amplitude is not None
    
    def test_loss_and_recovery_pipeline(self):
        """Test loss application and recovery."""
        from lagc.models.topologies import TopologyGenerator
        
        gen = TopologyGenerator(seed=42)
        graph = gen.create_2d_cluster_state(5, 5)
        
        initial_edges = graph.get_edge_count()
        
        # Apply loss
        graph.apply_loss_mask(0.2, seed=42)
        
        # Recover
        graph.recover_from_loss()
        
        # Should have fewer edges after recovery (lost nodes removed)
        final_edges = graph.get_edge_count()
        assert final_edges <= initial_edges


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
