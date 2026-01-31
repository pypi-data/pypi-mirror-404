"""
LAGC Example: Basic Usage
==========================

Demonstrates the basic workflow of LAGC for quantum photonics simulation.
"""

from lagc import LAGC
import numpy as np


def example_basic():
    """Basic simulation example."""
    print("=" * 60)
    print("LAGC Basic Example: 2D Cluster State Simulation")
    print("=" * 60)
    
    # Create simulator with 8GB RAM limit
    sim = LAGC(ram_limit_gb=8.0, hardware='realistic')
    
    # Create a 10x10 2D cluster state
    sim.create_lattice('2d_cluster', 10, 10)
    
    print(f"\nLattice created:")
    print(f"  - Qubits: {sim.n_qubits}")
    print(f"  - Edges: {sim.graph.get_edge_count()}")
    
    # Apply 5% photon loss
    sim.apply_loss(p_loss=0.05, seed=42)
    
    info = sim.get_state_info()
    print(f"\nAfter loss:")
    print(f"  - Active qubits: {info['n_active']}")
    print(f"  - Lost qubits: {info['n_lost']}")
    
    # Run simulation
    result = sim.run_simulation()
    
    print(f"\nSimulation Results:")
    print(f"  - Fidelity: {result.fidelity:.4f}")
    print(f"  - Execution time: {result.execution_time:.2f}s")
    print(f"  - Peak memory: {result.memory_peak_gb:.2f} GB")
    
    return result


def example_3d_rhg():
    """3D RHG lattice simulation for fault-tolerant quantum computing."""
    print("\n" + "=" * 60)
    print("LAGC 3D RHG Example: Fault-Tolerant Lattice")
    print("=" * 60)
    
    sim = LAGC(ram_limit_gb=8.0, hardware='realistic', seed=123)
    
    # Create 5x5x5 RHG lattice
    sim.create_lattice('3d_rhg', 5, 5, 5)
    
    print(f"\n3D RHG Lattice created:")
    print(f"  - Qubits: {sim.n_qubits}")
    print(f"  - Edges: {sim.graph.get_edge_count()}")
    
    # Scan different loss rates
    print("\nScanning loss rates...")
    loss_rates = [0.01, 0.03, 0.05, 0.07, 0.10]
    
    for p_loss in loss_rates:
        sim.reset()
        sim.create_lattice('3d_rhg', 5, 5, 5)
        sim.apply_loss(p_loss)
        result = sim.run_simulation()
        
        print(f"  p_loss={p_loss:.2f}: fidelity={result.fidelity:.4f}, "
              f"active={result.n_active}/{result.n_qubits}")
    
    return result


def example_hardware_comparison():
    """Compare different hardware models."""
    print("\n" + "=" * 60)
    print("LAGC Hardware Comparison")
    print("=" * 60)
    
    from lagc.models.hardware import HardwareModel
    
    hardware_models = ['ideal', 'realistic', 'near_term', 'experimental']
    
    for hw_name in hardware_models:
        sim = LAGC(hardware=hw_name, seed=42)
        sim.create_lattice('2d_cluster', 8, 8)
        sim.apply_loss(p_loss=0.05)
        result = sim.run_simulation()
        
        print(f"\n{hw_name.upper()} hardware:")
        print(f"  - Fidelity: {result.fidelity:.4f}")
        print(f"  - Active qubits: {result.n_active}/{result.n_qubits}")


def example_loss_threshold():
    """Find loss threshold for a topology."""
    print("\n" + "=" * 60)
    print("LAGC Loss Threshold Analysis")
    print("=" * 60)
    
    sim = LAGC(hardware='ideal', seed=42)
    
    # Scan loss rates
    results = sim.scan_loss_rates(
        loss_rates=[0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
        topology='2d_cluster',
        dims=(8, 8),
        n_samples=3
    )
    
    print("\nLoss Rate vs Fidelity:")
    for p, f in zip(results['loss_rates'], results['fidelities']):
        bar = '#' * int(f * 40)
        print(f"  {p:.2f}: {f:.4f} |{bar}")
    
    # Find threshold (50% fidelity)
    threshold_idx = None
    for i, f in enumerate(results['fidelities']):
        if f < 0.5:
            threshold_idx = i
            break
    
    if threshold_idx:
        threshold = results['loss_rates'][threshold_idx]
        print(f"\nApproximate 50% threshold: p_loss ≈ {threshold:.2f}")
    
    return results


def example_large_scale():
    """Large-scale simulation demonstration."""
    print("\n" + "=" * 60)
    print("LAGC Large-Scale Simulation")
    print("=" * 60)
    
    # Note: This might need slicing for large lattices
    sim = LAGC(ram_limit_gb=4.0, hardware='realistic')
    
    # Start with moderate size
    sizes = [(10, 10), (20, 20), (30, 30)]
    
    for rows, cols in sizes:
        sim.reset()
        sim.create_lattice('2d_cluster', rows, cols)
        
        n_qubits = rows * cols
        print(f"\n{rows}x{cols} lattice ({n_qubits} qubits):")
        
        sim.apply_loss(p_loss=0.05)
        result = sim.run_simulation()
        
        print(f"  - Fidelity: {result.fidelity:.4f}")
        print(f"  - Time: {result.execution_time:.2f}s")
        print(f"  - Memory: {result.memory_peak_gb:.2f} GB")


def main():
    """Run all examples."""
    print("\n" + "#" * 60)
    print("#  LAGC: LossAware-GraphCompiler Examples")
    print("#  Quantum Photonics Simulation Library")
    print("#" * 60 + "\n")
    
    # Run examples
    example_basic()
    example_3d_rhg()
    example_hardware_comparison()
    example_loss_threshold()
    # example_large_scale()  # Uncomment for larger simulations
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
