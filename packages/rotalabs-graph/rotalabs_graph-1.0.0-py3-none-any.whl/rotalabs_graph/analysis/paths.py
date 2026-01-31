"""
Path analysis for trust graphs.

Finds and evaluates paths through the trust graph, identifying
bottlenecks and alternative routes for trust propagation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING, Callable
from enum import Enum

import networkx as nx

if TYPE_CHECKING:
    from ..core.graph import TrustGraph
    from ..core.types import EdgeType


class PathMetric(str, Enum):
    """Metrics for evaluating trust paths."""

    TRUST = "trust"  # Combined trust score along path
    LENGTH = "length"  # Number of hops
    BOTTLENECK = "bottleneck"  # Minimum edge trust in path


@dataclass
class TrustPath:
    """Represents a path through the trust graph.

    Attributes:
        source_id: ID of the starting node.
        target_id: ID of the ending node.
        node_ids: Ordered list of node IDs in the path.
        edge_types: Types of edges along the path.
        path_trust: Combined trust score for the entire path.
        length: Number of edges in the path.
        bottleneck_edge: The weakest edge in the path (source, target, trust).
    """

    source_id: str
    target_id: str
    node_ids: List[str]
    edge_types: List["EdgeType"] = field(default_factory=list)
    path_trust: float = 1.0
    length: int = 0
    bottleneck_edge: Optional[Tuple[str, str, float]] = None

    def __post_init__(self):
        """Calculate length if not set."""
        if self.length == 0 and len(self.node_ids) > 1:
            self.length = len(self.node_ids) - 1


class PathAnalyzer:
    """Analyze trust paths between nodes.

    Finds and evaluates paths through the trust graph,
    identifying bottlenecks and alternative routes.

    Example:
        >>> from rotalabs_graph.analysis import PathAnalyzer
        >>> analyzer = PathAnalyzer()
        >>> paths = analyzer.find_all_paths(graph, "user-1", "model-a")
        >>> best = analyzer.best_path(graph, "user-1", "model-a")
        >>> print(f"Best path trust: {best.path_trust:.2f}")
        Best path trust: 0.72

    Attributes:
        trust_weight: Name of the edge attribute containing trust scores.
        default_trust: Default trust value for edges without explicit trust.
    """

    def __init__(
        self,
        trust_weight: str = "trust",
        default_trust: float = 1.0,
    ):
        """Initialize the path analyzer.

        Args:
            trust_weight: Name of the edge attribute for trust scores.
            default_trust: Default trust for edges without explicit scores.
        """
        self.trust_weight = trust_weight
        self.default_trust = default_trust

    def find_all_paths(
        self,
        graph: "TrustGraph",
        source_id: str,
        target_id: str,
        max_length: int = 5,
    ) -> List[TrustPath]:
        """Find all paths between two nodes.

        Uses depth-limited search to find all simple paths.

        Args:
            graph: The trust graph to analyze.
            source_id: ID of the starting node.
            target_id: ID of the target node.
            max_length: Maximum path length (number of edges).

        Returns:
            List of TrustPath objects for all found paths.

        Raises:
            ValueError: If source or target node doesn't exist.
        """
        nx_graph = graph.to_networkx()

        if source_id not in nx_graph:
            raise ValueError(f"Source node '{source_id}' not found in graph")
        if target_id not in nx_graph:
            raise ValueError(f"Target node '{target_id}' not found in graph")

        paths = []

        try:
            simple_paths = nx.all_simple_paths(
                nx_graph, source_id, target_id, cutoff=max_length
            )

            for path_nodes in simple_paths:
                trust_path = self._build_trust_path(nx_graph, path_nodes)
                paths.append(trust_path)

        except nx.NetworkXError:
            # No path exists
            pass

        return paths

    def best_path(
        self,
        graph: "TrustGraph",
        source_id: str,
        target_id: str,
        metric: str = "trust",
        max_length: int = 10,
    ) -> Optional[TrustPath]:
        """Find the best path by the given metric.

        Args:
            graph: The trust graph to analyze.
            source_id: ID of the starting node.
            target_id: ID of the target node.
            metric: Metric to optimize ("trust", "length", "bottleneck").
            max_length: Maximum path length to consider.

        Returns:
            The best TrustPath, or None if no path exists.

        Raises:
            ValueError: If source or target doesn't exist, or invalid metric.
        """
        nx_graph = graph.to_networkx()

        if source_id not in nx_graph:
            raise ValueError(f"Source node '{source_id}' not found in graph")
        if target_id not in nx_graph:
            raise ValueError(f"Target node '{target_id}' not found in graph")

        try:
            metric_enum = PathMetric(metric)
        except ValueError:
            raise ValueError(
                f"Invalid metric '{metric}'. Must be one of: {[m.value for m in PathMetric]}"
            )

        if metric_enum == PathMetric.LENGTH:
            return self._shortest_path(nx_graph, source_id, target_id)
        elif metric_enum == PathMetric.TRUST:
            return self._highest_trust_path(nx_graph, source_id, target_id, max_length)
        elif metric_enum == PathMetric.BOTTLENECK:
            return self._widest_bottleneck_path(nx_graph, source_id, target_id)

        return None

    def _shortest_path(
        self,
        nx_graph: nx.Graph,
        source_id: str,
        target_id: str,
    ) -> Optional[TrustPath]:
        """Find the shortest path by number of edges."""
        try:
            path_nodes = nx.shortest_path(nx_graph, source_id, target_id)
            return self._build_trust_path(nx_graph, path_nodes)
        except nx.NetworkXNoPath:
            return None

    def _highest_trust_path(
        self,
        nx_graph: nx.Graph,
        source_id: str,
        target_id: str,
        max_length: int,
    ) -> Optional[TrustPath]:
        """Find the path with highest combined trust.

        Uses negative log transformation to convert product to sum
        for shortest path algorithms.
        """
        # Create a copy with negative log weights for path finding
        import math

        weight_graph = nx_graph.copy()

        for u, v, data in weight_graph.edges(data=True):
            trust = data.get(self.trust_weight, self.default_trust)
            # Clamp trust to avoid log(0)
            trust = max(trust, 1e-10)
            # Negative log so that higher trust = shorter path
            weight_graph[u][v]["neg_log_trust"] = -math.log(trust)

        try:
            path_nodes = nx.shortest_path(
                weight_graph,
                source_id,
                target_id,
                weight="neg_log_trust",
            )
            return self._build_trust_path(nx_graph, path_nodes)
        except nx.NetworkXNoPath:
            return None

    def _widest_bottleneck_path(
        self,
        nx_graph: nx.Graph,
        source_id: str,
        target_id: str,
    ) -> Optional[TrustPath]:
        """Find the path with the widest bottleneck (highest minimum trust).

        Uses a modified Dijkstra's algorithm to maximize the minimum edge weight.
        """
        import heapq

        if source_id not in nx_graph or target_id not in nx_graph:
            return None

        # Priority queue: (-bottleneck_trust, node, path)
        # Negative because heapq is a min-heap
        pq = [(-float("inf"), source_id, [source_id])]
        visited = set()
        best_bottleneck = {source_id: float("inf")}

        while pq:
            neg_bottleneck, current, path = heapq.heappop(pq)
            bottleneck = -neg_bottleneck

            if current in visited:
                continue

            visited.add(current)

            if current == target_id:
                return self._build_trust_path(nx_graph, path)

            neighbors = (
                nx_graph.successors(current)
                if nx_graph.is_directed()
                else nx_graph.neighbors(current)
            )

            for neighbor in neighbors:
                if neighbor in visited:
                    continue

                edge_data = nx_graph.get_edge_data(current, neighbor)
                edge_trust = edge_data.get(self.trust_weight, self.default_trust)

                # Bottleneck is the minimum trust along the path
                new_bottleneck = min(bottleneck, edge_trust)

                if new_bottleneck > best_bottleneck.get(neighbor, -float("inf")):
                    best_bottleneck[neighbor] = new_bottleneck
                    new_path = path + [neighbor]
                    heapq.heappush(pq, (-new_bottleneck, neighbor, new_path))

        return None

    def _build_trust_path(
        self,
        nx_graph: nx.Graph,
        path_nodes: List[str],
    ) -> TrustPath:
        """Build a TrustPath from a list of node IDs."""
        if len(path_nodes) < 2:
            return TrustPath(
                source_id=path_nodes[0] if path_nodes else "",
                target_id=path_nodes[0] if path_nodes else "",
                node_ids=path_nodes,
                path_trust=1.0,
                length=0,
            )

        # Calculate path trust (product of edge trusts)
        path_trust = 1.0
        min_trust = float("inf")
        bottleneck_edge = None
        edge_types = []

        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i + 1]
            edge_data = nx_graph.get_edge_data(u, v, {})
            edge_trust = edge_data.get(self.trust_weight, self.default_trust)
            path_trust *= edge_trust

            if edge_trust < min_trust:
                min_trust = edge_trust
                bottleneck_edge = (u, v, edge_trust)

            # Get edge type if available
            edge_type = edge_data.get("edge_type")
            if edge_type:
                edge_types.append(edge_type)

        return TrustPath(
            source_id=path_nodes[0],
            target_id=path_nodes[-1],
            node_ids=path_nodes,
            edge_types=edge_types,
            path_trust=path_trust,
            length=len(path_nodes) - 1,
            bottleneck_edge=bottleneck_edge,
        )

    def find_bottlenecks(
        self,
        graph: "TrustGraph",
        threshold: float = 0.5,
    ) -> List[Tuple[str, str, float, float]]:
        """Find edges that are bottlenecks (low trust, high betweenness).

        Bottleneck edges are those with low trust but high importance
        to overall graph connectivity.

        Args:
            graph: The trust graph to analyze.
            threshold: Maximum trust for an edge to be considered weak.

        Returns:
            List of tuples (source, target, trust, betweenness) for bottleneck edges.
        """
        nx_graph = graph.to_networkx()

        # Compute edge betweenness centrality
        edge_betweenness = nx.edge_betweenness_centrality(nx_graph)

        # Find the median betweenness for comparison
        betweenness_values = list(edge_betweenness.values())
        if not betweenness_values:
            return []

        median_betweenness = sorted(betweenness_values)[len(betweenness_values) // 2]

        bottlenecks = []
        for (u, v), betweenness in edge_betweenness.items():
            edge_data = nx_graph.get_edge_data(u, v, {})
            trust = edge_data.get(self.trust_weight, self.default_trust)

            # Bottleneck: low trust but high importance
            if trust < threshold and betweenness > median_betweenness:
                bottlenecks.append((u, v, trust, betweenness))

        # Sort by betweenness (most important first)
        bottlenecks.sort(key=lambda x: -x[3])
        return bottlenecks

    def path_trust(
        self,
        graph: "TrustGraph",
        path: List[str],
        aggregation: str = "product",
    ) -> float:
        """Calculate combined trust along a path.

        Args:
            graph: The trust graph to analyze.
            path: List of node IDs representing the path.
            aggregation: How to combine edge trusts:
                - "product": Multiply all trusts (default)
                - "min": Take the minimum trust (bottleneck)
                - "avg": Average of all trusts
                - "harmonic": Harmonic mean of trusts

        Returns:
            The combined trust score for the path.

        Raises:
            ValueError: If path has less than 2 nodes or invalid aggregation.
        """
        if len(path) < 2:
            return 1.0

        nx_graph = graph.to_networkx()
        trusts = []

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = nx_graph.get_edge_data(u, v, {})
            if edge_data is None:
                return 0.0  # No edge exists
            trust = edge_data.get(self.trust_weight, self.default_trust)
            trusts.append(trust)

        if not trusts:
            return 1.0

        if aggregation == "product":
            result = 1.0
            for t in trusts:
                result *= t
            return result
        elif aggregation == "min":
            return min(trusts)
        elif aggregation == "avg":
            return sum(trusts) / len(trusts)
        elif aggregation == "harmonic":
            if any(t == 0 for t in trusts):
                return 0.0
            return len(trusts) / sum(1.0 / t for t in trusts)
        else:
            raise ValueError(
                f"Invalid aggregation '{aggregation}'. "
                "Must be one of: product, min, avg, harmonic"
            )

    def compute_betweenness(self, graph: "TrustGraph") -> Dict[str, float]:
        """Compute betweenness centrality for all nodes.

        Betweenness centrality measures how often a node lies on shortest
        paths between other nodes. High betweenness indicates a node is
        critical for trust flow.

        Args:
            graph: The trust graph to analyze.

        Returns:
            Dictionary mapping node IDs to their betweenness centrality.
        """
        nx_graph = graph.to_networkx()
        return nx.betweenness_centrality(nx_graph)

    def compute_closeness(self, graph: "TrustGraph") -> Dict[str, float]:
        """Compute closeness centrality for all nodes.

        Closeness centrality measures the average distance from a node
        to all other nodes. High closeness indicates a node can quickly
        reach others in the trust network.

        Args:
            graph: The trust graph to analyze.

        Returns:
            Dictionary mapping node IDs to their closeness centrality.
        """
        nx_graph = graph.to_networkx()
        return nx.closeness_centrality(nx_graph)

    def reachable_nodes(
        self,
        graph: "TrustGraph",
        source_id: str,
        max_length: int = None,
    ) -> Dict[str, int]:
        """Find all nodes reachable from a source with their distances.

        Args:
            graph: The trust graph to analyze.
            source_id: ID of the starting node.
            max_length: Maximum path length to consider (None for unlimited).

        Returns:
            Dictionary mapping reachable node IDs to their shortest distance.

        Raises:
            ValueError: If source node doesn't exist.
        """
        nx_graph = graph.to_networkx()

        if source_id not in nx_graph:
            raise ValueError(f"Source node '{source_id}' not found in graph")

        if max_length is not None:
            lengths = dict(
                nx.single_source_shortest_path_length(
                    nx_graph, source_id, cutoff=max_length
                )
            )
        else:
            lengths = dict(nx.single_source_shortest_path_length(nx_graph, source_id))

        return lengths


__all__ = [
    "PathMetric",
    "TrustPath",
    "PathAnalyzer",
]
