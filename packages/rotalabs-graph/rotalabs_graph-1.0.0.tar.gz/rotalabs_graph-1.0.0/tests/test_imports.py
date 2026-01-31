"""Tests for verifying package imports and exports."""

import pytest


def test_version():
    """Check version is '0.1.0'."""
    from rotalabs_graph import __version__

    assert __version__ == "0.1.0"


def test_core_imports():
    """Test core type imports."""
    from rotalabs_graph import (
        TrustGraph,
        TrustNode,
        TrustEdge,
        TrustScore,
        NodeType,
        EdgeType,
        PropagationConfig,
        GraphConfig,
        GraphError,
        NodeNotFoundError,
        EdgeNotFoundError,
    )

    # Verify enums
    assert NodeType.MODEL.value == "model"
    assert NodeType.AGENT.value == "agent"
    assert EdgeType.TRUSTS.value == "trusts"
    assert EdgeType.DELEGATES.value == "delegates"

    # Verify classes exist
    assert TrustGraph is not None
    assert TrustNode is not None
    assert TrustEdge is not None
    assert TrustScore is not None

    # Verify configs
    assert PropagationConfig is not None
    assert GraphConfig is not None

    # Verify exceptions
    assert issubclass(GraphError, Exception)
    assert issubclass(NodeNotFoundError, GraphError)
    assert issubclass(EdgeNotFoundError, GraphError)


def test_propagation_imports():
    """Test propagation module imports."""
    from rotalabs_graph import (
        BasePropagator,
        PageRankPropagator,
        EigenTrustPropagator,
        WeightedPropagator,
    )

    assert BasePropagator is not None
    assert PageRankPropagator is not None
    assert EigenTrustPropagator is not None
    assert WeightedPropagator is not None


def test_analysis_imports():
    """Test analysis module imports."""
    from rotalabs_graph import (
        AnomalyDetector,
        AnomalyType,
        TrustAnomaly,
        PathAnalyzer,
        ClusterAnalyzer,
        TrustCluster,
        MetricsCalculator,
        GraphMetrics,
    )

    assert AnomalyDetector is not None
    assert AnomalyType.CIRCULAR_TRUST.value == "circular_trust"
    assert PathAnalyzer is not None
    assert ClusterAnalyzer is not None
    assert MetricsCalculator is not None


def test_temporal_imports():
    """Test temporal module imports."""
    from rotalabs_graph import (
        DecayFunction,
        TrustHistory,
        TrustEvent,
        TemporalTrustGraph,
        exponential_decay,
        linear_decay,
    )

    assert DecayFunction.EXPONENTIAL.value == "exponential"
    assert TrustHistory is not None
    assert TrustEvent is not None
    assert TemporalTrustGraph is not None
    assert callable(exponential_decay)
    assert callable(linear_decay)


def test_utils_imports():
    """Test utils module imports."""
    from rotalabs_graph import (
        generate_id,
        validate_trust_score,
        merge_graphs,
        filter_by_trust,
        to_json,
        from_json,
    )

    assert callable(generate_id)
    assert callable(validate_trust_score)
    assert callable(merge_graphs)
    assert callable(filter_by_trust)
    assert callable(to_json)
    assert callable(from_json)


def test_all_exports():
    """Verify all __all__ items are importable."""
    import rotalabs_graph

    all_exports = rotalabs_graph.__all__

    for name in all_exports:
        assert hasattr(rotalabs_graph, name), f"Missing export: {name}"
        obj = getattr(rotalabs_graph, name)
        assert obj is not None, f"Export is None: {name}"


def test_available_modules():
    """Test get_available_modules function."""
    from rotalabs_graph import get_available_modules

    modules = get_available_modules()

    assert "core" in modules
    assert "propagation" in modules
    assert "analysis" in modules
    assert "temporal" in modules
    assert "utils" in modules
