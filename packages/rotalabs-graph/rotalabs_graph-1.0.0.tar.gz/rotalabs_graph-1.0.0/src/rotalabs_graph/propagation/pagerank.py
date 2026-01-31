"""PageRank-style trust propagation."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

import networkx as nx

from rotalabs_graph.core.config import PropagationConfig
from rotalabs_graph.core.exceptions import ConvergenceError, PropagationError
from rotalabs_graph.core.graph import TrustGraph
from rotalabs_graph.core.types import TrustScore

from .base import BasePropagator


class PageRankPropagator(BasePropagator):
    """Trust propagation using PageRank algorithm.

    PageRank treats trust as "voting" - nodes pass trust to their
    neighbors, with damping to ensure convergence. This is the classic
    algorithm used by Google for web page ranking, adapted here for
    trust propagation in entity graphs.

    Trust equation:
        T(v) = (1-d)/N + d * sum(T(u) * w(u,v) / out_degree(u))

    Where:
        - d is the damping factor (default 0.85)
        - N is the number of nodes
        - w(u,v) is the edge weight from u to v
        - out_degree(u) is the weighted out-degree of u

    The damping factor represents the probability that a random walker
    follows an edge vs. jumping to a random node. Higher damping means
    more influence from the graph structure.

    Example:
        >>> propagator = PageRankPropagator(damping=0.85)
        >>> scores = propagator.propagate(graph)
        >>> print(scores["model-a"].value)
        0.342

        >>> # Personalized PageRank from specific node
        >>> scores = propagator.propagate_from(graph, "trusted-authority")
        >>> # Nodes closer to trusted-authority will have higher scores
    """

    def __init__(
        self,
        config: Optional[PropagationConfig] = None,
        damping: Optional[float] = None,
    ) -> None:
        """Initialize PageRank propagator.

        Args:
            config: Propagation configuration
            damping: Damping factor (overrides config.damping if provided)
        """
        super().__init__(config)
        if damping is not None:
            if not 0.0 <= damping <= 1.0:
                raise ValueError(f"Damping must be in [0, 1], got {damping}")
            self.config.damping = damping

    def propagate(
        self,
        graph: TrustGraph,
        source_nodes: Optional[List[str]] = None,
    ) -> Dict[str, TrustScore]:
        """Propagate trust using PageRank algorithm.

        Computes the stationary distribution of trust values across all
        nodes in the graph.

        Args:
            graph: The trust graph
            source_nodes: If provided, only these nodes start with initial trust.
                         This creates a biased/personalized PageRank.

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        self._validate_graph(graph)
        self.last_run_time = datetime.now()

        nx_graph = graph.nx_graph

        # Prepare personalization vector if source nodes specified
        personalization = None
        if source_nodes:
            # Validate source nodes exist
            for node_id in source_nodes:
                self._validate_source(graph, node_id)

            # Create personalization vector
            personalization = {node_id: 0.0 for node_id in graph.node_ids()}
            weight_per_source = 1.0 / len(source_nodes)
            for node_id in source_nodes:
                personalization[node_id] = weight_per_source

        # Use node's initial trust as starting values
        nstart = None
        initial_scores = self._get_initial_scores(graph)
        if any(v != self.config.initial_trust for v in initial_scores.values()):
            # Normalize to sum to 1
            total = sum(initial_scores.values())
            if total > 0:
                nstart = {k: v / total for k, v in initial_scores.items()}

        try:
            # Run PageRank with edge weights
            scores = nx.pagerank(
                nx_graph,
                alpha=self.config.damping,
                personalization=personalization,
                max_iter=self.config.max_iterations,
                tol=self.config.convergence_threshold,
                nstart=nstart,
                weight="weight" if self.config.use_edge_weights else None,
            )
        except nx.PowerIterationFailedConvergence as e:
            raise ConvergenceError(
                iterations=self.config.max_iterations,
                delta=float("inf"),
                threshold=self.config.convergence_threshold,
            ) from e

        # Post-process scores
        if self.config.normalize:
            scores = self._normalize_scores(scores)

        scores = self._clamp_scores(scores)

        # Convert to TrustScore objects
        return self._scores_to_trust_scores(
            scores,
            source="pagerank",
            confidence=self._compute_confidence(graph, scores),
        )

    def propagate_from(
        self,
        graph: TrustGraph,
        source_id: str,
    ) -> Dict[str, TrustScore]:
        """Propagate trust from a single source using Personalized PageRank.

        Computes trust scores relative to a specific source node. Nodes
        that are closer (in terms of graph distance and edge weights)
        to the source will have higher trust scores.

        This is also known as "Personalized PageRank" or "Topic-Sensitive
        PageRank".

        Args:
            graph: The trust graph
            source_id: ID of the source node

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        self._validate_graph(graph)
        self._validate_source(graph, source_id)
        self.last_run_time = datetime.now()

        nx_graph = graph.nx_graph

        # Create personalization vector with all weight on source
        personalization = {node_id: 0.0 for node_id in graph.node_ids()}
        personalization[source_id] = 1.0

        try:
            scores = nx.pagerank(
                nx_graph,
                alpha=self.config.damping,
                personalization=personalization,
                max_iter=self.config.max_iterations,
                tol=self.config.convergence_threshold,
                weight="weight" if self.config.use_edge_weights else None,
            )
        except nx.PowerIterationFailedConvergence as e:
            raise ConvergenceError(
                iterations=self.config.max_iterations,
                delta=float("inf"),
                threshold=self.config.convergence_threshold,
            ) from e

        # Post-process scores
        if self.config.normalize:
            scores = self._normalize_scores(scores)

        scores = self._clamp_scores(scores)

        return self._scores_to_trust_scores(
            scores,
            source=f"pagerank_from_{source_id}",
            confidence=self._compute_confidence(graph, scores),
        )

    def _compute_confidence(
        self,
        graph: TrustGraph,
        scores: Dict[str, float],
    ) -> float:
        """Compute confidence in the PageRank results.

        Confidence is based on graph connectivity - a well-connected graph
        produces more reliable results.

        Args:
            graph: The trust graph
            scores: Computed scores

        Returns:
            Confidence value in [0, 1]
        """
        if graph.num_nodes == 0:
            return 0.0

        # Base confidence on edge density
        max_edges = graph.num_nodes * (graph.num_nodes - 1)
        if max_edges == 0:
            return 0.5

        density = graph.num_edges / max_edges

        # Also consider variance in scores (uniform scores = less informative)
        if scores:
            values = list(scores.values())
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            # Higher variance = more differentiation = higher confidence
            variance_factor = min(1.0, variance * 10)  # Scale variance contribution
        else:
            variance_factor = 0.5

        # Combine factors
        confidence = 0.5 * density + 0.5 * variance_factor
        return min(1.0, max(0.0, confidence))
