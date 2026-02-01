"""
Depth-First Search (DFS) Algorithm
==================================

DFS explores a graph by going as deep as possible before backtracking.
Useful for cycle detection, topological sorting, and finding connected components.

Time Complexity: O(V + E)
Space Complexity: O(V)
"""

from typing import Dict, List, Optional, Set, Union, Tuple
import networkx as nx


def dfs(
    graph: Union[nx.Graph, nx.DiGraph],
    source: Union[int, str],
    mode: str = 'recursive'
) -> List[Union[int, str]]:
    """
    Perform Depth-First Search from source vertex.
    
    Returns the order in which vertices are visited.

    Args:
        graph: NetworkX Graph or DiGraph
        source: Starting vertex
        mode: 'recursive' or 'iterative' (default: 'recursive')

    Returns:
        List of vertices in DFS visit order

    Raises:
        ValueError: If source vertex not in graph or invalid mode

    Time Complexity:
        O(V + E) where V = vertices, E = edges

    Example:
        >>> import networkx as nx
        >>> from logarithma.algorithms.traversal import dfs
        >>>
        >>> G = nx.Graph()
        >>> G.add_edges_from([('A', 'B'), ('B', 'C'), ('A', 'D')])
        >>>
        >>> visited = dfs(G, 'A')
        >>> print(visited)
        ['A', 'B', 'C', 'D']  # Order may vary
    """
    # Validate input
    if not graph:
        raise ValueError("Graph is empty")
    
    if source not in graph:
        raise ValueError(f"Source vertex '{source}' not found in graph")
    
    if mode not in ['recursive', 'iterative']:
        raise ValueError(f"Invalid mode '{mode}'. Use 'recursive' or 'iterative'")
    
    if mode == 'recursive':
        return _dfs_recursive(graph, source)
    else:
        return _dfs_iterative(graph, source)


def _dfs_recursive(
    graph: Union[nx.Graph, nx.DiGraph],
    source: Union[int, str]
) -> List[Union[int, str]]:
    """Recursive DFS implementation"""
    visited = []
    visited_set = set()
    
    def dfs_visit(node):
        visited_set.add(node)
        visited.append(node)
        
        for neighbor in graph.neighbors(node):
            if neighbor not in visited_set:
                dfs_visit(neighbor)
    
    dfs_visit(source)
    return visited


def _dfs_iterative(
    graph: Union[nx.Graph, nx.DiGraph],
    source: Union[int, str]
) -> List[Union[int, str]]:
    """Iterative DFS implementation using stack"""
    visited = []
    visited_set = set()
    stack = [source]
    
    while stack:
        node = stack.pop()
        
        if node not in visited_set:
            visited_set.add(node)
            visited.append(node)
            
            # Add neighbors to stack (reverse order for consistent traversal)
            neighbors = list(graph.neighbors(node))
            for neighbor in reversed(neighbors):
                if neighbor not in visited_set:
                    stack.append(neighbor)
    
    return visited


def dfs_path(
    graph: Union[nx.Graph, nx.DiGraph],
    source: Union[int, str],
    target: Union[int, str]
) -> Optional[List[Union[int, str]]]:
    """
    Find a path from source to target using DFS.
    
    Note: DFS does not guarantee the shortest path. Use BFS for shortest paths.

    Args:
        graph: NetworkX Graph or DiGraph
        source: Starting vertex
        target: Target vertex

    Returns:
        List of vertices representing a path from source to target,
        or None if no path exists

    Raises:
        ValueError: If source or target vertex not in graph

    Time Complexity:
        O(V + E)

    Example:
        >>> path = dfs_path(G, 'A', 'C')
        >>> print(path)
        ['A', 'B', 'C']  # One possible path
    """
    # Validate input
    if not graph:
        raise ValueError("Graph is empty")
    
    if source not in graph:
        raise ValueError(f"Source vertex '{source}' not found in graph")
    
    if target not in graph:
        raise ValueError(f"Target vertex '{target}' not found in graph")
    
    # DFS with path tracking
    visited = set()
    path = []
    
    def dfs_visit(node):
        visited.add(node)
        path.append(node)
        
        if node == target:
            return True
        
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                if dfs_visit(neighbor):
                    return True
        
        path.pop()
        return False
    
    if dfs_visit(source):
        return path
    else:
        return None


def detect_cycle(
    graph: Union[nx.Graph, nx.DiGraph]
) -> Tuple[bool, Optional[List]]:
    """
    Detect if graph contains a cycle using DFS.
    
    For directed graphs, detects directed cycles.
    For undirected graphs, detects any cycle.

    Args:
        graph: NetworkX Graph or DiGraph

    Returns:
        Tuple of (has_cycle: bool, cycle: Optional[List])
        If cycle exists, returns the cycle as a list of vertices

    Time Complexity:
        O(V + E)

    Example:
        >>> G = nx.DiGraph()
        >>> G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'A')])
        >>> has_cycle, cycle = detect_cycle(G)
        >>> print(has_cycle)  # True
        >>> print(cycle)      # ['A', 'B', 'C', 'A']
    """
    if not graph:
        return False, None
    
    is_directed = isinstance(graph, nx.DiGraph)
    visited = set()
    rec_stack = set()  # For directed graphs
    parent = {}  # For undirected graphs
    
    def dfs_visit(node, par=None):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                parent[neighbor] = node
                cycle = dfs_visit(neighbor, node)
                if cycle:
                    return cycle
            elif is_directed:
                # Directed graph: back edge means cycle
                if neighbor in rec_stack:
                    # Found cycle
                    cycle = [neighbor]
                    current = node
                    while current != neighbor:
                        cycle.append(current)
                        current = parent.get(current)
                    cycle.append(neighbor)
                    return cycle[::-1]
            else:
                # Undirected graph: back edge (not to parent) means cycle
                if neighbor != par:
                    # Found cycle
                    cycle = [neighbor]
                    current = node
                    while current != neighbor:
                        cycle.append(current)
                        current = parent.get(current)
                    cycle.append(neighbor)
                    return cycle[::-1]
        
        rec_stack.remove(node)
        return None
    
    # Try DFS from each unvisited node
    for node in graph.nodes():
        if node not in visited:
            parent[node] = None
            cycle = dfs_visit(node)
            if cycle:
                return True, cycle
    
    return False, None
