"""
Visualization Utilities
========================

Graph state and simulation result visualization.
"""

from __future__ import annotations

import numpy as np
from typing import Optional, List, Tuple, Dict, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from lagc.core.graph_engine import StabilizerGraph

logger = logging.getLogger(__name__)

# Try to import matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from mpl_toolkits.mplot3d import Axes3D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None
    logger.warning("matplotlib not available, visualization disabled")

# Try to import networkx
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None


class GraphVisualizer:
    """
    Visualizer for graph states and simulation results.
    
    Creates plots of graph structures, loss patterns,
    and fidelity trends.
    
    Example:
        >>> vis = GraphVisualizer()
        >>> vis.plot_graph(graph)
        >>> vis.save("graph_state.png")
    """
    
    def __init__(self, figsize: Tuple[int, int] = (10, 8)):
        """
        Initialize visualizer.
        
        Args:
            figsize: Default figure size
        """
        if not HAS_MATPLOTLIB:
            logger.warning("Visualization requires matplotlib")
        
        self.figsize = figsize
        self._fig = None
        self._ax = None
    
    def plot_graph(
        self,
        graph: 'StabilizerGraph',
        layout: str = 'spring',
        show_lost: bool = True,
        title: Optional[str] = None
    ) -> Optional[Any]:
        """
        Plot graph state structure.
        
        Args:
            graph: StabilizerGraph to visualize
            layout: Layout algorithm ('spring', 'circular', 'grid')
            show_lost: Whether to show lost nodes
            title: Optional plot title
            
        Returns:
            matplotlib figure or None if not available
        """
        if not HAS_MATPLOTLIB or not HAS_NETWORKX:
            logger.warning("Requires matplotlib and networkx")
            return None
        
        # Convert to networkx graph
        G = self._to_networkx(graph)
        
        # Create figure
        self._fig, self._ax = plt.subplots(figsize=self.figsize)
        
        # Choose layout
        if layout == 'spring':
            pos = nx.spring_layout(G, seed=42)
        elif layout == 'circular':
            pos = nx.circular_layout(G)
        elif layout == 'grid':
            n = int(np.sqrt(graph.n_qubits)) + 1
            pos = {i: (i % n, i // n) for i in range(graph.n_qubits)}
        else:
            pos = nx.spring_layout(G, seed=42)
        
        # Color nodes by status
        colors = []
        for i in range(graph.n_qubits):
            if i in graph.lost_nodes:
                colors.append('red')
            else:
                colors.append('lightblue')
        
        # Draw
        nx.draw(
            G, pos,
            ax=self._ax,
            node_color=colors,
            node_size=300,
            edge_color='gray',
            alpha=0.8,
            with_labels=True,
            font_size=8
        )
        
        # Legend
        active_patch = mpatches.Patch(color='lightblue', label='Active')
        lost_patch = mpatches.Patch(color='red', label='Lost')
        self._ax.legend(handles=[active_patch, lost_patch])
        
        if title:
            self._ax.set_title(title)
        else:
            info = graph.get_graph_info()
            self._ax.set_title(
                f"Graph State: {info['n_qubits']} qubits, "
                f"{info['n_edges']} edges, {info['n_lost']} lost"
            )
        
        plt.tight_layout()
        return self._fig
    
    def plot_3d_lattice(
        self,
        graph: 'StabilizerGraph',
        dims: Tuple[int, int, int],
        title: Optional[str] = None
    ) -> Optional[Any]:
        """
        Plot 3D lattice structure.
        
        Args:
            graph: StabilizerGraph (3D RHG or similar)
            dims: Lattice dimensions (lx, ly, lz)
            title: Optional plot title
            
        Returns:
            matplotlib figure or None
        """
        if not HAS_MATPLOTLIB:
            return None
        
        lx, ly, lz = dims
        
        self._fig = plt.figure(figsize=self.figsize)
        self._ax = self._fig.add_subplot(111, projection='3d')
        
        # Generate node positions
        positions = []
        colors = []
        
        for i in range(graph.n_qubits):
            # Approximate position based on index
            x = i % lx
            y = (i // lx) % ly
            z = i // (lx * ly)
            positions.append((x, y, z))
            
            if i in graph.lost_nodes:
                colors.append('red')
            else:
                colors.append('blue')
        
        positions = np.array(positions)
        
        # Plot nodes
        self._ax.scatter(
            positions[:, 0],
            positions[:, 1],
            positions[:, 2],
            c=colors,
            s=50,
            alpha=0.6
        )
        
        # Plot edges (subset for visibility)
        if not graph._finalized:
            graph._finalize()
        
        edges_plotted = 0
        max_edges = 500  # Limit for visibility
        
        for i in range(min(graph.n_qubits, 100)):
            neighbors = graph.get_neighbors(i)
            for j in neighbors:
                if j > i and edges_plotted < max_edges:
                    self._ax.plot(
                        [positions[i, 0], positions[j, 0]],
                        [positions[i, 1], positions[j, 1]],
                        [positions[i, 2], positions[j, 2]],
                        'gray', alpha=0.3, linewidth=0.5
                    )
                    edges_plotted += 1
        
        self._ax.set_xlabel('X')
        self._ax.set_ylabel('Y')
        self._ax.set_zlabel('Z')
        
        if title:
            self._ax.set_title(title)
        else:
            self._ax.set_title(f"3D Lattice: {lx}×{ly}×{lz}")
        
        return self._fig
    
    def plot_fidelity_vs_loss(
        self,
        loss_rates: List[float],
        fidelities: List[float],
        title: str = "Fidelity vs Loss Rate"
    ) -> Optional[Any]:
        """
        Plot fidelity as function of loss rate.
        
        Args:
            loss_rates: List of loss probabilities
            fidelities: Corresponding fidelities
            title: Plot title
            
        Returns:
            matplotlib figure or None
        """
        if not HAS_MATPLOTLIB:
            return None
        
        self._fig, self._ax = plt.subplots(figsize=self.figsize)
        
        self._ax.plot(loss_rates, fidelities, 'bo-', linewidth=2, markersize=8)
        self._ax.set_xlabel('Loss Rate')
        self._ax.set_ylabel('Fidelity')
        self._ax.set_title(title)
        self._ax.grid(True, alpha=0.3)
        self._ax.set_xlim(0, max(loss_rates) * 1.1)
        self._ax.set_ylim(0, 1.05)
        
        # Add threshold line
        self._ax.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='50% threshold')
        self._ax.legend()
        
        plt.tight_layout()
        return self._fig
    
    def plot_memory_usage(
        self,
        steps: List[int],
        memory_gb: List[float],
        limit_gb: Optional[float] = None,
        title: str = "Memory Usage"
    ) -> Optional[Any]:
        """
        Plot memory usage over simulation steps.
        
        Args:
            steps: Step numbers
            memory_gb: Memory usage in GB
            limit_gb: Optional memory limit line
            title: Plot title
            
        Returns:
            matplotlib figure or None
        """
        if not HAS_MATPLOTLIB:
            return None
        
        self._fig, self._ax = plt.subplots(figsize=self.figsize)
        
        self._ax.fill_between(steps, memory_gb, alpha=0.3)
        self._ax.plot(steps, memory_gb, 'b-', linewidth=2)
        
        if limit_gb is not None:
            self._ax.axhline(
                y=limit_gb, color='r', linestyle='--',
                label=f'Limit: {limit_gb:.1f} GB'
            )
            self._ax.legend()
        
        self._ax.set_xlabel('Step')
        self._ax.set_ylabel('Memory (GB)')
        self._ax.set_title(title)
        self._ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig
    
    def _to_networkx(self, graph: 'StabilizerGraph') -> Any:
        """Convert StabilizerGraph to networkx graph."""
        if not HAS_NETWORKX:
            raise ImportError("networkx required for graph conversion")
        
        G = nx.Graph()
        G.add_nodes_from(range(graph.n_qubits))
        
        if not graph._finalized:
            graph._finalize()
        
        # Add edges
        adj = graph._adj_csr
        rows, cols = adj.nonzero()
        for i, j in zip(rows, cols):
            if i < j:  # Add each edge once
                G.add_edge(i, j)
        
        return G
    
    def save(self, path: str, dpi: int = 150) -> bool:
        """
        Save current figure to file.
        
        Args:
            path: Output file path
            dpi: Resolution
            
        Returns:
            True if successful
        """
        if self._fig is None:
            logger.warning("No figure to save")
            return False
        
        try:
            self._fig.savefig(path, dpi=dpi, bbox_inches='tight')
            logger.info(f"Figure saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save figure: {e}")
            return False
    
    def show(self) -> None:
        """Display current figure."""
        if HAS_MATPLOTLIB and self._fig is not None:
            plt.show()
    
    def close(self) -> None:
        """Close current figure."""
        if HAS_MATPLOTLIB and self._fig is not None:
            plt.close(self._fig)
            self._fig = None
            self._ax = None


# Convenience functions
def plot_lattice(
    graph: 'StabilizerGraph',
    dims: Optional[Tuple[int, int, int]] = None,
    save_path: Optional[str] = None
) -> Optional[Any]:
    """
    Quick plot of lattice structure.
    
    Args:
        graph: Graph to plot
        dims: Optional 3D dimensions
        save_path: Optional path to save plot
        
    Returns:
        matplotlib figure or None
    """
    vis = GraphVisualizer()
    
    if dims is not None:
        fig = vis.plot_3d_lattice(graph, dims)
    else:
        fig = vis.plot_graph(graph)
    
    if save_path:
        vis.save(save_path)
    
    return fig


def plot_fidelity(
    loss_rates: List[float],
    fidelities: List[float],
    save_path: Optional[str] = None
) -> Optional[Any]:
    """
    Quick fidelity plot.
    
    Args:
        loss_rates: Loss rate values
        fidelities: Corresponding fidelities
        save_path: Optional path to save plot
        
    Returns:
        matplotlib figure or None
    """
    vis = GraphVisualizer()
    fig = vis.plot_fidelity_vs_loss(loss_rates, fidelities)
    
    if save_path:
        vis.save(save_path)
    
    return fig
