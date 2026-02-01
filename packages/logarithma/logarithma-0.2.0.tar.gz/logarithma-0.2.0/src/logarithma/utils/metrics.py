"""
Graph Metrics
=============

Calculate various graph metrics and properties.
"""

from typing import Union, Dict, Any
import networkx as nx


def graph_density(graph: Union[nx.Graph, nx.DiGraph]) -> float:
    """
    Calculate graph density (ratio of actual edges to possible edges).
    
    Density = 2*E / (V*(V-1)) for undirected graphs
    Density = E / (V*(V-1)) for directed graphs
    
    Args:
        graph: NetworkX Graph or DiGraph
    
    Returns:
        Density value between 0 and 1
    
    Example:
        >>> G = nx.complete_graph(10)
        >>> print(graph_density(G))  # 1.0 (complete graph)
        >>> G = nx.path_graph(10)
        >>> print(graph_density(G))  # Low density (sparse)
    """
    return nx.density(graph)


def average_degree(graph: Union[nx.Graph, nx.DiGraph]) -> float:
    """
    Calculate average degree of nodes in graph.
    
    Args:
        graph: NetworkX Graph or DiGraph
    
    Returns:
        Average degree
    
    Example:
        >>> G = nx.Graph()
        >>> G.add_edges_from([(1, 2), (2, 3), (3, 4)])
        >>> print(average_degree(G))  # 1.5
    """
    if graph.number_of_nodes() == 0:
        return 0.0
    
    degrees = [d for n, d in graph.degree()]
    return sum(degrees) / len(degrees)


def diameter(graph: Union[nx.Graph, nx.DiGraph]) -> int:
    """
    Calculate diameter of graph (longest shortest path).
    
    Only works for connected graphs.
    
    Args:
        graph: NetworkX Graph or DiGraph (must be connected)
    
    Returns:
        Diameter (maximum shortest path length)
    
    Raises:
        NetworkXError: If graph is not connected
    
    Example:
        >>> G = nx.path_graph(10)
        >>> print(diameter(G))  # 9 (path from 0 to 9)
    """
    if isinstance(graph, nx.DiGraph):
        if not nx.is_weakly_connected(graph):
            raise nx.NetworkXError("Graph is not connected")
    else:
        if not nx.is_connected(graph):
            raise nx.NetworkXError("Graph is not connected")
    
    return nx.diameter(graph)


def average_path_length(graph: Union[nx.Graph, nx.DiGraph]) -> float:
    """
    Calculate average shortest path length.
    
    Only works for connected graphs.
    
    Args:
        graph: NetworkX Graph or DiGraph (must be connected)
    
    Returns:
        Average path length
    
    Raises:
        NetworkXError: If graph is not connected
    
    Example:
        >>> G = nx.complete_graph(10)
        >>> print(average_path_length(G))  # 1.0 (all nodes directly connected)
    """
    if isinstance(graph, nx.DiGraph):
        if not nx.is_weakly_connected(graph):
            raise nx.NetworkXError("Graph is not connected")
    else:
        if not nx.is_connected(graph):
            raise nx.NetworkXError("Graph is not connected")
    
    return nx.average_shortest_path_length(graph)


def clustering_coefficient(
    graph: nx.Graph,
    node: Any = None
) -> Union[float, Dict[Any, float]]:
    """
    Calculate clustering coefficient.
    
    Measures how much nodes tend to cluster together.
    
    Args:
        graph: NetworkX Graph (undirected)
        node: Optional specific node (if None, returns dict for all nodes)
    
    Returns:
        Clustering coefficient (0 to 1) or dict of coefficients
    
    Example:
        >>> G = nx.complete_graph(5)
        >>> print(clustering_coefficient(G))  # All nodes: 1.0
    """
    if node is not None:
        return nx.clustering(graph, node)
    else:
        return nx.clustering(graph)


def degree_centrality(
    graph: Union[nx.Graph, nx.DiGraph]
) -> Dict[Any, float]:
    """
    Calculate degree centrality for all nodes.
    
    Measures importance based on number of connections.
    
    Args:
        graph: NetworkX Graph or DiGraph
    
    Returns:
        Dictionary mapping nodes to centrality values (0 to 1)
    
    Example:
        >>> G = nx.star_graph(10)
        >>> centrality = degree_centrality(G)
        >>> # Center node has highest centrality
    """
    return nx.degree_centrality(graph)


def betweenness_centrality(
    graph: Union[nx.Graph, nx.DiGraph],
    weighted: bool = True
) -> Dict[Any, float]:
    """
    Calculate betweenness centrality for all nodes.
    
    Measures importance based on number of shortest paths passing through node.
    
    Args:
        graph: NetworkX Graph or DiGraph
        weighted: Whether to use edge weights
    
    Returns:
        Dictionary mapping nodes to centrality values
    
    Example:
        >>> G = nx.path_graph(5)
        >>> centrality = betweenness_centrality(G)
        >>> # Middle nodes have higher centrality
    """
    weight = 'weight' if weighted else None
    return nx.betweenness_centrality(graph, weight=weight)


def closeness_centrality(
    graph: Union[nx.Graph, nx.DiGraph],
    weighted: bool = True
) -> Dict[Any, float]:
    """
    Calculate closeness centrality for all nodes.
    
    Measures how close a node is to all other nodes.
    
    Args:
        graph: NetworkX Graph or DiGraph
        weighted: Whether to use edge weights
    
    Returns:
        Dictionary mapping nodes to centrality values
    
    Example:
        >>> G = nx.star_graph(10)
        >>> centrality = closeness_centrality(G)
        >>> # Center node has highest closeness
    """
    distance = 'weight' if weighted else None
    return nx.closeness_centrality(graph, distance=distance)


def graph_summary(graph: Union[nx.Graph, nx.DiGraph]) -> Dict[str, Any]:
    """
    Get comprehensive summary of graph properties.
    
    Args:
        graph: NetworkX Graph or DiGraph
    
    Returns:
        Dictionary with various graph metrics
    
    Example:
        >>> G = nx.karate_club_graph()
        >>> summary = graph_summary(G)
        >>> for key, value in summary.items():
        ...     print(f"{key}: {value}")
    """
    summary = {
        'nodes': graph.number_of_nodes(),
        'edges': graph.number_of_edges(),
        'density': graph_density(graph),
        'average_degree': average_degree(graph),
        'is_directed': isinstance(graph, nx.DiGraph),
    }
    
    # Add connectivity info
    if isinstance(graph, nx.DiGraph):
        summary['is_weakly_connected'] = nx.is_weakly_connected(graph)
        summary['is_strongly_connected'] = nx.is_strongly_connected(graph)
    else:
        summary['is_connected'] = nx.is_connected(graph)
    
    # Add diameter and avg path length if connected
    try:
        summary['diameter'] = diameter(graph)
        summary['average_path_length'] = average_path_length(graph)
    except nx.NetworkXError:
        summary['diameter'] = None
        summary['average_path_length'] = None
    
    # Add degree statistics
    degrees = [d for n, d in graph.degree()]
    if degrees:
        summary['min_degree'] = min(degrees)
        summary['max_degree'] = max(degrees)
        summary['median_degree'] = sorted(degrees)[len(degrees) // 2]
    
    return summary
