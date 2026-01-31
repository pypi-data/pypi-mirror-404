"""
rotalabs-graph - GNN-based trust propagation for AI systems.

This package provides tools for modeling, propagating, and analyzing
trust relationships in AI infrastructure.

Key Features:
    - Trust graph data structures with temporal dynamics
    - Multiple propagation algorithms (PageRank, EigenTrust, GNN)
    - Anomaly detection for trust networks
    - Path and cluster analysis
    - Temporal trust dynamics with decay functions
    - Comprehensive serialization support

Quick Start:
    >>> from rotalabs_graph import TemporalTrustGraph, DecayFunction
    >>>
    >>> # Create a temporal trust graph
    >>> graph = TemporalTrustGraph(
    ...     decay_function=DecayFunction.EXPONENTIAL,
    ...     half_life_days=30.0,
    ... )
    >>>
    >>> # Add nodes with trust scores
    >>> graph.add_node("agent-1", initial_trust=0.9)
    >>> graph.add_node("agent-2", initial_trust=0.8)
    >>> graph.add_node("agent-3", initial_trust=0.7)
    >>>
    >>> # Add trust relationships
    >>> graph.add_edge("agent-1", "agent-2", weight=0.85)
    >>> graph.add_edge("agent-2", "agent-3", weight=0.75)
    >>>
    >>> # Get current trust (with decay applied)
    >>> trust = graph.get_current_trust("agent-1")
    >>>
    >>> # Serialize to JSON
    >>> from rotalabs_graph import to_json, from_json
    >>> json_str = to_json(graph)
    >>> loaded = from_json(json_str)

For more information, see:
    https://rotalabs.ai/docs/graph
    https://github.com/rotalabs/rotalabs-graph
"""

from rotalabs_graph._version import __version__

# =============================================================================
# Temporal module (always available)
# =============================================================================
from rotalabs_graph.temporal import (
    # Decay functions
    DecayFunction,
    linear_decay,
    exponential_decay,
    logarithmic_decay,
    step_decay,
    no_decay,
    get_decay_function,
    apply_decay,
    # History tracking
    TrustEvent,
    TrustHistory,
    # Dynamic graph
    TemporalTrustGraph,
)

# =============================================================================
# Utility functions (always available)
# =============================================================================
from rotalabs_graph.utils import (
    # ID and validation
    generate_id,
    validate_trust_score,
    # Visualization helpers
    trust_to_color,
    trust_to_gradient_color,
    format_trust,
    # Graph operations
    merge_graphs,
    filter_by_trust,
    get_trust_statistics,
    partition_by_trust,
    # Serialization
    to_json,
    from_json,
    to_graphml,
    from_graphml,
    to_adjacency_matrix,
    from_adjacency_matrix,
    to_networkx,
    from_networkx,
)

# =============================================================================
# Integration module (always available, dependencies optional)
# =============================================================================
from rotalabs_graph.integration import (
    ComplyIntegration,
    AuditIntegration,
    CascadeIntegration,
    ProbeIntegration,
)

# =============================================================================
# Core module (import if available)
# Core classes will be available when core module is implemented
# =============================================================================
try:
    from rotalabs_graph.core import (
        TrustGraph,
        TrustNode,
        TrustEdge,
        TrustScore,
        TrustPath,
        NodeType,
        EdgeType,
        AggregationMethod,
        PropagationConfig,
        GraphConfig,
        GNNConfig,
        EigenTrustConfig,
        GraphError,
        NodeNotFoundError,
        EdgeNotFoundError,
        PropagationError,
        ConvergenceError,
        InvalidGraphError,
        ValidationError,
        CycleDetectedError,
        GNNError,
        GNNNotFittedError,
        aggregate_scores,
        PropagationResult,
    )
    _HAS_CORE = True
except ImportError:
    _HAS_CORE = False

# =============================================================================
# Propagation module (import if available)
# Propagation algorithms will be available when propagation module is implemented
# =============================================================================
try:
    from rotalabs_graph.propagation import (
        BasePropagator,
        PageRankPropagator,
        EigenTrustPropagator,
        WeightedPropagator,
        DijkstraPropagator,
        get_propagator,
    )
    _HAS_PROPAGATION = True
except ImportError:
    _HAS_PROPAGATION = False

# Conditionally import GNN propagator (requires torch)
try:
    from rotalabs_graph.propagation.gnn import GNNPropagator, TrustGNN
    _HAS_GNN = True
except ImportError:
    _HAS_GNN = False

# =============================================================================
# Analysis module (import if available)
# Analysis tools will be available when analysis module is implemented
# =============================================================================
try:
    from rotalabs_graph.analysis import (
        AnomalyDetector,
        AnomalyType,
        TrustAnomaly,
        PathAnalyzer,
        ClusterAnalyzer,
        TrustCluster,
        MetricsCalculator,
        GraphMetrics,
    )
    _HAS_ANALYSIS = True
except ImportError:
    _HAS_ANALYSIS = False

# =============================================================================
# Public API
# =============================================================================
__all__ = [
    # Version
    "__version__",
    # Temporal - Decay functions
    "DecayFunction",
    "linear_decay",
    "exponential_decay",
    "logarithmic_decay",
    "step_decay",
    "no_decay",
    "get_decay_function",
    "apply_decay",
    # Temporal - History
    "TrustEvent",
    "TrustHistory",
    # Temporal - Dynamic graph
    "TemporalTrustGraph",
    # Utils - Helpers
    "generate_id",
    "validate_trust_score",
    "trust_to_color",
    "trust_to_gradient_color",
    "format_trust",
    "merge_graphs",
    "filter_by_trust",
    "get_trust_statistics",
    "partition_by_trust",
    # Utils - Serialization
    "to_json",
    "from_json",
    "to_graphml",
    "from_graphml",
    "to_adjacency_matrix",
    "from_adjacency_matrix",
    "to_networkx",
    "from_networkx",
    # Integration
    "ComplyIntegration",
    "AuditIntegration",
    "CascadeIntegration",
    "ProbeIntegration",
]

# Add core exports if available
if _HAS_CORE:
    __all__.extend([
        "TrustGraph",
        "TrustNode",
        "TrustEdge",
        "TrustScore",
        "TrustPath",
        "NodeType",
        "EdgeType",
        "AggregationMethod",
        "PropagationConfig",
        "GraphConfig",
        "GNNConfig",
        "EigenTrustConfig",
        "GraphError",
        "NodeNotFoundError",
        "EdgeNotFoundError",
        "PropagationError",
        "ConvergenceError",
        "InvalidGraphError",
        "ValidationError",
        "CycleDetectedError",
        "GNNError",
        "GNNNotFittedError",
        "aggregate_scores",
        "PropagationResult",
    ])

# Add propagation exports if available
if _HAS_PROPAGATION:
    __all__.extend([
        "BasePropagator",
        "PageRankPropagator",
        "EigenTrustPropagator",
        "WeightedPropagator",
        "DijkstraPropagator",
        "get_propagator",
    ])

if _HAS_GNN:
    __all__.extend(["GNNPropagator", "TrustGNN"])

# Add analysis exports if available
if _HAS_ANALYSIS:
    __all__.extend([
        "AnomalyDetector",
        "AnomalyType",
        "TrustAnomaly",
        "PathAnalyzer",
        "ClusterAnalyzer",
        "TrustCluster",
        "MetricsCalculator",
        "GraphMetrics",
    ])


def get_available_modules() -> dict:
    """Get information about available modules.

    Returns:
        Dictionary with module availability status

    Example:
        >>> from rotalabs_graph import get_available_modules
        >>> modules = get_available_modules()
        >>> modules["temporal"]
        True
    """
    return {
        "temporal": True,  # Always available
        "utils": True,  # Always available
        "integration": True,  # Always available (deps optional)
        "core": _HAS_CORE,
        "propagation": _HAS_PROPAGATION,
        "gnn": _HAS_GNN,
        "analysis": _HAS_ANALYSIS,
    }


def check_dependencies() -> dict:
    """Check optional dependency availability.

    Returns:
        Dictionary mapping dependency names to availability

    Example:
        >>> from rotalabs_graph import check_dependencies
        >>> deps = check_dependencies()
        >>> deps["numpy"]
        True
    """
    deps = {}

    try:
        import numpy
        deps["numpy"] = True
    except ImportError:
        deps["numpy"] = False

    try:
        import pandas
        deps["pandas"] = True
    except ImportError:
        deps["pandas"] = False

    try:
        import networkx
        deps["networkx"] = True
    except ImportError:
        deps["networkx"] = False

    try:
        import torch
        deps["torch"] = True
    except ImportError:
        deps["torch"] = False

    try:
        import torch_geometric
        deps["torch_geometric"] = True
    except ImportError:
        deps["torch_geometric"] = False

    return deps
