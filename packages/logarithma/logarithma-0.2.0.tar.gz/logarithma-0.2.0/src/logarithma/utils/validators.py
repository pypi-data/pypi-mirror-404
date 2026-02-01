"""
Graph Validators
===============

Functions to validate graph properties and check constraints.
"""

from typing import Union, Dict, Any
import networkx as nx


def is_connected(graph: Union[nx.Graph, nx.DiGraph]) -> bool:
    """
    Check if graph is connected.
    
    For directed graphs, checks if weakly connected.
    
    Args:
        graph: NetworkX Graph or DiGraph
    
    Returns:
        True if connected, False otherwise
    
    Example:
        >>> from logarithma.utils import is_connected
        >>> G = nx.Graph()
        >>> G.add_edges_from([(1, 2), (2, 3)])
        >>> print(is_connected(G))  # True
        >>> G.add_node(4)  # Isolated node
        >>> print(is_connected(G))  # False
    """
    if not graph:
        return True
    
    if isinstance(graph, nx.DiGraph):
        return nx.is_weakly_connected(graph)
    else:
        return nx.is_connected(graph)


def is_dag(graph: Union[nx.Graph, nx.DiGraph]) -> bool:
    """
    Check if graph is a Directed Acyclic Graph (DAG).
    
    Args:
        graph: NetworkX Graph or DiGraph
    
    Returns:
        True if DAG, False otherwise
    
    Example:
        >>> DG = nx.DiGraph()
        >>> DG.add_edges_from([(1, 2), (2, 3)])
        >>> print(is_dag(DG))  # True
        >>> DG.add_edge(3, 1)  # Create cycle
        >>> print(is_dag(DG))  # False
    """
    if not isinstance(graph, nx.DiGraph):
        # Undirected graphs can't be DAGs (they have cycles by definition)
        return False
    
    return nx.is_directed_acyclic_graph(graph)


def has_negative_weights(graph: Union[nx.Graph, nx.DiGraph]) -> bool:
    """
    Check if graph has any negative edge weights.
    
    Args:
        graph: NetworkX Graph or DiGraph
    
    Returns:
        True if any edge has negative weight, False otherwise
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edge(1, 2, weight=5)
        >>> print(has_negative_weights(G))  # False
        >>> G.add_edge(2, 3, weight=-1)
        >>> print(has_negative_weights(G))  # True
    """
    for u, v, data in graph.edges(data=True):
        weight = data.get('weight', 1)
        if weight < 0:
            return True
    return False


def has_self_loops(graph: Union[nx.Graph, nx.DiGraph]) -> bool:
    """
    Check if graph has self-loops (edges from a node to itself).
    
    Args:
        graph: NetworkX Graph or DiGraph
    
    Returns:
        True if has self-loops, False otherwise
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edge(1, 2)
        >>> print(has_self_loops(G))  # False
        >>> G.add_edge(1, 1)  # Self-loop
        >>> print(has_self_loops(G))  # True
    """
    return graph.number_of_selfloops() > 0


def is_bipartite(graph: nx.Graph) -> bool:
    """
    Check if graph is bipartite (2-colorable).
    
    A graph is bipartite if its vertices can be divided into two disjoint sets
    such that no two vertices within the same set are adjacent.
    
    Args:
        graph: NetworkX Graph (undirected)
    
    Returns:
        True if bipartite, False otherwise
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edges_from([(1, 2), (2, 3), (3, 4)])
        >>> print(is_bipartite(G))  # True
        >>> G.add_edge(1, 3)  # Create odd cycle
        >>> print(is_bipartite(G))  # False
    """
    if isinstance(graph, nx.DiGraph):
        # Convert to undirected for bipartite check
        graph = graph.to_undirected()
    
    return nx.is_bipartite(graph)


def validate_graph(
    graph: Union[nx.Graph, nx.DiGraph],
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate graph against multiple requirements.
    
    Args:
        graph: NetworkX Graph or DiGraph
        requirements: Dictionary of requirements to check
            Possible keys:
            - 'connected': bool - must be connected
            - 'dag': bool - must be DAG
            - 'no_negative_weights': bool - no negative weights allowed
            - 'no_self_loops': bool - no self-loops allowed
            - 'bipartite': bool - must be bipartite
            - 'min_nodes': int - minimum number of nodes
            - 'max_nodes': int - maximum number of nodes
            - 'min_edges': int - minimum number of edges
            - 'max_edges': int - maximum number of edges
    
    Returns:
        Dictionary with validation results:
            - 'valid': bool - overall validation result
            - 'errors': List[str] - list of validation errors
            - 'warnings': List[str] - list of warnings
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edges_from([(1, 2), (2, 3)])
        >>> requirements = {
        ...     'connected': True,
        ...     'no_negative_weights': True,
        ...     'min_nodes': 3
        ... }
        >>> result = validate_graph(G, requirements)
        >>> print(result['valid'])  # True
        >>> print(result['errors'])  # []
    """
    errors = []
    warnings = []
    
    # Check connectivity
    if requirements.get('connected', False):
        if not is_connected(graph):
            errors.append("Graph is not connected")
    
    # Check DAG
    if requirements.get('dag', False):
        if not is_dag(graph):
            errors.append("Graph is not a DAG")
    
    # Check negative weights
    if requirements.get('no_negative_weights', False):
        if has_negative_weights(graph):
            errors.append("Graph has negative edge weights")
    
    # Check self-loops
    if requirements.get('no_self_loops', False):
        if has_self_loops(graph):
            errors.append("Graph has self-loops")
    
    # Check bipartite
    if requirements.get('bipartite', False):
        if not is_bipartite(graph):
            errors.append("Graph is not bipartite")
    
    # Check node count
    n_nodes = graph.number_of_nodes()
    if 'min_nodes' in requirements:
        if n_nodes < requirements['min_nodes']:
            errors.append(f"Graph has {n_nodes} nodes, minimum required: {requirements['min_nodes']}")
    
    if 'max_nodes' in requirements:
        if n_nodes > requirements['max_nodes']:
            warnings.append(f"Graph has {n_nodes} nodes, maximum recommended: {requirements['max_nodes']}")
    
    # Check edge count
    n_edges = graph.number_of_edges()
    if 'min_edges' in requirements:
        if n_edges < requirements['min_edges']:
            errors.append(f"Graph has {n_edges} edges, minimum required: {requirements['min_edges']}")
    
    if 'max_edges' in requirements:
        if n_edges > requirements['max_edges']:
            warnings.append(f"Graph has {n_edges} edges, maximum recommended: {requirements['max_edges']}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def is_weighted(graph: Union[nx.Graph, nx.DiGraph]) -> bool:
    """
    Check if graph has weighted edges.
    
    Args:
        graph: NetworkX Graph or DiGraph
    
    Returns:
        True if all edges have 'weight' attribute, False otherwise
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edge(1, 2, weight=5)
        >>> print(is_weighted(G))  # True
    """
    if graph.number_of_edges() == 0:
        return False
    
    for u, v, data in graph.edges(data=True):
        if 'weight' not in data:
            return False
    return True


def is_simple(graph: Union[nx.Graph, nx.DiGraph]) -> bool:
    """
    Check if graph is simple (no self-loops or multiple edges).
    
    Args:
        graph: NetworkX Graph or DiGraph
    
    Returns:
        True if simple, False otherwise
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edges_from([(1, 2), (2, 3)])
        >>> print(is_simple(G))  # True
    """
    # Check for self-loops
    if has_self_loops(graph):
        return False
    
    # Check for multiple edges (only relevant for MultiGraph)
    if isinstance(graph, (nx.MultiGraph, nx.MultiDiGraph)):
        for u, v in graph.edges():
            if graph.number_of_edges(u, v) > 1:
                return False
    
    return True
