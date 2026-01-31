"""Tests for analysis modules."""

import pytest
from datetime import datetime


def create_test_graph():
    """Create a test graph for analysis."""
    from rotalabs_graph import TrustGraph, TrustNode, TrustEdge, NodeType, EdgeType

    graph = TrustGraph()
    now = datetime.utcnow()

    # Create nodes
    for i in range(5):
        graph.add_node(TrustNode(
            id=f"n{i}", name=f"Node {i}", node_type=NodeType.MODEL,
            base_trust=0.8 + i * 0.05, created_at=now, updated_at=now
        ))

    # Create edges: chain with a cycle
    edges = [
        ("n0", "n1", 0.9),
        ("n1", "n2", 0.8),
        ("n2", "n3", 0.7),
        ("n3", "n4", 0.6),
        ("n2", "n0", 0.5),  # Creates a cycle
    ]
    for src, tgt, weight in edges:
        graph.add_edge(TrustEdge(
            source_id=src, target_id=tgt, edge_type=EdgeType.TRUSTS,
            weight=weight, created_at=now
        ))

    return graph


def test_anomaly_detector_cycles():
    """Test cycle detection."""
    from rotalabs_graph import AnomalyDetector, AnomalyType

    graph = create_test_graph()
    detector = AnomalyDetector()

    anomalies = detector.detect_cycles(graph)

    # Should detect the cycle n0 -> n1 -> n2 -> n0
    assert len(anomalies) >= 1
    cycle_anomaly = anomalies[0]
    assert cycle_anomaly.anomaly_type == AnomalyType.CIRCULAR_TRUST


def test_anomaly_detector_all():
    """Test running all anomaly detection."""
    from rotalabs_graph import AnomalyDetector

    graph = create_test_graph()
    detector = AnomalyDetector()

    anomalies = detector.detect_all(graph)

    # Should return a list of anomalies
    assert isinstance(anomalies, list)


def test_path_analyzer():
    """Test path analysis."""
    from rotalabs_graph import PathAnalyzer

    graph = create_test_graph()
    analyzer = PathAnalyzer()

    # Find paths from n0 to n4
    paths = analyzer.find_all_paths(graph, "n0", "n4", max_length=5)

    assert len(paths) >= 1
    # Each path should start at n0 and end at n4
    for path in paths:
        assert path.source_id == "n0"
        assert path.target_id == "n4"


def test_path_analyzer_best_path():
    """Test finding best path."""
    from rotalabs_graph import PathAnalyzer

    graph = create_test_graph()
    analyzer = PathAnalyzer()

    best = analyzer.best_path(graph, "n0", "n4")

    assert best is not None
    assert best.source_id == "n0"
    assert best.target_id == "n4"
    assert best.path_trust > 0


def test_metrics_calculator():
    """Test graph metrics calculation."""
    from rotalabs_graph import MetricsCalculator

    graph = create_test_graph()
    calc = MetricsCalculator()

    metrics = calc.compute(graph)

    assert metrics.num_nodes == 5
    assert metrics.num_edges == 5
    assert 0 <= metrics.density <= 1
    assert metrics.avg_trust > 0


def test_cluster_analyzer():
    """Test community detection."""
    from rotalabs_graph import ClusterAnalyzer

    graph = create_test_graph()
    analyzer = ClusterAnalyzer()

    clusters = analyzer.detect_communities(graph)

    assert len(clusters) >= 1
    # All nodes should be in some cluster
    all_nodes = set()
    for cluster in clusters:
        all_nodes.update(cluster.node_ids)
    assert len(all_nodes) == 5
