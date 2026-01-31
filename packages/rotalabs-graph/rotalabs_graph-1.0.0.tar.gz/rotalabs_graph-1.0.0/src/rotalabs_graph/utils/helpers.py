"""Utility functions for rotalabs-graph.

This module provides helper functions for common operations:
- ID generation
- Trust score validation and formatting
- Graph operations (merge, filter)
- Color mapping for visualization

Example:
    >>> from rotalabs_graph.utils.helpers import (
    ...     generate_id,
    ...     validate_trust_score,
    ...     trust_to_color,
    ... )
    >>> node_id = generate_id("agent")
    >>> node_id
    'agent_a1b2c3d4'
    >>> validate_trust_score(1.5)
    1.0
    >>> trust_to_color(0.8)
    '#4CAF50'  # Green for high trust
"""

import uuid
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rotalabs_graph.temporal import TemporalTrustGraph


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix.

    Creates a URL-safe unique identifier using UUID4.
    Useful for creating node and edge IDs.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique identifier string

    Example:
        >>> id1 = generate_id()
        >>> id2 = generate_id("node")
        >>> id3 = generate_id("edge")
        >>> id1 != id2 != id3
        True
        >>> id2.startswith("node_")
        True
    """
    unique_part = uuid.uuid4().hex[:8]

    if prefix:
        # Clean prefix: lowercase, replace spaces with underscores
        clean_prefix = prefix.lower().replace(" ", "_").replace("-", "_")
        return f"{clean_prefix}_{unique_part}"

    return unique_part


def validate_trust_score(score: float, clamp: bool = True) -> float:
    """Validate and optionally clamp a trust score.

    Ensures trust scores are valid floating-point numbers
    within the range [0.0, 1.0].

    Args:
        score: Trust score to validate
        clamp: If True, clamp to [0, 1]; if False, raise on invalid

    Returns:
        Validated (and optionally clamped) trust score

    Raises:
        TypeError: If score is not numeric
        ValueError: If clamp=False and score is out of range

    Example:
        >>> validate_trust_score(0.5)
        0.5
        >>> validate_trust_score(1.5)  # Clamped
        1.0
        >>> validate_trust_score(-0.2)  # Clamped
        0.0
        >>> validate_trust_score(1.5, clamp=False)
        Traceback (most recent call last):
        ValueError: Trust score must be between 0 and 1, got 1.5
    """
    if not isinstance(score, (int, float)):
        raise TypeError(f"Trust score must be numeric, got {type(score).__name__}")

    score = float(score)

    if clamp:
        return max(0.0, min(1.0, score))

    if score < 0.0 or score > 1.0:
        raise ValueError(f"Trust score must be between 0 and 1, got {score}")

    return score


def trust_to_color(
    score: float,
    scheme: str = "traffic",
) -> str:
    """Convert trust score to a color for visualization.

    Maps trust scores to colors using various color schemes.
    Higher trust = more green/positive, lower trust = more red/negative.

    Args:
        score: Trust score (0.0 to 1.0)
        scheme: Color scheme to use:
            - "traffic": Red-Yellow-Green traffic light colors
            - "heat": Blue (cold/low) to Red (hot/high)
            - "grayscale": Black (low) to White (high)

    Returns:
        Hex color code (e.g., "#4CAF50")

    Example:
        >>> trust_to_color(0.9)  # High trust = green
        '#4CAF50'
        >>> trust_to_color(0.5)  # Medium trust = yellow
        '#FFEB3B'
        >>> trust_to_color(0.2)  # Low trust = red
        '#F44336'
        >>> trust_to_color(0.8, scheme="heat")
        '#E57373'
    """
    score = validate_trust_score(score)

    if scheme == "traffic":
        # Traffic light: red -> yellow -> green
        if score >= 0.7:
            return "#4CAF50"  # Green
        elif score >= 0.4:
            return "#FFEB3B"  # Yellow
        else:
            return "#F44336"  # Red

    elif scheme == "heat":
        # Blue (cold) -> Red (hot)
        if score >= 0.8:
            return "#E57373"  # Light red
        elif score >= 0.6:
            return "#FFB74D"  # Orange
        elif score >= 0.4:
            return "#FFF176"  # Yellow
        elif score >= 0.2:
            return "#81D4FA"  # Light blue
        else:
            return "#64B5F6"  # Blue

    elif scheme == "grayscale":
        # Black (0) -> White (1)
        gray_value = int(score * 255)
        hex_value = f"{gray_value:02X}"
        return f"#{hex_value}{hex_value}{hex_value}"

    else:
        # Default to traffic scheme
        return trust_to_color(score, scheme="traffic")


def trust_to_gradient_color(score: float) -> str:
    """Convert trust score to a smooth gradient color.

    Uses RGB interpolation for a smooth gradient from
    red (0.0) through yellow (0.5) to green (1.0).

    Args:
        score: Trust score (0.0 to 1.0)

    Returns:
        Hex color code

    Example:
        >>> trust_to_gradient_color(0.0)
        '#FF0000'  # Pure red
        >>> trust_to_gradient_color(0.5)
        '#FFFF00'  # Yellow
        >>> trust_to_gradient_color(1.0)
        '#00FF00'  # Pure green
    """
    score = validate_trust_score(score)

    if score < 0.5:
        # Red to Yellow (increase green)
        r = 255
        g = int(255 * (score * 2))
        b = 0
    else:
        # Yellow to Green (decrease red)
        r = int(255 * (1 - (score - 0.5) * 2))
        g = 255
        b = 0

    return f"#{r:02X}{g:02X}{b:02X}"


def format_trust(score: float, precision: int = 3) -> str:
    """Format trust score for display.

    Formats a trust score as a human-readable string
    with optional percentage representation.

    Args:
        score: Trust score (0.0 to 1.0)
        precision: Number of decimal places

    Returns:
        Formatted trust string

    Example:
        >>> format_trust(0.875)
        '0.875 (87.5%)'
        >>> format_trust(0.5, precision=1)
        '0.5 (50.0%)'
    """
    score = validate_trust_score(score)
    percentage = score * 100
    return f"{score:.{precision}f} ({percentage:.{precision-1}f}%)"


def merge_graphs(
    graphs: List["TemporalTrustGraph"],
    conflict_strategy: str = "average",
) -> "TemporalTrustGraph":
    """Merge multiple trust graphs into one.

    Combines nodes and edges from multiple graphs. When the same
    node or edge exists in multiple graphs, the conflict_strategy
    determines how to combine the trust scores.

    Args:
        graphs: List of graphs to merge
        conflict_strategy: How to handle conflicting trust scores:
            - "average": Use average of all scores
            - "max": Use maximum score
            - "min": Use minimum score
            - "first": Use score from first graph
            - "last": Use score from last graph

    Returns:
        New merged TemporalTrustGraph

    Raises:
        ValueError: If graphs list is empty

    Example:
        >>> from rotalabs_graph.temporal import TemporalTrustGraph
        >>> g1 = TemporalTrustGraph()
        >>> g1.add_node("agent-1", 0.8)
        >>> g2 = TemporalTrustGraph()
        >>> g2.add_node("agent-1", 0.6)
        >>> g2.add_node("agent-2", 0.9)
        >>> merged = merge_graphs([g1, g2], conflict_strategy="average")
        >>> merged.get_raw_trust("agent-1")
        0.7
    """
    from rotalabs_graph.temporal import TemporalTrustGraph

    if not graphs:
        raise ValueError("Cannot merge empty list of graphs")

    # Use first graph's config
    merged = TemporalTrustGraph(
        decay_function=graphs[0].decay_function,
        half_life_days=graphs[0].half_life,
        track_history=True,
    )

    # Collect all node trust scores
    node_scores: dict[str, list[float]] = {}
    node_metadata: dict[str, dict] = {}

    for graph in graphs:
        for node_id in graph.nodes:
            if node_id not in node_scores:
                node_scores[node_id] = []
                node_metadata[node_id] = {}
            node_scores[node_id].append(graph.get_raw_trust(node_id))
            # Merge metadata (later graphs override)
            node_metadata[node_id].update(graph._nodes[node_id].get("metadata", {}))

    # Add nodes with resolved trust
    for node_id, scores in node_scores.items():
        trust = _resolve_conflict(scores, conflict_strategy)
        merged.add_node(node_id, trust, metadata=node_metadata.get(node_id))

    # Collect all edge weights
    edge_weights: dict[tuple, list[float]] = {}
    edge_metadata: dict[tuple, dict] = {}

    for graph in graphs:
        for edge_key in graph.edges:
            if edge_key not in edge_weights:
                edge_weights[edge_key] = []
                edge_metadata[edge_key] = {}
            edge_weights[edge_key].append(graph._edges[edge_key]["weight"])
            edge_metadata[edge_key].update(graph._edges[edge_key].get("metadata", {}))

    # Add edges with resolved weights
    for edge_key, weights in edge_weights.items():
        source, target = edge_key
        # Only add edge if both nodes exist
        if source in merged and target in merged:
            weight = _resolve_conflict(weights, conflict_strategy)
            merged.add_edge(source, target, weight, metadata=edge_metadata.get(edge_key))

    return merged


def _resolve_conflict(values: List[float], strategy: str) -> float:
    """Resolve conflicting trust values."""
    if not values:
        return 0.5  # Default trust

    if strategy == "average":
        return sum(values) / len(values)
    elif strategy == "max":
        return max(values)
    elif strategy == "min":
        return min(values)
    elif strategy == "first":
        return values[0]
    elif strategy == "last":
        return values[-1]
    else:
        raise ValueError(f"Unknown conflict strategy: {strategy}")


def filter_by_trust(
    graph: "TemporalTrustGraph",
    min_trust: float = 0.0,
    max_trust: float = 1.0,
    include_edges: bool = True,
) -> "TemporalTrustGraph":
    """Create a subgraph with nodes in trust range.

    Filters nodes by their current (decayed) trust score and
    optionally includes edges between remaining nodes.

    Args:
        graph: Source graph to filter
        min_trust: Minimum trust threshold (inclusive)
        max_trust: Maximum trust threshold (inclusive)
        include_edges: Whether to copy edges between remaining nodes

    Returns:
        New TemporalTrustGraph with filtered nodes

    Example:
        >>> from rotalabs_graph.temporal import TemporalTrustGraph
        >>> graph = TemporalTrustGraph()
        >>> graph.add_node("high", 0.9)
        >>> graph.add_node("medium", 0.5)
        >>> graph.add_node("low", 0.2)
        >>> trusted = filter_by_trust(graph, min_trust=0.5)
        >>> trusted.nodes
        ['high', 'medium']
    """
    from rotalabs_graph.temporal import TemporalTrustGraph

    filtered = TemporalTrustGraph(
        decay_function=graph.decay_function,
        half_life_days=graph.half_life,
        track_history=graph.history is not None,
    )

    # Add nodes within trust range
    for node_id in graph.nodes:
        trust = graph.get_current_trust(node_id)
        if min_trust <= trust <= max_trust:
            filtered.add_node(
                node_id,
                graph.get_raw_trust(node_id),
                metadata=graph._nodes[node_id].get("metadata", {}),
            )

    # Add edges between remaining nodes
    if include_edges:
        for edge_key in graph.edges:
            source, target = edge_key
            if source in filtered and target in filtered:
                filtered.add_edge(
                    source,
                    target,
                    graph._edges[edge_key]["weight"],
                    metadata=graph._edges[edge_key].get("metadata", {}),
                )

    return filtered


def get_trust_statistics(graph: "TemporalTrustGraph") -> dict:
    """Calculate trust statistics for a graph.

    Args:
        graph: Graph to analyze

    Returns:
        Dictionary with trust statistics:
            - mean: Average trust score
            - median: Median trust score
            - min: Minimum trust score
            - max: Maximum trust score
            - std: Standard deviation
            - count: Number of nodes

    Example:
        >>> from rotalabs_graph.temporal import TemporalTrustGraph
        >>> graph = TemporalTrustGraph()
        >>> graph.add_node("a", 0.9)
        >>> graph.add_node("b", 0.5)
        >>> graph.add_node("c", 0.2)
        >>> stats = get_trust_statistics(graph)
        >>> stats["mean"]
        0.533...
    """
    if not graph.nodes:
        return {
            "mean": 0.0,
            "median": 0.0,
            "min": 0.0,
            "max": 0.0,
            "std": 0.0,
            "count": 0,
        }

    scores = [graph.get_current_trust(node_id) for node_id in graph.nodes]
    scores.sort()

    n = len(scores)
    mean = sum(scores) / n

    if n % 2 == 0:
        median = (scores[n // 2 - 1] + scores[n // 2]) / 2
    else:
        median = scores[n // 2]

    variance = sum((s - mean) ** 2 for s in scores) / n
    std = variance ** 0.5

    return {
        "mean": mean,
        "median": median,
        "min": min(scores),
        "max": max(scores),
        "std": std,
        "count": n,
    }


def partition_by_trust(
    graph: "TemporalTrustGraph",
    thresholds: List[float] = None,
) -> dict:
    """Partition nodes into trust tiers.

    Args:
        graph: Graph to partition
        thresholds: Trust boundaries for tiers (default: [0.3, 0.7])

    Returns:
        Dictionary mapping tier names to node ID lists:
            - "low": trust < first threshold
            - "medium": first threshold <= trust < second threshold
            - "high": trust >= second threshold

    Example:
        >>> from rotalabs_graph.temporal import TemporalTrustGraph
        >>> graph = TemporalTrustGraph()
        >>> graph.add_node("trusted", 0.9)
        >>> graph.add_node("neutral", 0.5)
        >>> graph.add_node("untrusted", 0.1)
        >>> tiers = partition_by_trust(graph)
        >>> tiers["high"]
        ['trusted']
    """
    if thresholds is None:
        thresholds = [0.3, 0.7]

    if len(thresholds) != 2:
        raise ValueError("Expected exactly 2 thresholds")

    low_threshold, high_threshold = sorted(thresholds)

    partitions = {
        "low": [],
        "medium": [],
        "high": [],
    }

    for node_id in graph.nodes:
        trust = graph.get_current_trust(node_id)
        if trust < low_threshold:
            partitions["low"].append(node_id)
        elif trust >= high_threshold:
            partitions["high"].append(node_id)
        else:
            partitions["medium"].append(node_id)

    return partitions
