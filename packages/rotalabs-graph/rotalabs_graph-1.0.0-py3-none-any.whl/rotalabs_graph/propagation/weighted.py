"""Simple weighted trust propagation with decay."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from rotalabs_graph.core.config import PropagationConfig
from rotalabs_graph.core.exceptions import PropagationError
from rotalabs_graph.core.graph import TrustGraph
from rotalabs_graph.core.types import AggregationMethod, TrustScore, aggregate_scores

from .base import BasePropagator


class WeightedPropagator(BasePropagator):
    """Simple weighted trust propagation with decay.

    This propagator uses a straightforward approach where trust decays
    with each hop through the graph:

        T(source -> target) = T(source) * edge_weight * (1 - decay)^hops

    Multiple paths between source and target are aggregated using the
    configured aggregation method (mean, max, min, product).

    This is a simpler alternative to PageRank/EigenTrust that provides
    more interpretable results and direct control over propagation behavior.

    Attributes:
        decay: Trust decay per hop (0 = no decay, 1 = full decay)
        aggregation: Method for combining multiple path scores

    Example:
        >>> propagator = WeightedPropagator(decay=0.1, aggregation="max")
        >>> scores = propagator.propagate_from(graph, "trusted-source")
        >>> print(scores["target-node"].value)
        0.72

        >>> # Using mean aggregation for multiple paths
        >>> propagator = WeightedPropagator(decay=0.2, aggregation="mean")
        >>> scores = propagator.propagate(graph)
    """

    def __init__(
        self,
        config: Optional[PropagationConfig] = None,
        decay: Optional[float] = None,
        aggregation: Optional[AggregationMethod] = None,
    ) -> None:
        """Initialize weighted propagator.

        Args:
            config: Propagation configuration
            decay: Trust decay per hop (overrides config.decay)
            aggregation: Aggregation method (overrides config.aggregation)
        """
        super().__init__(config)

        if decay is not None:
            if not 0.0 <= decay <= 1.0:
                raise ValueError(f"Decay must be in [0, 1], got {decay}")
            self.config.decay = decay

        if aggregation is not None:
            if isinstance(aggregation, str):
                aggregation = AggregationMethod(aggregation)
            self.config.aggregation = aggregation

    def propagate(
        self,
        graph: TrustGraph,
        source_nodes: Optional[List[str]] = None,
    ) -> Dict[str, TrustScore]:
        """Propagate trust from multiple source nodes.

        If source_nodes is not provided, nodes with initial_trust set
        are used as sources. If no nodes have initial_trust, all nodes
        are used as potential sources.

        Args:
            graph: The trust graph
            source_nodes: Optional list of source node IDs

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        self._validate_graph(graph)
        self.last_run_time = datetime.now()

        # Determine source nodes
        if source_nodes is None:
            # Use nodes with initial trust as sources
            source_nodes = [
                n.node_id for n in graph.nodes()
                if n.initial_trust is not None and n.initial_trust > 0
            ]

            # If no initial trust nodes, use all nodes
            if not source_nodes:
                source_nodes = graph.node_ids()

        # Validate sources
        for source_id in source_nodes:
            self._validate_source(graph, source_id)

        # Propagate from each source and aggregate
        all_scores: Dict[str, List[float]] = defaultdict(list)

        for source_id in source_nodes:
            source_node = graph.get_node(source_id)
            source_trust = (
                source_node.base_trust
                if source_node and source_node.base_trust is not None
                else self.config.initial_trust
            )

            # Run BFS propagation from this source
            path_scores = self._bfs_propagate(graph, source_id, source_trust)

            for node_id, score in path_scores.items():
                all_scores[node_id].append(score)

        # Aggregate scores from all sources
        final_scores = {}
        for node_id, scores in all_scores.items():
            final_scores[node_id] = self._aggregate_scores(scores)

        # Ensure all nodes have a score
        for node_id in graph.node_ids():
            if node_id not in final_scores:
                # Unreachable node gets minimum trust
                final_scores[node_id] = self.config.min_trust

        # Post-process
        if self.config.normalize:
            final_scores = self._normalize_scores(final_scores)

        final_scores = self._clamp_scores(final_scores)

        return self._scores_to_trust_scores(
            final_scores,
            source="weighted",
            confidence=self._compute_confidence(graph, source_nodes),
        )

    def propagate_from(
        self,
        graph: TrustGraph,
        source_id: str,
    ) -> Dict[str, TrustScore]:
        """Propagate trust from a single source node.

        Args:
            graph: The trust graph
            source_id: ID of the source node

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        self._validate_graph(graph)
        self._validate_source(graph, source_id)
        self.last_run_time = datetime.now()

        # Get source trust value
        source_node = graph.get_node(source_id)
        source_trust = (
            source_node.base_trust
            if source_node and source_node.base_trust is not None
            else 1.0  # Full trust for single-source propagation
        )

        # Run BFS propagation
        scores = self._bfs_propagate(graph, source_id, source_trust)

        # Ensure all nodes have a score
        for node_id in graph.node_ids():
            if node_id not in scores:
                scores[node_id] = 0.0  # Unreachable from source

        # Post-process
        if self.config.normalize:
            scores = self._normalize_scores(scores)

        scores = self._clamp_scores(scores)

        return self._scores_to_trust_scores(
            scores,
            source=f"weighted_from_{source_id}",
            confidence=self._compute_confidence(graph, [source_id]),
        )

    def _bfs_propagate(
        self,
        graph: TrustGraph,
        source_id: str,
        source_trust: float,
    ) -> Dict[str, float]:
        """Propagate trust using breadth-first search.

        Explores all paths up to max_depth and tracks the best score
        for each node (multiple paths are aggregated).

        Args:
            graph: The trust graph
            source_id: Starting node ID
            source_trust: Initial trust value at source

        Returns:
            Dictionary mapping node_id to propagated trust score
        """
        # Track scores for each node (may receive from multiple paths)
        node_scores: Dict[str, List[float]] = defaultdict(list)

        # Source always has its trust value
        node_scores[source_id].append(source_trust)

        # BFS queue: (node_id, current_trust, depth)
        queue: deque = deque([(source_id, source_trust, 0)])
        # Track visited at each depth to allow multiple paths
        visited_at_depth: Dict[str, int] = {source_id: 0}

        decay_factor = 1.0 - self.config.decay

        while queue:
            current_id, current_trust, depth = queue.popleft()

            # Stop if max depth reached
            if depth >= self.config.max_depth:
                continue

            # Explore neighbors
            for neighbor_id in graph.neighbors(current_id):
                edge = graph.get_edge(current_id, neighbor_id)
                if edge is None:
                    continue

                # Calculate propagated trust
                edge_weight = edge.weight if self.config.use_edge_weights else 1.0
                propagated_trust = current_trust * edge_weight * decay_factor

                # Skip if trust is negligible
                if propagated_trust < 1e-10:
                    continue

                # Record this score
                node_scores[neighbor_id].append(propagated_trust)

                # Only continue BFS if we haven't visited at this depth
                # or if we're finding a better path
                new_depth = depth + 1
                prev_depth = visited_at_depth.get(neighbor_id, float("inf"))

                if new_depth <= prev_depth:
                    visited_at_depth[neighbor_id] = new_depth
                    queue.append((neighbor_id, propagated_trust, new_depth))

        # Aggregate multiple path scores for each node
        final_scores = {}
        for node_id, scores in node_scores.items():
            final_scores[node_id] = self._aggregate_scores(scores)

        return final_scores

    def _aggregate_scores(self, scores: List[float]) -> float:
        """Aggregate multiple trust scores.

        Args:
            scores: List of scores to aggregate

        Returns:
            Aggregated score
        """
        if not scores:
            return 0.0

        return aggregate_scores(scores, self.config.aggregation)

    def _compute_confidence(
        self,
        graph: TrustGraph,
        source_nodes: List[str],
    ) -> float:
        """Compute confidence in weighted propagation results.

        Args:
            graph: The trust graph
            source_nodes: List of source node IDs

        Returns:
            Confidence value in [0, 1]
        """
        if graph.num_nodes == 0:
            return 0.0

        # Factor 1: Coverage - what fraction of nodes are sources
        source_coverage = len(source_nodes) / graph.num_nodes

        # Factor 2: Connectivity - are nodes well connected
        if graph.num_nodes > 1:
            max_edges = graph.num_nodes * (graph.num_nodes - 1)
            density = graph.num_edges / max_edges
        else:
            density = 0.5

        # Factor 3: Decay setting - lower decay = more information preserved
        decay_factor = 1.0 - self.config.decay

        # Combine factors
        confidence = (
            0.3 * min(1.0, source_coverage * 2)  # Cap at 50% coverage
            + 0.4 * density
            + 0.3 * decay_factor
        )
        return min(1.0, max(0.0, confidence))


class DijkstraPropagator(BasePropagator):
    """Trust propagation using shortest path (Dijkstra's algorithm).

    Computes trust based on the shortest (highest trust) path between
    nodes. Unlike WeightedPropagator which considers all paths,
    this only uses the single best path.

    Path trust is computed as the product of edge weights along the path,
    with optional decay per hop.

    Example:
        >>> propagator = DijkstraPropagator()
        >>> scores = propagator.propagate_from(graph, "trusted-source")
    """

    def __init__(
        self,
        config: Optional[PropagationConfig] = None,
        decay: Optional[float] = None,
    ) -> None:
        """Initialize Dijkstra propagator.

        Args:
            config: Propagation configuration
            decay: Trust decay per hop
        """
        super().__init__(config)

        if decay is not None:
            if not 0.0 <= decay <= 1.0:
                raise ValueError(f"Decay must be in [0, 1], got {decay}")
            self.config.decay = decay

    def propagate(
        self,
        graph: TrustGraph,
        source_nodes: Optional[List[str]] = None,
    ) -> Dict[str, TrustScore]:
        """Propagate trust from multiple sources using shortest paths.

        Args:
            graph: The trust graph
            source_nodes: Optional list of source node IDs

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        self._validate_graph(graph)
        self.last_run_time = datetime.now()

        # Determine source nodes
        if source_nodes is None:
            source_nodes = [
                n.node_id for n in graph.nodes()
                if n.initial_trust is not None and n.initial_trust > 0
            ]
            if not source_nodes:
                source_nodes = graph.node_ids()

        for source_id in source_nodes:
            self._validate_source(graph, source_id)

        # Compute best path from any source to each node
        all_scores: Dict[str, List[float]] = defaultdict(list)

        for source_id in source_nodes:
            source_node = graph.get_node(source_id)
            source_trust = (
                source_node.base_trust
                if source_node and source_node.base_trust is not None
                else self.config.initial_trust
            )

            path_scores = self._dijkstra_propagate(graph, source_id, source_trust)
            for node_id, score in path_scores.items():
                all_scores[node_id].append(score)

        # Take maximum from all sources (best reachability)
        final_scores = {}
        for node_id, scores in all_scores.items():
            final_scores[node_id] = max(scores) if scores else 0.0

        for node_id in graph.node_ids():
            if node_id not in final_scores:
                final_scores[node_id] = self.config.min_trust

        if self.config.normalize:
            final_scores = self._normalize_scores(final_scores)

        final_scores = self._clamp_scores(final_scores)

        return self._scores_to_trust_scores(
            final_scores,
            source="dijkstra",
            confidence=0.8,  # High confidence due to exact paths
        )

    def propagate_from(
        self,
        graph: TrustGraph,
        source_id: str,
    ) -> Dict[str, TrustScore]:
        """Propagate trust from a single source using shortest paths.

        Args:
            graph: The trust graph
            source_id: ID of the source node

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        self._validate_graph(graph)
        self._validate_source(graph, source_id)
        self.last_run_time = datetime.now()

        source_node = graph.get_node(source_id)
        source_trust = (
            source_node.base_trust
            if source_node and source_node.base_trust is not None
            else 1.0
        )

        scores = self._dijkstra_propagate(graph, source_id, source_trust)

        for node_id in graph.node_ids():
            if node_id not in scores:
                scores[node_id] = 0.0

        if self.config.normalize:
            scores = self._normalize_scores(scores)

        scores = self._clamp_scores(scores)

        return self._scores_to_trust_scores(
            scores,
            source=f"dijkstra_from_{source_id}",
            confidence=0.8,
        )

    def _dijkstra_propagate(
        self,
        graph: TrustGraph,
        source_id: str,
        source_trust: float,
    ) -> Dict[str, float]:
        """Compute trust using Dijkstra's algorithm.

        We use a modified Dijkstra where we maximize trust instead of
        minimizing distance. Trust along a path is the product of
        edge weights with decay.

        Args:
            graph: The trust graph
            source_id: Starting node
            source_trust: Initial trust at source

        Returns:
            Dictionary of best trust scores to each reachable node
        """
        import heapq

        # Priority queue: (-trust, node_id, hops)
        # Negative trust because heapq is a min-heap
        pq = [(-source_trust, source_id, 0)]
        best_trust: Dict[str, float] = {source_id: source_trust}
        decay_factor = 1.0 - self.config.decay

        while pq:
            neg_trust, current_id, hops = heapq.heappop(pq)
            current_trust = -neg_trust

            # Skip if we've found a better path
            if current_trust < best_trust.get(current_id, 0):
                continue

            # Stop if max depth reached
            if hops >= self.config.max_depth:
                continue

            # Explore neighbors
            for neighbor_id in graph.neighbors(current_id):
                edge = graph.get_edge(current_id, neighbor_id)
                if edge is None:
                    continue

                edge_weight = edge.weight if self.config.use_edge_weights else 1.0
                new_trust = current_trust * edge_weight * decay_factor

                # Only update if this is a better path
                if new_trust > best_trust.get(neighbor_id, 0):
                    best_trust[neighbor_id] = new_trust
                    heapq.heappush(pq, (-new_trust, neighbor_id, hops + 1))

        return best_trust
