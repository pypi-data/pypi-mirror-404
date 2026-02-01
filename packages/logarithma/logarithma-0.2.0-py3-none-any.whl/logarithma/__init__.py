
"""
LOGARITHMA - Graph Algorithms Library
=====================================

High-performance graph algorithms library featuring advanced shortest path algorithms.

Quick Start:
    >>> import logarithma as lg
    >>> import networkx as nx
    >>>
    >>> # Create a simple graph
    >>> G = nx.Graph()
    >>> G.add_edge('A', 'B', weight=4)
    >>> G.add_edge('A', 'C', weight=2)
    >>>
    >>> # Find shortest paths
    >>> distances = lg.dijkstra(G, 'A')
    >>> print(distances)
"""
__version__ = "0.2.0"
__author__ = "Can AKYILDIRIM"

# Import main algorithms for easy access
from .algorithms import dijkstra, dijkstra_with_path
from .algorithms.traversal import bfs, bfs_path, dfs, dfs_path, detect_cycle

# Package metadata
__all__ = [
    # Shortest Path
    'dijkstra',
    'dijkstra_with_path',
    # Traversal
    'bfs',
    'bfs_path',
    'dfs',
    'dfs_path',
    'detect_cycle',
    # Metadata
    '__version__',
    '__author__'
]