"""Core data types for rotalabs-graph.

This module defines the fundamental data structures for representing
trust graphs, including nodes, edges, trust scores, and paths.

Example:
    >>> from rotalabs_graph.core.types import TrustNode, TrustEdge, NodeType, EdgeType
    >>> node = TrustNode(
    ...     id="model-gpt4",
    ...     name="GPT-4",
    ...     node_type=NodeType.MODEL,
    ...     base_trust=0.95
    ... )
    >>> edge = TrustEdge(
    ...     source_id="agent-1",
    ...     target_id="model-gpt4",
    ...     edge_type=EdgeType.TRUSTS,
    ...     weight=0.9
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(str, Enum):
    """Types of nodes in a trust graph.

    Each node type represents a different entity in an AI system
    that can participate in trust relationships.

    Attributes:
        MODEL: An AI/ML model (e.g., GPT-4, Claude).
        AGENT: An autonomous agent that can take actions.
        USER: A human user interacting with the system.
        DATA_SOURCE: A source of data (e.g., database, API).
        TOOL: A tool or function that agents can use.
        SERVICE: An external service or microservice.

    Example:
        >>> node_type = NodeType.MODEL
        >>> print(node_type.value)
        'model'
        >>> node_type == "model"
        True
    """

    MODEL = "model"
    AGENT = "agent"
    USER = "user"
    DATA_SOURCE = "data_source"
    TOOL = "tool"
    SERVICE = "service"


class EdgeType(str, Enum):
    """Types of edges (relationships) in a trust graph.

    Each edge type represents a different kind of trust or
    dependency relationship between nodes.

    Attributes:
        TRUSTS: Source trusts target (general trust relationship).
        DELEGATES: Source delegates authority to target.
        VERIFIES: Source verifies/validates target's outputs.
        VALIDATES: Source validates target's behavior.
        DEPENDS_ON: Source depends on target for functionality.
        CALLS: Source calls/invokes target.
        OWNS: Source owns/controls target.

    Example:
        >>> edge_type = EdgeType.TRUSTS
        >>> print(edge_type.value)
        'trusts'
    """

    TRUSTS = "trusts"
    DELEGATES = "delegates"
    VERIFIES = "verifies"
    VALIDATES = "validates"
    DEPENDS_ON = "depends_on"
    CALLS = "calls"
    OWNS = "owns"


class AggregationMethod(str, Enum):
    """Methods for aggregating multiple trust scores.

    Attributes:
        MEAN: Average of all scores.
        MAX: Maximum score.
        MIN: Minimum score.
        PRODUCT: Product of all scores.
        WEIGHTED_MEAN: Weighted average of scores.
        HARMONIC_MEAN: Harmonic mean of scores.

    Example:
        >>> method = AggregationMethod.MEAN
        >>> scores = [0.8, 0.9, 0.7]
        >>> result = aggregate_scores(scores, method)
    """

    MEAN = "mean"
    MAX = "max"
    MIN = "min"
    PRODUCT = "product"
    WEIGHTED_MEAN = "weighted_mean"
    HARMONIC_MEAN = "harmonic_mean"


def _now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class TrustNode:
    """A node in the trust graph representing an entity.

    Each node has an intrinsic base trust score and can participate
    in trust relationships with other nodes via edges.

    Attributes:
        id: Unique identifier for the node.
        name: Human-readable name for the node.
        node_type: The type of entity this node represents.
        base_trust: Intrinsic trust score (0-1). This represents the
            node's inherent trustworthiness before considering
            relationships with other nodes. Default: 1.0.
        metadata: Arbitrary key-value metadata for the node.
        created_at: When the node was created.
        updated_at: When the node was last updated.

    Example:
        >>> node = TrustNode(
        ...     id="model-gpt4",
        ...     name="GPT-4",
        ...     node_type=NodeType.MODEL,
        ...     base_trust=0.95,
        ...     metadata={"provider": "openai", "version": "4.0"}
        ... )
        >>> print(f"{node.name} has base trust {node.base_trust}")
        GPT-4 has base trust 0.95
    """

    id: str
    name: str
    node_type: NodeType
    base_trust: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        """Validate node data after initialization."""
        if not self.id:
            raise ValueError("Node id cannot be empty")
        if not self.name:
            raise ValueError("Node name cannot be empty")
        if not 0 <= self.base_trust <= 1:
            raise ValueError(f"base_trust must be between 0 and 1, got {self.base_trust}")
        # Convert string to enum if necessary
        if isinstance(self.node_type, str):
            self.node_type = NodeType(self.node_type)

    def __hash__(self) -> int:
        """Return hash of node ID for use in sets and dicts."""
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        """Check equality based on node ID."""
        if not isinstance(other, TrustNode):
            return False
        return self.id == other.id

    def update(self, **kwargs: Any) -> "TrustNode":
        """Create an updated copy of this node.

        Args:
            **kwargs: Fields to update.

        Returns:
            A new TrustNode with the specified fields updated.

        Example:
            >>> updated = node.update(base_trust=0.8, name="GPT-4 Turbo")
        """
        data = {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type,
            "base_trust": self.base_trust,
            "metadata": self.metadata.copy(),
            "created_at": self.created_at,
            "updated_at": _now(),
        }
        data.update(kwargs)
        return TrustNode(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation.

        Returns:
            Dictionary with all node fields.

        Example:
            >>> data = node.to_dict()
            >>> print(data["id"])
            'model-gpt4'
        """
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type.value,
            "base_trust": self.base_trust,
            "metadata": self.metadata.copy(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustNode":
        """Create a TrustNode from a dictionary.

        Args:
            data: Dictionary with node fields.

        Returns:
            A new TrustNode instance.

        Example:
            >>> data = {"id": "model-1", "name": "Test", "node_type": "model"}
            >>> node = TrustNode.from_dict(data)
        """
        # Parse datetime strings if present
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = _now()

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        elif updated_at is None:
            updated_at = _now()

        return cls(
            id=data["id"],
            name=data["name"],
            node_type=NodeType(data["node_type"]),
            base_trust=data.get("base_trust", 1.0),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class TrustEdge:
    """An edge in the trust graph representing a relationship.

    Edges connect two nodes and represent trust or dependency
    relationships between them.

    Attributes:
        source_id: ID of the source node.
        target_id: ID of the target node.
        edge_type: The type of relationship.
        weight: Trust weight (0-1). Higher values indicate stronger
            trust. Default: 1.0.
        metadata: Arbitrary key-value metadata for the edge.
        created_at: When the edge was created.

    Example:
        >>> edge = TrustEdge(
        ...     source_id="agent-1",
        ...     target_id="model-gpt4",
        ...     edge_type=EdgeType.TRUSTS,
        ...     weight=0.9,
        ...     metadata={"reason": "verified outputs"}
        ... )
        >>> print(f"{edge.source_id} --[{edge.edge_type.value}]--> {edge.target_id}")
        agent-1 --[trusts]--> model-gpt4
    """

    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        """Validate edge data after initialization."""
        if not self.source_id:
            raise ValueError("Edge source_id cannot be empty")
        if not self.target_id:
            raise ValueError("Edge target_id cannot be empty")
        if not 0 <= self.weight <= 1:
            raise ValueError(f"weight must be between 0 and 1, got {self.weight}")
        # Convert string to enum if necessary
        if isinstance(self.edge_type, str):
            self.edge_type = EdgeType(self.edge_type)

    def __hash__(self) -> int:
        """Return hash for use in sets and dicts."""
        return hash((self.source_id, self.target_id, self.edge_type))

    @property
    def edge_id(self) -> str:
        """Generate a unique ID for this edge.

        Returns:
            String ID combining source, target, and type.
        """
        return f"{self.source_id}|{self.edge_type.value}|{self.target_id}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary representation.

        Returns:
            Dictionary with all edge fields.
        """
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "metadata": self.metadata.copy(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustEdge":
        """Create a TrustEdge from a dictionary.

        Args:
            data: Dictionary with edge fields.

        Returns:
            A new TrustEdge instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = _now()

        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            edge_type=EdgeType(data["edge_type"]),
            weight=data.get("weight", 1.0),
            metadata=data.get("metadata", {}),
            created_at=created_at,
        )


@dataclass
class TrustScore:
    """A computed trust score for a node.

    Trust scores are computed by propagation algorithms and represent
    the overall trustworthiness of a node considering its relationships.

    Attributes:
        node_id: ID of the node this score is for.
        score: Computed trust score (0-1).
        confidence: Confidence in the score (0-1). Higher values indicate
            more reliable scores (e.g., more paths contributing).
        path_count: Number of paths contributing to this score.
        computation_method: Name of the algorithm used to compute the score.
        computed_at: When the score was computed.

    Example:
        >>> score = TrustScore(
        ...     node_id="model-gpt4",
        ...     score=0.87,
        ...     confidence=0.95,
        ...     path_count=15,
        ...     computation_method="pagerank"
        ... )
        >>> print(f"Trust: {score.score:.2f} (confidence: {score.confidence:.2f})")
        Trust: 0.87 (confidence: 0.95)
    """

    node_id: str
    score: float
    confidence: float
    path_count: int
    computation_method: str
    computed_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        """Validate score data after initialization."""
        if not self.node_id:
            raise ValueError("TrustScore node_id cannot be empty")
        if not 0 <= self.score <= 1:
            raise ValueError(f"score must be between 0 and 1, got {self.score}")
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"confidence must be between 0 and 1, got {self.confidence}")
        if self.path_count < 0:
            raise ValueError(f"path_count must be non-negative, got {self.path_count}")

    def weighted_value(self) -> float:
        """Return score weighted by confidence.

        Returns:
            Score multiplied by confidence.
        """
        return self.score * self.confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert score to dictionary representation.

        Returns:
            Dictionary with all score fields.
        """
        return {
            "node_id": self.node_id,
            "score": self.score,
            "confidence": self.confidence,
            "path_count": self.path_count,
            "computation_method": self.computation_method,
            "computed_at": self.computed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustScore":
        """Create a TrustScore from a dictionary.

        Args:
            data: Dictionary with score fields.

        Returns:
            A new TrustScore instance.
        """
        computed_at = data.get("computed_at")
        if isinstance(computed_at, str):
            computed_at = datetime.fromisoformat(computed_at.replace("Z", "+00:00"))
        elif computed_at is None:
            computed_at = _now()

        return cls(
            node_id=data["node_id"],
            score=data["score"],
            confidence=data["confidence"],
            path_count=data["path_count"],
            computation_method=data["computation_method"],
            computed_at=computed_at,
        )


@dataclass
class TrustPath:
    """A path through the trust graph.

    Represents a sequence of nodes and edges connecting them,
    along with the combined trust along the path.

    Attributes:
        nodes: List of node IDs in the path, in order.
        edges: List of edge IDs in the path, in order.
        path_trust: Combined trust score along the entire path.
            Typically computed as the product of edge weights.
        length: Number of hops (edges) in the path.

    Example:
        >>> path = TrustPath(
        ...     nodes=["user-1", "agent-1", "model-gpt4"],
        ...     edges=["user-1|trusts|agent-1", "agent-1|calls|model-gpt4"],
        ...     path_trust=0.81,  # 0.9 * 0.9
        ...     length=2
        ... )
        >>> print(f"Path of length {path.length}: {' -> '.join(path.nodes)}")
        Path of length 2: user-1 -> agent-1 -> model-gpt4
    """

    nodes: List[str]
    edges: List[str]
    path_trust: float
    length: int

    def __post_init__(self) -> None:
        """Validate path data after initialization."""
        if len(self.nodes) < 2:
            raise ValueError("Path must have at least 2 nodes")
        if len(self.edges) != len(self.nodes) - 1:
            raise ValueError(
                f"Number of edges ({len(self.edges)}) must be one less than "
                f"number of nodes ({len(self.nodes)})"
            )
        if self.length != len(self.edges):
            raise ValueError(
                f"length ({self.length}) must equal number of edges ({len(self.edges)})"
            )
        if not 0 <= self.path_trust <= 1:
            raise ValueError(f"path_trust must be between 0 and 1, got {self.path_trust}")

    @property
    def source(self) -> str:
        """Get the source node ID (first node in path).

        Returns:
            ID of the first node.
        """
        return self.nodes[0]

    @property
    def target(self) -> str:
        """Get the target node ID (last node in path).

        Returns:
            ID of the last node.
        """
        return self.nodes[-1]

    def to_dict(self) -> Dict[str, Any]:
        """Convert path to dictionary representation.

        Returns:
            Dictionary with all path fields.
        """
        return {
            "nodes": self.nodes.copy(),
            "edges": self.edges.copy(),
            "path_trust": self.path_trust,
            "length": self.length,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustPath":
        """Create a TrustPath from a dictionary.

        Args:
            data: Dictionary with path fields.

        Returns:
            A new TrustPath instance.
        """
        return cls(
            nodes=data["nodes"],
            edges=data["edges"],
            path_trust=data["path_trust"],
            length=data["length"],
        )


@dataclass
class PropagationResult:
    """Result of a trust propagation computation.

    Contains all computed trust scores and metadata about the
    propagation process.

    Attributes:
        scores: Mapping from node ID to TrustScore.
        converged: Whether the algorithm converged.
        iterations: Number of iterations performed.
        final_delta: Maximum change in the final iteration.
        computation_time_ms: Time taken in milliseconds.
        method: Name of the propagation method used.
        computed_at: When the computation was performed.

    Example:
        >>> result = propagator.compute_trust(graph)
        >>> if result.converged:
        ...     for node_id, score in result.scores.items():
        ...         print(f"{node_id}: {score.score:.3f}")
        ... else:
        ...     print(f"Did not converge after {result.iterations} iterations")
    """

    scores: Dict[str, TrustScore]
    converged: bool
    iterations: int
    final_delta: float
    computation_time_ms: float
    method: str
    computed_at: datetime = field(default_factory=_now)

    def get_score(self, node_id: str) -> Optional[TrustScore]:
        """Get the trust score for a specific node.

        Args:
            node_id: ID of the node.

        Returns:
            TrustScore for the node, or None if not found.
        """
        return self.scores.get(node_id)

    def get_top_k(self, k: int = 10, reverse: bool = True) -> List[TrustScore]:
        """Get the top k nodes by trust score.

        Args:
            k: Number of nodes to return.
            reverse: If True, return highest scores first.

        Returns:
            List of TrustScore objects, sorted by score.
        """
        sorted_scores = sorted(
            self.scores.values(),
            key=lambda s: s.score,
            reverse=reverse,
        )
        return sorted_scores[:k]

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation.

        Returns:
            Dictionary with all result fields.
        """
        return {
            "scores": {k: v.to_dict() for k, v in self.scores.items()},
            "converged": self.converged,
            "iterations": self.iterations,
            "final_delta": self.final_delta,
            "computation_time_ms": self.computation_time_ms,
            "method": self.method,
            "computed_at": self.computed_at.isoformat(),
        }


def aggregate_scores(
    scores: List[float],
    method: AggregationMethod = AggregationMethod.MEAN,
    weights: Optional[List[float]] = None,
) -> float:
    """Aggregate multiple trust scores using the specified method.

    Args:
        scores: List of scores to aggregate.
        method: Aggregation method to use.
        weights: Optional weights for weighted aggregation.

    Returns:
        Aggregated score.

    Example:
        >>> scores = [0.8, 0.9, 0.7]
        >>> aggregate_scores(scores, AggregationMethod.MEAN)
        0.8
        >>> aggregate_scores(scores, AggregationMethod.MAX)
        0.9
    """
    if not scores:
        return 0.0

    if method == AggregationMethod.MEAN:
        return sum(scores) / len(scores)

    elif method == AggregationMethod.MAX:
        return max(scores)

    elif method == AggregationMethod.MIN:
        return min(scores)

    elif method == AggregationMethod.PRODUCT:
        result = 1.0
        for s in scores:
            result *= s
        return result

    elif method == AggregationMethod.WEIGHTED_MEAN:
        if weights is None:
            weights = [1.0] * len(scores)
        if len(weights) != len(scores):
            raise ValueError("Weights must match scores length")
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        return sum(s * w for s, w in zip(scores, weights)) / total_weight

    elif method == AggregationMethod.HARMONIC_MEAN:
        # Avoid division by zero
        non_zero = [s for s in scores if s > 0]
        if not non_zero:
            return 0.0
        return len(non_zero) / sum(1.0 / s for s in non_zero)

    else:
        raise ValueError(f"Unknown aggregation method: {method}")
