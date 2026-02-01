"""
Utility Functions and Helpers
=============================

Graph generation, validation, conversion, and analysis utilities.

Modules:
- graph_generators: Create various types of graphs
- validators: Validate graph properties
- converters: Convert between graph formats
- metrics: Calculate graph metrics
"""

from .graph_generators import (
    generate_random_graph,
    generate_grid_graph,
    generate_complete_graph,
    generate_path_graph,
    generate_cycle_graph,
    generate_star_graph,
    generate_tree_graph,
    generate_scale_free_graph,
    generate_small_world_graph
)

from .validators import (
    is_connected,
    is_dag,
    has_negative_weights,
    has_self_loops,
    is_bipartite,
    is_weighted,
    is_simple,
    validate_graph
)

from .converters import (
    from_adjacency_matrix,
    to_adjacency_matrix,
    from_edge_list,
    to_edge_list,
    from_dict,
    to_dict,
    to_graphml,
    from_graphml
)

from .metrics import (
    graph_density,
    average_degree,
    diameter,
    average_path_length,
    clustering_coefficient,
    degree_centrality,
    betweenness_centrality,
    closeness_centrality,
    graph_summary
)

__all__ = [
    # Generators
    'generate_random_graph',
    'generate_grid_graph',
    'generate_complete_graph',
    'generate_path_graph',
    'generate_cycle_graph',
    'generate_star_graph',
    'generate_tree_graph',
    'generate_scale_free_graph',
    'generate_small_world_graph',
    # Validators
    'is_connected',
    'is_dag',
    'has_negative_weights',
    'has_self_loops',
    'is_bipartite',
    'is_weighted',
    'is_simple',
    'validate_graph',
    # Converters
    'from_adjacency_matrix',
    'to_adjacency_matrix',
    'from_edge_list',
    'to_edge_list',
    'from_dict',
    'to_dict',
    'to_graphml',
    'from_graphml',
    # Metrics
    'graph_density',
    'average_degree',
    'diameter',
    'average_path_length',
    'clustering_coefficient',
    'degree_centrality',
    'betweenness_centrality',
    'closeness_centrality',
    'graph_summary'
]
