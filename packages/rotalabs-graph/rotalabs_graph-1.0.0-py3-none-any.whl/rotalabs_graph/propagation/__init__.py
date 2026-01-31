"""Trust propagation algorithms for trust graphs.

This module provides various algorithms for propagating trust through
entity graphs. Each propagator takes a TrustGraph and computes trust
scores for all nodes based on graph structure and edge weights.

Algorithms:
    - PageRankPropagator: Classic PageRank algorithm for trust voting
    - EigenTrustPropagator: EigenTrust algorithm from P2P networks
    - WeightedPropagator: Simple weighted propagation with decay
    - DijkstraPropagator: Shortest path based trust propagation
    - GNNPropagator: GNN-based learned propagation (requires torch-geometric)

Example:
    >>> from rotalabs_graph.core import TrustGraph, NodeType
    >>> from rotalabs_graph.propagation import PageRankPropagator
    >>>
    >>> # Create a trust graph
    >>> graph = TrustGraph()
    >>> graph.add_node("model-a", node_type=NodeType.MODEL)
    >>> graph.add_node("model-b", node_type=NodeType.MODEL)
    >>> graph.add_edge("model-a", "model-b", weight=0.8)
    >>>
    >>> # Propagate trust
    >>> propagator = PageRankPropagator(damping=0.85)
    >>> scores = propagator.propagate(graph)
    >>> print(f"model-b trust: {scores['model-b'].value:.3f}")
"""

from .base import BasePropagator
from .eigentrust import EigenTrustPropagator
from .pagerank import PageRankPropagator
from .weighted import DijkstraPropagator, WeightedPropagator

# GNN propagator requires optional dependencies
try:
    from .gnn import GNNPropagator, TrustGNN

    _HAS_GNN = True
except ImportError:
    _HAS_GNN = False
    GNNPropagator = None
    TrustGNN = None

__all__ = [
    # Base
    "BasePropagator",
    # Classical algorithms
    "PageRankPropagator",
    "EigenTrustPropagator",
    "WeightedPropagator",
    "DijkstraPropagator",
    # GNN (optional)
    "GNNPropagator",
    "TrustGNN",
]


def get_propagator(
    algorithm: str = "pagerank",
    **kwargs,
) -> BasePropagator:
    """Factory function to create a propagator by name.

    Args:
        algorithm: Name of the algorithm (pagerank, eigentrust, weighted, dijkstra, gnn)
        **kwargs: Arguments to pass to the propagator constructor

    Returns:
        Configured propagator instance

    Raises:
        ValueError: If algorithm name is unknown
        ImportError: If GNN is requested but torch-geometric is not installed
    """
    algorithm = algorithm.lower()

    propagators = {
        "pagerank": PageRankPropagator,
        "eigentrust": EigenTrustPropagator,
        "weighted": WeightedPropagator,
        "dijkstra": DijkstraPropagator,
    }

    if algorithm == "gnn":
        if not _HAS_GNN:
            raise ImportError(
                "GNN propagation requires torch-geometric. "
                "Install with: pip install rotalabs-graph[gnn]"
            )
        return GNNPropagator(**kwargs)

    if algorithm not in propagators:
        raise ValueError(
            f"Unknown algorithm: {algorithm}. "
            f"Available: {list(propagators.keys()) + ['gnn']}"
        )

    return propagators[algorithm](**kwargs)
