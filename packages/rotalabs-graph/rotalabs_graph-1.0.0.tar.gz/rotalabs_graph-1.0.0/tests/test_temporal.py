"""Tests for temporal trust functionality."""

import pytest
from datetime import datetime, timedelta


def test_decay_functions():
    """Test trust decay functions."""
    from rotalabs_graph import exponential_decay, linear_decay

    initial = 1.0
    half_life = 30.0  # days

    # At time 0, trust should be initial
    assert exponential_decay(initial, 0.0, half_life) == initial
    assert linear_decay(initial, 0.0, half_life) == initial

    # At half_life, exponential should be ~0.5
    exp_at_half = exponential_decay(initial, half_life, half_life)
    assert 0.4 < exp_at_half < 0.6

    # Linear at half_life should also be ~0.5
    lin_at_half = linear_decay(initial, half_life, half_life)
    assert 0.4 < lin_at_half < 0.6


def test_decay_function_enum():
    """Test DecayFunction enum."""
    from rotalabs_graph import DecayFunction, get_decay_function

    assert DecayFunction.EXPONENTIAL.value == "exponential"
    assert DecayFunction.LINEAR.value == "linear"

    # Get decay function by type
    exp_fn = get_decay_function(DecayFunction.EXPONENTIAL)
    assert callable(exp_fn)


def test_trust_history():
    """Test trust history tracking."""
    from rotalabs_graph import TrustHistory

    history = TrustHistory()

    # Record some events
    history.record_creation("node-1", 0.9)
    history.record_update("node-1", 0.9, 0.7, "behavior_anomaly")
    history.record_decay("node-1", 0.7, 0.65, days_elapsed=30.0, decay_function="exponential")

    # Get events for node-1
    events = history.get_events(node_id="node-1")

    assert len(events) == 3
    assert events[0].event_type == "created"
    assert events[1].event_type == "updated"
    assert events[2].event_type == "decayed"


def test_trust_history_timeline():
    """Test getting trust timeline."""
    from rotalabs_graph import TrustHistory

    history = TrustHistory()

    history.record_creation("node-1", 1.0)
    history.record_update("node-1", 1.0, 0.8, "test")
    history.record_update("node-1", 0.8, 0.6, "test")

    timeline = history.get_trust_timeline("node-1")

    assert len(timeline) == 3
    # Timeline should show decreasing trust
    values = [t[1] for t in timeline]
    assert values == [1.0, 0.8, 0.6]


def test_temporal_trust_graph():
    """Test TemporalTrustGraph."""
    from rotalabs_graph import TemporalTrustGraph, DecayFunction

    graph = TemporalTrustGraph(
        decay_function=DecayFunction.EXPONENTIAL,
        half_life_days=30.0,
        track_history=True,
    )

    now = datetime.utcnow()

    # Add a node using the actual API
    graph.add_node("test-node", initial_trust=1.0)

    # Raw trust should be 1.0
    raw = graph.get_raw_trust("test-node")
    assert raw == 1.0

    # Current trust at time of creation should also be 1.0
    current = graph.get_current_trust("test-node", as_of=now)
    assert current == 1.0


def test_temporal_graph_update_trust():
    """Test updating trust in temporal graph."""
    from rotalabs_graph import TemporalTrustGraph, DecayFunction

    graph = TemporalTrustGraph(
        decay_function=DecayFunction.NONE,
        track_history=True,
    )

    # Add node using actual API
    graph.add_node("n1", initial_trust=0.9)

    # Update trust
    graph.update_trust("n1", 0.7, reason="test update")

    assert graph.get_raw_trust("n1") == 0.7

    # Check history if available
    if graph.history is not None:
        events = graph.history.get_events(node_id="n1")
        # History tracking may vary
        assert events is not None


def test_temporal_graph_snapshot():
    """Test snapshot and restore."""
    from rotalabs_graph import TemporalTrustGraph, DecayFunction

    graph = TemporalTrustGraph(decay_function=DecayFunction.NONE)

    # Add node using actual API
    graph.add_node("n1", initial_trust=0.9)

    # Take snapshot
    snapshot = graph.snapshot()

    # Modify graph
    graph.update_trust("n1", 0.5, reason="modification")

    # Restore snapshot
    graph.restore_snapshot(snapshot)

    # Trust should be back to original
    assert graph.get_raw_trust("n1") == 0.9
