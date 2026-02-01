"""
Graph Format Converters
=======================

Convert between different graph representations.
"""

from typing import List, Tuple, Dict, Union, Any, Optional
import networkx as nx
import numpy as np


def from_adjacency_matrix(
    matrix: Union[List[List[float]], np.ndarray],
    directed: bool = False,
    node_labels: Optional[List] = None
) -> Union[nx.Graph, nx.DiGraph]:
    """
    Create graph from adjacency matrix.
    
    Args:
        matrix: 2D array where matrix[i][j] is weight of edge from i to j
                0 or None means no edge
        directed: Whether to create directed graph
        node_labels: Optional list of node labels (default: 0, 1, 2, ...)
    
    Returns:
        NetworkX Graph or DiGraph
    
    Example:
        >>> matrix = [
        ...     [0, 1, 2],
        ...     [1, 0, 3],
        ...     [2, 3, 0]
        ... ]
        >>> G = from_adjacency_matrix(matrix)
    """
    if isinstance(matrix, list):
        matrix = np.array(matrix)
    
    n = len(matrix)
    
    # Create graph
    if directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    
    # Add nodes
    if node_labels:
        G.add_nodes_from(node_labels[:n])
    else:
        G.add_nodes_from(range(n))
    
    # Add edges
    nodes = list(G.nodes())
    for i in range(n):
        for j in range(n):
            if matrix[i][j] != 0 and matrix[i][j] is not None:
                if not directed and i > j:
                    continue  # Skip duplicate edges in undirected graph
                G.add_edge(nodes[i], nodes[j], weight=float(matrix[i][j]))
    
    return G


def to_adjacency_matrix(
    graph: Union[nx.Graph, nx.DiGraph],
    weight_attr: str = 'weight',
    default_weight: float = 1.0
) -> np.ndarray:
    """
    Convert graph to adjacency matrix.
    
    Args:
        graph: NetworkX Graph or DiGraph
        weight_attr: Edge attribute to use as weight
        default_weight: Default weight for edges without weight attribute
    
    Returns:
        NumPy array of shape (n, n)
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edge(0, 1, weight=5)
        >>> G.add_edge(1, 2, weight=3)
        >>> matrix = to_adjacency_matrix(G)
    """
    return nx.to_numpy_array(graph, weight=weight_attr, nonedge=0)


def from_edge_list(
    edges: List[Tuple],
    directed: bool = False,
    weighted: bool = True
) -> Union[nx.Graph, nx.DiGraph]:
    """
    Create graph from edge list.
    
    Args:
        edges: List of tuples:
               - (u, v) for unweighted edges
               - (u, v, weight) for weighted edges
        directed: Whether to create directed graph
        weighted: Whether edges include weights
    
    Returns:
        NetworkX Graph or DiGraph
    
    Example:
        >>> edges = [(1, 2, 5), (2, 3, 3), (1, 3, 10)]
        >>> G = from_edge_list(edges, weighted=True)
    """
    if directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    
    if weighted:
        for edge in edges:
            if len(edge) == 3:
                u, v, weight = edge
                G.add_edge(u, v, weight=weight)
            else:
                u, v = edge
                G.add_edge(u, v, weight=1.0)
    else:
        G.add_edges_from(edges)
    
    return G


def to_edge_list(
    graph: Union[nx.Graph, nx.DiGraph],
    include_weights: bool = True
) -> List[Tuple]:
    """
    Convert graph to edge list.
    
    Args:
        graph: NetworkX Graph or DiGraph
        include_weights: Whether to include edge weights in output
    
    Returns:
        List of tuples (u, v) or (u, v, weight)
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edge(1, 2, weight=5)
        >>> edges = to_edge_list(G)
        >>> print(edges)  # [(1, 2, 5)]
    """
    if include_weights:
        return [(u, v, data.get('weight', 1.0)) 
                for u, v, data in graph.edges(data=True)]
    else:
        return list(graph.edges())


def from_dict(
    graph_dict: Dict[Any, List[Tuple]],
    directed: bool = False
) -> Union[nx.Graph, nx.DiGraph]:
    """
    Create graph from adjacency dictionary.
    
    Args:
        graph_dict: Dictionary where keys are nodes and values are lists of
                   (neighbor, weight) tuples
        directed: Whether to create directed graph
    
    Returns:
        NetworkX Graph or DiGraph
    
    Example:
        >>> graph_dict = {
        ...     'A': [('B', 5), ('C', 2)],
        ...     'B': [('C', 1)],
        ...     'C': []
        ... }
        >>> G = from_dict(graph_dict)
    """
    if directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    
    # Add all nodes first
    G.add_nodes_from(graph_dict.keys())
    
    # Add edges
    for node, neighbors in graph_dict.items():
        for neighbor_info in neighbors:
            if isinstance(neighbor_info, tuple):
                neighbor, weight = neighbor_info
                G.add_edge(node, neighbor, weight=weight)
            else:
                G.add_edge(node, neighbor_info)
    
    return G


def to_dict(
    graph: Union[nx.Graph, nx.DiGraph],
    include_weights: bool = True
) -> Dict[Any, List]:
    """
    Convert graph to adjacency dictionary.
    
    Args:
        graph: NetworkX Graph or DiGraph
        include_weights: Whether to include edge weights
    
    Returns:
        Dictionary mapping nodes to list of neighbors (with weights if requested)
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edge('A', 'B', weight=5)
        >>> d = to_dict(G)
        >>> print(d)  # {'A': [('B', 5)], 'B': [('A', 5)]}
    """
    result = {}
    
    for node in graph.nodes():
        if include_weights:
            neighbors = [(neighbor, graph[node][neighbor].get('weight', 1.0))
                        for neighbor in graph.neighbors(node)]
        else:
            neighbors = list(graph.neighbors(node))
        result[node] = neighbors
    
    return result


def to_graphml(
    graph: Union[nx.Graph, nx.DiGraph],
    filepath: str
) -> None:
    """
    Export graph to GraphML format.
    
    Args:
        graph: NetworkX Graph or DiGraph
        filepath: Path to output file
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edge(1, 2, weight=5)
        >>> to_graphml(G, 'graph.graphml')
    """
    nx.write_graphml(graph, filepath)


def from_graphml(filepath: str) -> Union[nx.Graph, nx.DiGraph]:
    """
    Import graph from GraphML format.
    
    Args:
        filepath: Path to GraphML file
    
    Returns:
        NetworkX Graph or DiGraph
    
    Example:
        >>> G = from_graphml('graph.graphml')
    """
    return nx.read_graphml(filepath)
