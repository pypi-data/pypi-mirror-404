"""Base class for trust propagation algorithms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from rotalabs_graph.core.config import PropagationConfig
from rotalabs_graph.core.exceptions import PropagationError
from rotalabs_graph.core.graph import TrustGraph
from rotalabs_graph.core.types import TrustScore


class BasePropagator(ABC):
    """Base class for trust propagation algorithms.

    All propagation algorithms should inherit from this class and implement
    the `propagate` and `propagate_from` methods.

    Attributes:
        config: Configuration for the propagation algorithm
        last_run_time: Timestamp of the last propagation run
        last_iterations: Number of iterations in the last run (for iterative algorithms)

    Example:
        >>> class MyPropagator(BasePropagator):
        ...     def propagate(self, graph, source_nodes=None):
        ...         # Custom implementation
        ...         pass
        ...     def propagate_from(self, graph, source_id):
        ...         # Custom implementation
        ...         pass
    """

    def __init__(self, config: Optional[PropagationConfig] = None) -> None:
        """Initialize the propagator.

        Args:
            config: Configuration for the propagation algorithm.
                   If None, uses default PropagationConfig.
        """
        self.config = config or PropagationConfig()
        self.last_run_time: Optional[datetime] = None
        self.last_iterations: Optional[int] = None

    @abstractmethod
    def propagate(
        self,
        graph: TrustGraph,
        source_nodes: Optional[List[str]] = None,
    ) -> Dict[str, TrustScore]:
        """Propagate trust through the graph.

        This is the main method for computing trust scores for all nodes
        in the graph based on the graph structure and edge weights.

        Args:
            graph: The trust graph to propagate through
            source_nodes: Optional list of source node IDs to start from.
                         If None, all nodes are considered as potential sources.

        Returns:
            Dictionary mapping node_id to computed TrustScore

        Raises:
            PropagationError: If propagation fails (e.g., empty graph)
        """
        pass

    @abstractmethod
    def propagate_from(
        self,
        graph: TrustGraph,
        source_id: str,
    ) -> Dict[str, TrustScore]:
        """Propagate trust from a single source node.

        Computes trust scores relative to a specific source node,
        useful for personalized trust computation.

        Args:
            graph: The trust graph to propagate through
            source_id: ID of the source node to propagate from

        Returns:
            Dictionary mapping node_id to computed TrustScore

        Raises:
            PropagationError: If propagation fails
            KeyError: If source_id is not in the graph
        """
        pass

    def _validate_graph(self, graph: TrustGraph) -> None:
        """Validate graph before propagation.

        Args:
            graph: The graph to validate

        Raises:
            PropagationError: If the graph is invalid for propagation
        """
        if graph.num_nodes == 0:
            raise PropagationError("Cannot propagate on empty graph")

    def _validate_source(self, graph: TrustGraph, source_id: str) -> None:
        """Validate that a source node exists in the graph.

        Args:
            graph: The graph to check
            source_id: ID of the source node

        Raises:
            PropagationError: If the source node doesn't exist
        """
        if not graph.has_node(source_id):
            raise PropagationError(f"Source node '{source_id}' not found in graph")

    def _normalize_scores(
        self, scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Normalize scores to [0, 1] range.

        Args:
            scores: Dictionary of raw scores

        Returns:
            Dictionary of normalized scores
        """
        if not scores:
            return scores

        values = list(scores.values())
        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            # All scores are the same, return 0.5 for all
            return {k: 0.5 for k in scores}

        return {
            k: (v - min_val) / (max_val - min_val)
            for k, v in scores.items()
        }

    def _clamp_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Clamp scores to configured min/max bounds.

        Args:
            scores: Dictionary of scores

        Returns:
            Dictionary of clamped scores
        """
        return {
            k: max(self.config.min_trust, min(self.config.max_trust, v))
            for k, v in scores.items()
        }

    def _scores_to_trust_scores(
        self,
        scores: Dict[str, float],
        source: str,
        confidence: float = 1.0,
    ) -> Dict[str, TrustScore]:
        """Convert raw scores to TrustScore objects.

        Args:
            scores: Dictionary of raw scores
            source: Source identifier for the scores
            confidence: Confidence level for all scores

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        timestamp = datetime.now()
        return {
            node_id: TrustScore(
                value=score,
                confidence=confidence,
                source=source,
                timestamp=timestamp,
            )
            for node_id, score in scores.items()
        }

    def _get_initial_scores(self, graph: TrustGraph) -> Dict[str, float]:
        """Get initial trust scores from graph nodes.

        Uses node's base_trust if set, otherwise uses config.base_trust.

        Args:
            graph: The trust graph

        Returns:
            Dictionary of initial scores
        """
        scores = {}
        for node_id in graph.node_ids():
            node = graph.get_node(node_id)
            if node and node.base_trust is not None:
                scores[node_id] = node.base_trust
            else:
                scores[node_id] = self.config.base_trust
        return scores

    def apply_to_graph(
        self,
        graph: TrustGraph,
        source_nodes: Optional[List[str]] = None,
    ) -> TrustGraph:
        """Propagate trust and store results in the graph.

        Convenience method that propagates trust and updates the graph's
        trust scores in place.

        Args:
            graph: The trust graph (will be modified)
            source_nodes: Optional list of source nodes

        Returns:
            The same graph with updated trust scores
        """
        scores = self.propagate(graph, source_nodes)
        for node_id, score in scores.items():
            graph.set_trust_score(node_id, score)
        return graph
