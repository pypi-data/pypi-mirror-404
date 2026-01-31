"""Tests for propagation algorithms."""

import pytest
from datetime import datetime


def create_test_graph():
    """Create a simple test graph."""
    from rotalabs_graph import TrustGraph, TrustNode, TrustEdge, NodeType, EdgeType

    graph = TrustGraph()
    now = datetime.utcnow()

    # Create a diamond graph: A -> B, A -> C, B -> D, C -> D
    nodes = ["A", "B", "C", "D"]
    for name in nodes:
        graph.add_node(TrustNode(
            id=name, name=name, node_type=NodeType.MODEL,
            base_trust=1.0, created_at=now, updated_at=now
        ))

    edges = [("A", "B", 0.9), ("A", "C", 0.8), ("B", "D", 0.7), ("C", "D", 0.6)]
    for src, tgt, weight in edges:
        graph.add_edge(TrustEdge(
            source_id=src, target_id=tgt, edge_type=EdgeType.TRUSTS,
            weight=weight, created_at=now
        ))

    return graph


def test_pagerank_propagator():
    """Test PageRank propagator can be instantiated."""
    from rotalabs_graph import PageRankPropagator, PropagationConfig

    config = PropagationConfig(damping_factor=0.85)
    propagator = PageRankPropagator(config)

    assert propagator is not None
    assert propagator.config.damping_factor == 0.85


def test_eigentrust_propagator():
    """Test EigenTrust propagator can be instantiated."""
    from rotalabs_graph import EigenTrustPropagator

    propagator = EigenTrustPropagator(pre_trusted_nodes=["A"])

    assert propagator is not None


def test_weighted_propagator():
    """Test weighted propagator can be instantiated."""
    from rotalabs_graph import WeightedPropagator, PropagationConfig

    config = PropagationConfig(decay_per_hop=0.1)
    propagator = WeightedPropagator(config)

    assert propagator is not None
    assert propagator.config.decay_per_hop == 0.1


def test_propagator_empty_graph():
    """Test propagation on empty graph raises error."""
    from rotalabs_graph import TrustGraph, PageRankPropagator, PropagationError

    graph = TrustGraph()
    propagator = PageRankPropagator()

    with pytest.raises(PropagationError):
        propagator.propagate(graph)


def test_propagation_config():
    """Test propagation configuration."""
    from rotalabs_graph import PropagationConfig

    config = PropagationConfig(
        max_iterations=50,
        convergence_threshold=1e-4,
        damping_factor=0.9,
        decay_per_hop=0.05,
    )

    assert config.max_iterations == 50
    assert config.damping_factor == 0.9
    assert config.decay_per_hop == 0.05
