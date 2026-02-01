"""
Shortest Path Algorithms
========================

Collection of shortest path algorithms for graph analysis.

Available algorithms:
- dijkstra: Classic Dijkstra's algorithm
- dijkstra_with_path: Dijkstra with path reconstruction

Future algorithms:
- fast_sssp: O(m log^{2/3} n) algorithm
- bellman_ford: For graphs with negative weights
- floyd_warshall: All-pairs shortest paths
"""

from .dijkstra import dijkstra, dijkstra_with_path

__all__ = [
    'dijkstra',
    'dijkstra_with_path'
]