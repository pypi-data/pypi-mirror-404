"""
Graph Generators
===============

Functions to generate various types of graphs for testing and benchmarking.
"""

import random
from typing import Union, Optional, List, Tuple
import networkx as nx


def generate_random_graph(
    n: int,
    edge_probability: float = 0.1,
    weighted: bool = True,
    directed: bool = False,
    weight_range: Tuple[float, float] = (1, 10),
    seed: Optional[int] = None
) -> Union[nx.Graph, nx.DiGraph]:
    """
    Generate a random graph using Erdős-Rényi model.
    
    Args:
        n: Number of vertices
        edge_probability: Probability of edge creation (0 to 1)
        weighted: Whether to add random weights to edges
        directed: Whether to create directed graph
        weight_range: Tuple of (min_weight, max_weight)
        seed: Random seed for reproducibility
    
    Returns:
        NetworkX Graph or DiGraph
    
    Example:
        >>> from logarithma.utils import generate_random_graph
        >>> G = generate_random_graph(100, edge_probability=0.05)
        >>> print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    """
    if seed is not None:
        random.seed(seed)
    
    # Create base graph
    if directed:
        G = nx.erdos_renyi_graph(n, edge_probability, seed=seed, directed=True)
    else:
        G = nx.erdos_renyi_graph(n, edge_probability, seed=seed)
    
    # Add weights if requested
    if weighted:
        for u, v in G.edges():
            weight = random.uniform(weight_range[0], weight_range[1])
            G[u][v]['weight'] = round(weight, 2)
    
    return G


def generate_grid_graph(
    rows: int,
    cols: int,
    weighted: bool = True,
    diagonal: bool = False,
    weight_range: Tuple[float, float] = (1, 10),
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a 2D grid graph.
    
    Useful for pathfinding algorithms and spatial problems.
    
    Args:
        rows: Number of rows
        cols: Number of columns
        weighted: Whether to add random weights
        diagonal: Whether to include diagonal connections
        weight_range: Tuple of (min_weight, max_weight)
        seed: Random seed for reproducibility
    
    Returns:
        NetworkX Graph
    
    Example:
        >>> G = generate_grid_graph(10, 10, diagonal=True)
        >>> # Perfect for A* pathfinding tests
    """
    if seed is not None:
        random.seed(seed)
    
    # Create grid graph
    G = nx.grid_2d_graph(rows, cols)
    
    # Add diagonal edges if requested
    if diagonal:
        for i in range(rows):
            for j in range(cols):
                # Add diagonal neighbors
                for di, dj in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols:
                        G.add_edge((i, j), (ni, nj))
    
    # Add weights if requested
    if weighted:
        for u, v in G.edges():
            weight = random.uniform(weight_range[0], weight_range[1])
            G[u][v]['weight'] = round(weight, 2)
    
    return G


def generate_complete_graph(
    n: int,
    weighted: bool = True,
    directed: bool = False,
    weight_range: Tuple[float, float] = (1, 10),
    seed: Optional[int] = None
) -> Union[nx.Graph, nx.DiGraph]:
    """
    Generate a complete graph where every pair of vertices is connected.
    
    Args:
        n: Number of vertices
        weighted: Whether to add random weights
        directed: Whether to create directed graph
        weight_range: Tuple of (min_weight, max_weight)
        seed: Random seed for reproducibility
    
    Returns:
        NetworkX Graph or DiGraph
    
    Example:
        >>> G = generate_complete_graph(10)
        >>> # Worst case for many algorithms: O(n²) edges
    """
    if seed is not None:
        random.seed(seed)
    
    # Create complete graph
    if directed:
        G = nx.complete_graph(n, create_using=nx.DiGraph())
    else:
        G = nx.complete_graph(n)
    
    # Add weights if requested
    if weighted:
        for u, v in G.edges():
            weight = random.uniform(weight_range[0], weight_range[1])
            G[u][v]['weight'] = round(weight, 2)
    
    return G


def generate_path_graph(
    n: int,
    weighted: bool = True,
    weight_range: Tuple[float, float] = (1, 10),
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a path graph (linear chain of vertices).
    
    Args:
        n: Number of vertices
        weighted: Whether to add random weights
        weight_range: Tuple of (min_weight, max_weight)
        seed: Random seed for reproducibility
    
    Returns:
        NetworkX Graph
    
    Example:
        >>> G = generate_path_graph(100)
        >>> # Simple case: only one path from start to end
    """
    if seed is not None:
        random.seed(seed)
    
    G = nx.path_graph(n)
    
    if weighted:
        for u, v in G.edges():
            weight = random.uniform(weight_range[0], weight_range[1])
            G[u][v]['weight'] = round(weight, 2)
    
    return G


def generate_cycle_graph(
    n: int,
    weighted: bool = True,
    weight_range: Tuple[float, float] = (1, 10),
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a cycle graph (circular chain of vertices).
    
    Args:
        n: Number of vertices
        weighted: Whether to add random weights
        weight_range: Tuple of (min_weight, max_weight)
        seed: Random seed for reproducibility
    
    Returns:
        NetworkX Graph
    
    Example:
        >>> G = generate_cycle_graph(10)
        >>> # Has cycle: useful for cycle detection tests
    """
    if seed is not None:
        random.seed(seed)
    
    G = nx.cycle_graph(n)
    
    if weighted:
        for u, v in G.edges():
            weight = random.uniform(weight_range[0], weight_range[1])
            G[u][v]['weight'] = round(weight, 2)
    
    return G


def generate_star_graph(
    n: int,
    weighted: bool = True,
    weight_range: Tuple[float, float] = (1, 10),
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a star graph (one central node connected to all others).
    
    Args:
        n: Number of outer vertices (total vertices = n + 1)
        weighted: Whether to add random weights
        weight_range: Tuple of (min_weight, max_weight)
        seed: Random seed for reproducibility
    
    Returns:
        NetworkX Graph
    
    Example:
        >>> G = generate_star_graph(10)
        >>> # Central hub topology
    """
    if seed is not None:
        random.seed(seed)
    
    G = nx.star_graph(n)
    
    if weighted:
        for u, v in G.edges():
            weight = random.uniform(weight_range[0], weight_range[1])
            G[u][v]['weight'] = round(weight, 2)
    
    return G


def generate_tree_graph(
    n: int,
    branching_factor: int = 2,
    weighted: bool = True,
    weight_range: Tuple[float, float] = (1, 10),
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a random tree graph.
    
    Args:
        n: Number of vertices
        branching_factor: Average number of children per node
        weighted: Whether to add random weights
        weight_range: Tuple of (min_weight, max_weight)
        seed: Random seed for reproducibility
    
    Returns:
        NetworkX Graph (tree structure)
    
    Example:
        >>> G = generate_tree_graph(100, branching_factor=3)
        >>> # Hierarchical structure, no cycles
    """
    if seed is not None:
        random.seed(seed)
    
    # Generate random tree
    G = nx.random_tree(n, seed=seed)
    
    if weighted:
        for u, v in G.edges():
            weight = random.uniform(weight_range[0], weight_range[1])
            G[u][v]['weight'] = round(weight, 2)
    
    return G


def generate_scale_free_graph(
    n: int,
    weighted: bool = True,
    weight_range: Tuple[float, float] = (1, 10),
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a scale-free graph using Barabási-Albert model.
    
    Scale-free graphs have power-law degree distribution,
    common in social networks and the internet.
    
    Args:
        n: Number of vertices
        weighted: Whether to add random weights
        weight_range: Tuple of (min_weight, max_weight)
        seed: Random seed for reproducibility
    
    Returns:
        NetworkX Graph
    
    Example:
        >>> G = generate_scale_free_graph(1000)
        >>> # Realistic network topology
    """
    if seed is not None:
        random.seed(seed)
    
    # m = number of edges to attach from new node
    m = max(1, int(n ** 0.5) // 10)
    G = nx.barabasi_albert_graph(n, m, seed=seed)
    
    if weighted:
        for u, v in G.edges():
            weight = random.uniform(weight_range[0], weight_range[1])
            G[u][v]['weight'] = round(weight, 2)
    
    return G


def generate_small_world_graph(
    n: int,
    k: int = 4,
    p: float = 0.1,
    weighted: bool = True,
    weight_range: Tuple[float, float] = (1, 10),
    seed: Optional[int] = None
) -> nx.Graph:
    """
    Generate a small-world graph using Watts-Strogatz model.
    
    Small-world graphs have high clustering and short path lengths,
    common in social networks.
    
    Args:
        n: Number of vertices
        k: Each node is connected to k nearest neighbors in ring topology
        p: Probability of rewiring each edge
        weighted: Whether to add random weights
        weight_range: Tuple of (min_weight, max_weight)
        seed: Random seed for reproducibility
    
    Returns:
        NetworkX Graph
    
    Example:
        >>> G = generate_small_world_graph(100, k=4, p=0.1)
        >>> # Six degrees of separation
    """
    if seed is not None:
        random.seed(seed)
    
    G = nx.watts_strogatz_graph(n, k, p, seed=seed)
    
    if weighted:
        for u, v in G.edges():
            weight = random.uniform(weight_range[0], weight_range[1])
            G[u][v]['weight'] = round(weight, 2)
    
    return G
