"""
Graph-level trust metrics.

Computes various metrics for understanding overall trust health
and structure of the trust graph.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Tuple, TYPE_CHECKING

import networkx as nx
import numpy as np

if TYPE_CHECKING:
    from ..core.graph import TrustGraph


@dataclass
class GraphMetrics:
    """Comprehensive metrics for a trust graph.

    Attributes:
        num_nodes: Total number of nodes in the graph.
        num_edges: Total number of edges (trust relationships).
        density: Graph density (actual edges / possible edges).
        avg_trust: Average trust score across all edges.
        trust_std: Standard deviation of trust scores.
        avg_clustering: Average clustering coefficient.
        num_components: Number of connected components.
        diameter: Longest shortest path (None if disconnected).
        avg_path_length: Average shortest path length.
        trust_gini: Gini coefficient measuring trust inequality.
    """

    num_nodes: int
    num_edges: int
    density: float
    avg_trust: float
    trust_std: float
    avg_clustering: float
    num_components: int
    diameter: Optional[int]
    avg_path_length: float
    trust_gini: float


@dataclass
class NodeMetrics:
    """Metrics for a single node in the trust graph.

    Attributes:
        node_id: Identifier for the node.
        in_degree: Number of incoming trust edges.
        out_degree: Number of outgoing trust edges.
        avg_in_trust: Average trust received from others.
        avg_out_trust: Average trust given to others.
        betweenness: Betweenness centrality.
        closeness: Closeness centrality.
        pagerank: PageRank score.
        clustering: Local clustering coefficient.
    """

    node_id: str
    in_degree: int = 0
    out_degree: int = 0
    avg_in_trust: float = 0.0
    avg_out_trust: float = 0.0
    betweenness: float = 0.0
    closeness: float = 0.0
    pagerank: float = 0.0
    clustering: float = 0.0


class MetricsCalculator:
    """Calculate trust graph metrics.

    Computes various metrics for understanding overall
    trust health and structure.

    Example:
        >>> from rotalabs_graph.analysis import MetricsCalculator
        >>> calc = MetricsCalculator()
        >>> metrics = calc.compute(graph)
        >>> print(f"Trust Gini: {metrics.trust_gini:.2f}")
        Trust Gini: 0.32
        >>> print(f"Avg clustering: {metrics.avg_clustering:.2f}")
        Avg clustering: 0.45

    Attributes:
        trust_weight: Name of the edge attribute containing trust scores.
        default_trust: Default trust value for edges without explicit trust.
    """

    def __init__(
        self,
        trust_weight: str = "trust",
        default_trust: float = 1.0,
    ):
        """Initialize the metrics calculator.

        Args:
            trust_weight: Name of the edge attribute for trust scores.
            default_trust: Default trust for edges without explicit scores.
        """
        self.trust_weight = trust_weight
        self.default_trust = default_trust

    def compute(self, graph: "TrustGraph") -> GraphMetrics:
        """Compute comprehensive metrics for the trust graph.

        Args:
            graph: The trust graph to analyze.

        Returns:
            GraphMetrics object with all computed metrics.
        """
        nx_graph = graph.to_networkx()

        num_nodes = nx_graph.number_of_nodes()
        num_edges = nx_graph.number_of_edges()

        # Density
        density = nx.density(nx_graph)

        # Trust statistics
        trust_scores = [
            data.get(self.trust_weight, self.default_trust)
            for _, _, data in nx_graph.edges(data=True)
        ]

        if trust_scores:
            avg_trust = np.mean(trust_scores)
            trust_std = np.std(trust_scores)
        else:
            avg_trust = 0.0
            trust_std = 0.0

        # Clustering coefficient
        if nx_graph.is_directed():
            undirected = nx_graph.to_undirected()
        else:
            undirected = nx_graph

        try:
            avg_clustering = nx.average_clustering(undirected)
        except Exception:
            avg_clustering = 0.0

        # Connected components
        if nx_graph.is_directed():
            num_components = nx.number_weakly_connected_components(nx_graph)
            components = list(nx.weakly_connected_components(nx_graph))
        else:
            num_components = nx.number_connected_components(nx_graph)
            components = list(nx.connected_components(nx_graph))

        # Diameter and average path length
        diameter = None
        avg_path_length = 0.0

        if num_components == 1 and num_nodes > 1:
            try:
                if nx_graph.is_directed():
                    # For directed graphs, check strong connectivity
                    if nx.is_strongly_connected(nx_graph):
                        diameter = nx.diameter(nx_graph)
                        avg_path_length = nx.average_shortest_path_length(nx_graph)
                    else:
                        # Use largest strongly connected component
                        largest_scc = max(
                            nx.strongly_connected_components(nx_graph), key=len
                        )
                        if len(largest_scc) > 1:
                            subgraph = nx_graph.subgraph(largest_scc)
                            diameter = nx.diameter(subgraph)
                            avg_path_length = nx.average_shortest_path_length(subgraph)
                else:
                    diameter = nx.diameter(nx_graph)
                    avg_path_length = nx.average_shortest_path_length(nx_graph)
            except Exception:
                pass
        elif num_components > 1:
            # Compute for largest component
            largest_component = max(components, key=len)
            if len(largest_component) > 1:
                subgraph = nx_graph.subgraph(largest_component)
                try:
                    if nx_graph.is_directed():
                        if nx.is_strongly_connected(subgraph):
                            diameter = nx.diameter(subgraph)
                            avg_path_length = nx.average_shortest_path_length(subgraph)
                    else:
                        diameter = nx.diameter(subgraph)
                        avg_path_length = nx.average_shortest_path_length(subgraph)
                except Exception:
                    pass

        # Trust Gini coefficient
        trust_gini = self._gini_coefficient(trust_scores) if trust_scores else 0.0

        return GraphMetrics(
            num_nodes=num_nodes,
            num_edges=num_edges,
            density=density,
            avg_trust=float(avg_trust),
            trust_std=float(trust_std),
            avg_clustering=avg_clustering,
            num_components=num_components,
            diameter=diameter,
            avg_path_length=avg_path_length,
            trust_gini=trust_gini,
        )

    def _gini_coefficient(self, values: List[float]) -> float:
        """Compute the Gini coefficient for a list of values.

        The Gini coefficient measures inequality, where 0 is perfect
        equality and 1 is maximum inequality.

        Args:
            values: List of values to compute Gini for.

        Returns:
            Gini coefficient between 0 and 1.
        """
        if not values:
            return 0.0

        values = np.array(sorted(values))
        n = len(values)

        if n == 1:
            return 0.0

        # Gini formula: 2 * sum((i - (n+1)/2) * x_i) / (n * sum(x_i))
        indices = np.arange(1, n + 1)
        return float(
            (2 * np.sum(indices * values) - (n + 1) * np.sum(values))
            / (n * np.sum(values))
        ) if np.sum(values) > 0 else 0.0

    def trust_distribution(self, graph: "TrustGraph") -> Dict[str, float]:
        """Get the distribution of trust scores.

        Args:
            graph: The trust graph to analyze.

        Returns:
            Dictionary with distribution statistics:
                - min: Minimum trust
                - max: Maximum trust
                - mean: Mean trust
                - median: Median trust
                - std: Standard deviation
                - p25: 25th percentile
                - p75: 75th percentile
        """
        nx_graph = graph.to_networkx()

        trust_scores = [
            data.get(self.trust_weight, self.default_trust)
            for _, _, data in nx_graph.edges(data=True)
        ]

        if not trust_scores:
            return {
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
                "p25": 0.0,
                "p75": 0.0,
            }

        trust_array = np.array(trust_scores)

        return {
            "min": float(np.min(trust_array)),
            "max": float(np.max(trust_array)),
            "mean": float(np.mean(trust_array)),
            "median": float(np.median(trust_array)),
            "std": float(np.std(trust_array)),
            "p25": float(np.percentile(trust_array, 25)),
            "p75": float(np.percentile(trust_array, 75)),
        }

    def node_importance(
        self,
        graph: "TrustGraph",
        method: str = "pagerank",
    ) -> Dict[str, float]:
        """Compute node importance scores.

        Args:
            graph: The trust graph to analyze.
            method: Importance metric to use:
                - "pagerank": PageRank algorithm (default)
                - "eigenvector": Eigenvector centrality
                - "katz": Katz centrality
                - "degree": Degree centrality

        Returns:
            Dictionary mapping node IDs to importance scores.

        Raises:
            ValueError: If an invalid method is specified.
        """
        nx_graph = graph.to_networkx()

        if method == "pagerank":
            return nx.pagerank(nx_graph, weight=self.trust_weight)
        elif method == "eigenvector":
            try:
                return nx.eigenvector_centrality(
                    nx_graph, weight=self.trust_weight, max_iter=1000
                )
            except nx.PowerIterationFailedConvergence:
                # Fall back to PageRank if eigenvector doesn't converge
                return nx.pagerank(nx_graph, weight=self.trust_weight)
        elif method == "katz":
            try:
                return nx.katz_centrality(nx_graph, weight=self.trust_weight)
            except Exception:
                return nx.pagerank(nx_graph, weight=self.trust_weight)
        elif method == "degree":
            if nx_graph.is_directed():
                return dict(nx_graph.in_degree())
            else:
                return dict(nx_graph.degree())
        else:
            raise ValueError(
                f"Invalid method '{method}'. "
                "Must be one of: pagerank, eigenvector, katz, degree"
            )

    def trust_reciprocity(self, graph: "TrustGraph") -> float:
        """Compute trust reciprocity in the graph.

        Reciprocity measures the proportion of mutual trust relationships.
        A value of 1 means all trust is reciprocated; 0 means no reciprocity.

        Args:
            graph: The trust graph to analyze.

        Returns:
            Reciprocity score between 0 and 1.
        """
        nx_graph = graph.to_networkx()

        if not nx_graph.is_directed():
            return 1.0  # Undirected graphs are fully reciprocal

        if nx_graph.number_of_edges() == 0:
            return 0.0

        return nx.reciprocity(nx_graph)

    def trust_transitivity(self, graph: "TrustGraph") -> float:
        """Compute trust transitivity (global clustering coefficient).

        Transitivity measures the tendency of nodes to cluster together.
        High transitivity suggests that if A trusts B and B trusts C,
        then A likely trusts C.

        Args:
            graph: The trust graph to analyze.

        Returns:
            Transitivity score between 0 and 1.
        """
        nx_graph = graph.to_networkx()

        if nx_graph.is_directed():
            undirected = nx_graph.to_undirected()
        else:
            undirected = nx_graph

        return nx.transitivity(undirected)

    def node_metrics(self, graph: "TrustGraph", node_id: str) -> NodeMetrics:
        """Compute detailed metrics for a specific node.

        Args:
            graph: The trust graph to analyze.
            node_id: ID of the node to analyze.

        Returns:
            NodeMetrics object with detailed metrics.

        Raises:
            ValueError: If the node doesn't exist.
        """
        nx_graph = graph.to_networkx()

        if node_id not in nx_graph:
            raise ValueError(f"Node '{node_id}' not found in graph")

        # Degree metrics
        if nx_graph.is_directed():
            in_degree = nx_graph.in_degree(node_id)
            out_degree = nx_graph.out_degree(node_id)

            # Average in-trust
            in_edges = nx_graph.in_edges(node_id, data=True)
            in_trusts = [
                data.get(self.trust_weight, self.default_trust)
                for _, _, data in in_edges
            ]
            avg_in_trust = np.mean(in_trusts) if in_trusts else 0.0

            # Average out-trust
            out_edges = nx_graph.out_edges(node_id, data=True)
            out_trusts = [
                data.get(self.trust_weight, self.default_trust)
                for _, _, data in out_edges
            ]
            avg_out_trust = np.mean(out_trusts) if out_trusts else 0.0
        else:
            in_degree = nx_graph.degree(node_id)
            out_degree = in_degree

            edges = nx_graph.edges(node_id, data=True)
            trusts = [
                data.get(self.trust_weight, self.default_trust)
                for _, _, data in edges
            ]
            avg_in_trust = np.mean(trusts) if trusts else 0.0
            avg_out_trust = avg_in_trust

        # Centrality metrics
        betweenness = nx.betweenness_centrality(nx_graph).get(node_id, 0.0)
        closeness = nx.closeness_centrality(nx_graph).get(node_id, 0.0)
        pagerank = nx.pagerank(nx_graph, weight=self.trust_weight).get(node_id, 0.0)

        # Clustering
        if nx_graph.is_directed():
            undirected = nx_graph.to_undirected()
        else:
            undirected = nx_graph
        clustering = nx.clustering(undirected, node_id)

        return NodeMetrics(
            node_id=node_id,
            in_degree=in_degree,
            out_degree=out_degree,
            avg_in_trust=float(avg_in_trust),
            avg_out_trust=float(avg_out_trust),
            betweenness=betweenness,
            closeness=closeness,
            pagerank=pagerank,
            clustering=clustering,
        )

    def all_node_metrics(self, graph: "TrustGraph") -> Dict[str, NodeMetrics]:
        """Compute metrics for all nodes.

        Args:
            graph: The trust graph to analyze.

        Returns:
            Dictionary mapping node IDs to their NodeMetrics.
        """
        nx_graph = graph.to_networkx()

        # Pre-compute centrality metrics for efficiency
        betweenness = nx.betweenness_centrality(nx_graph)
        closeness = nx.closeness_centrality(nx_graph)
        pagerank_scores = nx.pagerank(nx_graph, weight=self.trust_weight)

        if nx_graph.is_directed():
            undirected = nx_graph.to_undirected()
        else:
            undirected = nx_graph
        clustering = nx.clustering(undirected)

        metrics = {}
        for node_id in nx_graph.nodes():
            # Degree metrics
            if nx_graph.is_directed():
                in_degree = nx_graph.in_degree(node_id)
                out_degree = nx_graph.out_degree(node_id)

                in_edges = nx_graph.in_edges(node_id, data=True)
                in_trusts = [
                    data.get(self.trust_weight, self.default_trust)
                    for _, _, data in in_edges
                ]
                avg_in_trust = np.mean(in_trusts) if in_trusts else 0.0

                out_edges = nx_graph.out_edges(node_id, data=True)
                out_trusts = [
                    data.get(self.trust_weight, self.default_trust)
                    for _, _, data in out_edges
                ]
                avg_out_trust = np.mean(out_trusts) if out_trusts else 0.0
            else:
                in_degree = nx_graph.degree(node_id)
                out_degree = in_degree

                edges = nx_graph.edges(node_id, data=True)
                trusts = [
                    data.get(self.trust_weight, self.default_trust)
                    for _, _, data in edges
                ]
                avg_in_trust = np.mean(trusts) if trusts else 0.0
                avg_out_trust = avg_in_trust

            metrics[node_id] = NodeMetrics(
                node_id=node_id,
                in_degree=in_degree,
                out_degree=out_degree,
                avg_in_trust=float(avg_in_trust),
                avg_out_trust=float(avg_out_trust),
                betweenness=betweenness.get(node_id, 0.0),
                closeness=closeness.get(node_id, 0.0),
                pagerank=pagerank_scores.get(node_id, 0.0),
                clustering=clustering.get(node_id, 0.0),
            )

        return metrics

    def trust_flow_summary(
        self,
        graph: "TrustGraph",
    ) -> Dict[str, List[Tuple[str, float]]]:
        """Summarize trust flow in the graph.

        Identifies the major trust sources (nodes that give trust)
        and trust sinks (nodes that receive trust).

        Args:
            graph: The trust graph to analyze.

        Returns:
            Dictionary with:
                - "sources": Top trust-giving nodes
                - "sinks": Top trust-receiving nodes
                - "balanced": Nodes with balanced in/out trust
        """
        nx_graph = graph.to_networkx()

        if not nx_graph.is_directed():
            # For undirected, all nodes are balanced
            degrees = dict(nx_graph.degree())
            balanced = sorted(degrees.items(), key=lambda x: -x[1])[:10]
            return {
                "sources": [],
                "sinks": [],
                "balanced": balanced,
            }

        # Compute trust flow for each node
        node_flow: Dict[str, Tuple[float, float]] = {}

        for node in nx_graph.nodes():
            # Out-trust (given)
            out_edges = nx_graph.out_edges(node, data=True)
            out_trust = sum(
                data.get(self.trust_weight, self.default_trust)
                for _, _, data in out_edges
            )

            # In-trust (received)
            in_edges = nx_graph.in_edges(node, data=True)
            in_trust = sum(
                data.get(self.trust_weight, self.default_trust)
                for _, _, data in in_edges
            )

            node_flow[node] = (out_trust, in_trust)

        # Categorize nodes
        sources = []  # High out-trust, low in-trust
        sinks = []  # High in-trust, low out-trust
        balanced = []  # Similar in and out trust

        for node, (out_trust, in_trust) in node_flow.items():
            total = out_trust + in_trust
            if total == 0:
                continue

            ratio = out_trust / total if total > 0 else 0.5

            if ratio > 0.7:
                sources.append((node, out_trust))
            elif ratio < 0.3:
                sinks.append((node, in_trust))
            else:
                balanced.append((node, total))

        # Sort by magnitude
        sources.sort(key=lambda x: -x[1])
        sinks.sort(key=lambda x: -x[1])
        balanced.sort(key=lambda x: -x[1])

        return {
            "sources": sources[:10],
            "sinks": sinks[:10],
            "balanced": balanced[:10],
        }


__all__ = [
    "GraphMetrics",
    "NodeMetrics",
    "MetricsCalculator",
]
