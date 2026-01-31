"""
LAGC Utils Module
=================

Utility functions for memory management and visualization.
"""

from .memory import MemoryManager, get_available_memory, get_memory_stats

# Visualization is optional (requires matplotlib)
try:
    from .visualization import GraphVisualizer, plot_lattice, plot_fidelity
    _HAS_VIZ = True
except ImportError:
    _HAS_VIZ = False
    GraphVisualizer = None
    plot_lattice = None
    plot_fidelity = None

__all__ = [
    "MemoryManager",
    "get_available_memory",
    "get_memory_stats",
]

# Add visualization if available
if _HAS_VIZ:
    __all__.extend(["GraphVisualizer", "plot_lattice", "plot_fidelity"])
