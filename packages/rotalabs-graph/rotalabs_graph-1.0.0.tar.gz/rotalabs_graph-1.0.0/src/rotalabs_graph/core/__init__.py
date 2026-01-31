"""Core module for rotalabs-graph.

This module exports all core types, classes, and exceptions for
building and manipulating trust graphs.

Example:
    >>> from rotalabs_graph.core import (
    ...     TrustGraph,
    ...     TrustNode,
    ...     TrustEdge,
    ...     NodeType,
    ...     EdgeType,
    ... )
    >>>
    >>> graph = TrustGraph()
    >>> node = TrustNode(
    ...     id="model-1",
    ...     name="GPT-4",
    ...     node_type=NodeType.MODEL,
    ...     base_trust=0.95
    ... )
    >>> graph.add_node(node)
"""

from rotalabs_graph.core.config import (
    EigenTrustConfig,
    GNNConfig,
    GraphConfig,
    PropagationConfig,
    SerializationConfig,
    VisualizationConfig,
)
from rotalabs_graph.core.exceptions import (
    ConvergenceError,
    CycleDetectedError,
    EdgeNotFoundError,
    GNNError,
    GNNNotFittedError,
    GraphError,
    InvalidGraphError,
    NodeNotFoundError,
    PropagationError,
    ValidationError,
)
from rotalabs_graph.core.graph import TrustGraph
from rotalabs_graph.core.types import (
    AggregationMethod,
    EdgeType,
    NodeType,
    PropagationResult,
    TrustEdge,
    TrustNode,
    TrustPath,
    TrustScore,
    aggregate_scores,
)

__all__ = [
    # Types and enums
    "NodeType",
    "EdgeType",
    "AggregationMethod",
    "TrustNode",
    "TrustEdge",
    "TrustScore",
    "TrustPath",
    "PropagationResult",
    "aggregate_scores",
    # Main graph class
    "TrustGraph",
    # Configuration
    "GraphConfig",
    "PropagationConfig",
    "GNNConfig",
    "EigenTrustConfig",
    "SerializationConfig",
    "VisualizationConfig",
    # Exceptions
    "GraphError",
    "NodeNotFoundError",
    "EdgeNotFoundError",
    "CycleDetectedError",
    "PropagationError",
    "ConvergenceError",
    "InvalidGraphError",
    "ValidationError",
    "GNNError",
    "GNNNotFittedError",
]
