"""
LAGC Command Line Interface
===========================

Simple CLI for running LAGC simulations from the terminal.

Usage:
    lagc --help
    lagc simulate --topology 2d_cluster --size 5 5 --loss 0.05
    lagc info
"""

import argparse
import sys
from typing import List, Optional


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="lagc",
        description="LAGC: LossAware-GraphCompiler for Photonic Quantum Computing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  lagc info                                    # Show library info
  lagc simulate --topology 2d_cluster --size 4 4 --loss 0.05
  lagc simulate --topology 3d_rhg --size 3 3 3 --hardware realistic
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show LAGC information")
    
    # Simulate command
    sim_parser = subparsers.add_parser("simulate", help="Run a simulation")
    sim_parser.add_argument(
        "--topology", "-t",
        type=str,
        default="2d_cluster",
        choices=["3d_rhg", "2d_cluster", "linear", "ghz", "ring", "complete"],
        help="Lattice topology (default: 2d_cluster)"
    )
    sim_parser.add_argument(
        "--size", "-s",
        type=int,
        nargs="+",
        default=[4, 4],
        help="Lattice dimensions (default: 4 4)"
    )
    sim_parser.add_argument(
        "--loss", "-l",
        type=float,
        default=0.05,
        help="Loss probability (default: 0.05)"
    )
    sim_parser.add_argument(
        "--hardware", "-hw",
        type=str,
        default="realistic",
        choices=["ideal", "realistic", "near_term", "experimental", "future"],
        help="Hardware model (default: realistic)"
    )
    sim_parser.add_argument(
        "--ram",
        type=float,
        default=8.0,
        help="RAM limit in GB (default: 8.0)"
    )
    sim_parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    
    # Version command
    parser.add_argument(
        "--version", "-V",
        action="store_true",
        help="Show version"
    )
    
    parsed_args = parser.parse_args(args)
    
    if parsed_args.version:
        from lagc import __version__
        print(f"LAGC v{__version__}")
        return 0
    
    if parsed_args.command == "info":
        from lagc import info
        info()
        return 0
    
    elif parsed_args.command == "simulate":
        return run_simulation(parsed_args)
    
    else:
        parser.print_help()
        return 0


def run_simulation(args) -> int:
    """Run simulation with CLI arguments."""
    from lagc import LAGC
    
    print("=" * 60)
    print("LAGC Simulation")
    print("=" * 60)
    
    # Create simulator
    sim = LAGC(
        ram_limit_gb=args.ram,
        hardware=args.hardware,
        seed=args.seed
    )
    
    # Create lattice
    print(f"\n📐 Topology: {args.topology}")
    print(f"   Size: {args.size}")
    sim.create_lattice(args.topology, *args.size)
    print(f"   Qubits: {sim.n_qubits}")
    print(f"   Edges: {sim.graph.get_edge_count()}")
    
    # Apply loss
    print(f"\n⚡ Applying {args.loss*100:.1f}% loss...")
    sim.apply_loss(p_loss=args.loss)
    info = sim.graph.get_graph_info()
    print(f"   Lost: {info['n_lost']} qubits")
    print(f"   Active: {info['n_active']} qubits")
    
    # Run simulation
    print(f"\n🔬 Running simulation (Hardware: {args.hardware})...")
    result = sim.run_simulation()
    
    # Results
    print(f"\n📊 Results:")
    print(f"   Fidelity: {result.fidelity:.4f}")
    print(f"   Time: {result.execution_time:.2f}s")
    print(f"   Memory: {result.memory_peak_gb:.2f} GB")
    
    print("\n" + "=" * 60)
    print("✅ Simulation complete!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
