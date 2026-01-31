"""Temporal trust dynamics for rotalabs-graph.

This module provides tools for modeling trust that changes over time:

- **Decay Functions**: Model how trust diminishes without reinforcement
- **History Tracking**: Audit trail of all trust changes
- **Temporal Graph**: Trust graph with built-in temporal dynamics

Example:
    >>> from rotalabs_graph.temporal import (
    ...     TemporalTrustGraph,
    ...     DecayFunction,
    ...     TrustHistory,
    ... )
    >>>
    >>> # Create a temporal trust graph with exponential decay
    >>> graph = TemporalTrustGraph(
    ...     decay_function=DecayFunction.EXPONENTIAL,
    ...     half_life_days=30.0,
    ... )
    >>>
    >>> # Add nodes and edges
    >>> graph.add_node("agent-1", initial_trust=0.9)
    >>> graph.add_node("agent-2", initial_trust=0.8)
    >>> graph.add_edge("agent-1", "agent-2", weight=0.7)
    >>>
    >>> # Trust decays over time
    >>> from datetime import datetime, timedelta
    >>> future = datetime.now() + timedelta(days=30)
    >>> graph.get_current_trust("agent-1", as_of=future)  # ~0.45
"""

from rotalabs_graph.temporal.decay import (
    DecayFunction,
    linear_decay,
    exponential_decay,
    logarithmic_decay,
    step_decay,
    no_decay,
    get_decay_function,
    apply_decay,
)

from rotalabs_graph.temporal.history import (
    TrustEvent,
    TrustHistory,
)

from rotalabs_graph.temporal.dynamic import (
    TemporalTrustGraph,
)

__all__ = [
    # Decay functions
    "DecayFunction",
    "linear_decay",
    "exponential_decay",
    "logarithmic_decay",
    "step_decay",
    "no_decay",
    "get_decay_function",
    "apply_decay",
    # History
    "TrustEvent",
    "TrustHistory",
    # Dynamic graph
    "TemporalTrustGraph",
]
