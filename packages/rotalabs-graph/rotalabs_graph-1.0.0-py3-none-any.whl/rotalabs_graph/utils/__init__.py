"""Utility functions for rotalabs-graph.

This module provides helper functions for common operations:

- **ID Generation**: Create unique identifiers
- **Validation**: Validate and format trust scores
- **Visualization**: Map trust scores to colors
- **Graph Operations**: Merge, filter, and analyze graphs
- **Serialization**: Convert graphs to/from various formats

Example:
    >>> from rotalabs_graph.utils import (
    ...     generate_id,
    ...     validate_trust_score,
    ...     trust_to_color,
    ...     merge_graphs,
    ...     to_json,
    ...     from_json,
    ... )
    >>>
    >>> # Generate unique IDs
    >>> node_id = generate_id("agent")  # "agent_a1b2c3d4"
    >>>
    >>> # Validate trust scores
    >>> trust = validate_trust_score(1.5)  # Clamps to 1.0
    >>>
    >>> # Visualize trust
    >>> color = trust_to_color(0.8)  # "#4CAF50" (green)
"""

from rotalabs_graph.utils.helpers import (
    generate_id,
    validate_trust_score,
    trust_to_color,
    trust_to_gradient_color,
    format_trust,
    merge_graphs,
    filter_by_trust,
    get_trust_statistics,
    partition_by_trust,
)

from rotalabs_graph.utils.serialization import (
    to_json,
    from_json,
    to_graphml,
    from_graphml,
    to_adjacency_matrix,
    from_adjacency_matrix,
    to_networkx,
    from_networkx,
)

__all__ = [
    # Helpers
    "generate_id",
    "validate_trust_score",
    "trust_to_color",
    "trust_to_gradient_color",
    "format_trust",
    "merge_graphs",
    "filter_by_trust",
    "get_trust_statistics",
    "partition_by_trust",
    # Serialization
    "to_json",
    "from_json",
    "to_graphml",
    "from_graphml",
    "to_adjacency_matrix",
    "from_adjacency_matrix",
    "to_networkx",
    "from_networkx",
]
