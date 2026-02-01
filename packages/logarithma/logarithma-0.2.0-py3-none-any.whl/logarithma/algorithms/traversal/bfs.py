"""
Breadth-First Search (BFS) Algorithm
====================================

BFS explores a graph level by level, visiting all neighbors
of a vertex before moving to the next level.

Time Complexity: O(V + E)
Space Complexity: O(V)
"""

from collections import deque
from typing import Dict, List, Optional, Set, Union
import networkx as nx


def bfs(
    graph: Union[nx.Graph, nx.DiGraph],
    source: Union[int, str]
) -> Dict[Union[int, str], int]:
    """
    Perform Breadth-First Search from source vertex.
    
    Returns the distance (number of edges) from source to all reachable vertices.
    Useful for finding shortest paths in unweighted graphs.

    Args:
        graph: NetworkX Graph or DiGraph (unweighted)
        source: Starting vertex

    Returns:
        Dictionary mapping each reachable vertex to its distance from source.
        Unreachable vertices are not included in the result.

    Raises:
        ValueError: If source vertex not in graph or graph is empty

    Time Complexity:
        O(V + E) where V = vertices, E = edges

    Example:
        >>> import networkx as nx
        >>> from logarithma.algorithms.traversal import bfs
        >>>
        >>> G = nx.Graph()
        >>> G.add_edges_from([('A', 'B'), ('B', 'C'), ('A', 'D')])
        >>>
        >>> distances = bfs(G, 'A')
        >>> print(distances)
        {'A': 0, 'B': 1, 'D': 1, 'C': 2}
    """
    # Validate input
    if not graph:
        raise ValueError("Graph is empty")
    
    if source not in graph:
        raise ValueError(f"Source vertex '{source}' not found in graph")
    
    # Initialize
    distances = {source: 0}
    queue = deque([source])
    
    # BFS traversal
    while queue:
        current = queue.popleft()
        current_dist = distances[current]
        
        # Visit all neighbors
        for neighbor in graph.neighbors(current):
            if neighbor not in distances:
                distances[neighbor] = current_dist + 1
                queue.append(neighbor)
    
    return distances


def bfs_path(
    graph: Union[nx.Graph, nx.DiGraph],
    source: Union[int, str],
    target: Optional[Union[int, str]] = None
) -> Dict[str, Union[Dict, List]]:
    """
    BFS with path reconstruction.
    
    Finds shortest paths (by number of edges) from source to target or all vertices.

    Args:
        graph: NetworkX Graph or DiGraph (unweighted)
        source: Starting vertex
        target: Optional target vertex. If specified, returns only path to target
                and may terminate early.

    Returns:
        Dictionary with two keys:
            - 'distances': Dict mapping vertices to distances
            - 'paths': Dict mapping vertices to shortest paths (list of vertices)
                      Empty list for unreachable vertices

    Raises:
        ValueError: If source or target vertex not in graph

    Time Complexity:
        O(V + E), may be faster with target specified

    Example:
        >>> result = bfs_path(G, 'A', 'C')
        >>> print(result['distances']['C'])  # Distance: 2
        >>> print(result['paths']['C'])      # Path: ['A', 'B', 'C']
    """
    # Validate input
    if not graph:
        raise ValueError("Graph is empty")
    
    if source not in graph:
        raise ValueError(f"Source vertex '{source}' not found in graph")
    
    if target and target not in graph:
        raise ValueError(f"Target vertex '{target}' not found in graph")
    
    # Initialize
    distances = {source: 0}
    previous = {source: None}
    queue = deque([source])
    
    # BFS traversal
    while queue:
        current = queue.popleft()
        
        # Early termination if target found
        if target and current == target:
            break
        
        # Visit all neighbors
        for neighbor in graph.neighbors(current):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                previous[neighbor] = current
                queue.append(neighbor)
    
    # Reconstruct paths
    def get_path(target_node):
        if target_node not in distances:
            return []
        
        path = []
        current = target_node
        while current is not None:
            path.append(current)
            current = previous[current]
        return path[::-1]
    
    # Build paths dictionary
    if target:
        paths = {target: get_path(target)}
    else:
        paths = {node: get_path(node) for node in distances.keys()}
    
    return {
        'distances': distances,
        'paths': paths
    }
