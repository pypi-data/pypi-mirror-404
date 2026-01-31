"""
Clustering and community detection for trust graphs.

Identifies groups of nodes with high mutual trust, useful for
understanding trust boundaries and organizational structure.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING, Tuple
from enum import Enum

import networkx as nx
import numpy as np

if TYPE_CHECKING:
    from ..core.graph import TrustGraph


class ClusteringMethod(str, Enum):
    """Available clustering methods."""

    LOUVAIN = "louvain"
    LABEL_PROPAGATION = "label_propagation"
    GIRVAN_NEWMAN = "girvan_newman"
    SPECTRAL = "spectral"


@dataclass
class TrustCluster:
    """Represents a cluster of nodes in the trust graph.

    Attributes:
        cluster_id: Unique identifier for the cluster.
        node_ids: List of node IDs in this cluster.
        internal_trust: Average trust score within the cluster.
        external_trust: Average trust score to nodes outside the cluster.
        cohesion: How tightly connected nodes are within the cluster (0-1).
        central_nodes: Most connected nodes within the cluster.
    """

    cluster_id: str
    node_ids: List[str]
    internal_trust: float = 0.0
    external_trust: float = 0.0
    cohesion: float = 0.0
    central_nodes: List[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        """Number of nodes in the cluster."""
        return len(self.node_ids)

    @property
    def trust_ratio(self) -> float:
        """Ratio of internal to external trust."""
        if self.external_trust == 0:
            return float("inf") if self.internal_trust > 0 else 0.0
        return self.internal_trust / self.external_trust


class ClusterAnalyzer:
    """Analyze trust communities and clusters.

    Identifies groups of nodes with high mutual trust,
    useful for understanding trust boundaries.

    Example:
        >>> from rotalabs_graph.analysis import ClusterAnalyzer
        >>> analyzer = ClusterAnalyzer()
        >>> clusters = analyzer.detect_communities(graph)
        >>> for c in clusters:
        ...     print(f"Cluster {c.cluster_id}: {len(c.node_ids)} nodes")
        Cluster 0: 5 nodes
        Cluster 1: 3 nodes

    Attributes:
        trust_weight: Name of the edge attribute containing trust scores.
        default_trust: Default trust value for edges without explicit trust.
    """

    def __init__(
        self,
        trust_weight: str = "trust",
        default_trust: float = 1.0,
    ):
        """Initialize the cluster analyzer.

        Args:
            trust_weight: Name of the edge attribute for trust scores.
            default_trust: Default trust for edges without explicit scores.
        """
        self.trust_weight = trust_weight
        self.default_trust = default_trust

    def detect_communities(
        self,
        graph: "TrustGraph",
        method: str = "louvain",
        resolution: float = 1.0,
    ) -> List[TrustCluster]:
        """Detect trust communities using community detection algorithms.

        Args:
            graph: The trust graph to analyze.
            method: Community detection method:
                - "louvain": Louvain algorithm (default, best for large graphs)
                - "label_propagation": Label propagation (fast, non-deterministic)
                - "girvan_newman": Edge betweenness (slow but interpretable)
                - "spectral": Spectral clustering
            resolution: Resolution parameter for Louvain (higher = more clusters).

        Returns:
            List of TrustCluster objects representing detected communities.

        Raises:
            ValueError: If an invalid method is specified.
        """
        try:
            method_enum = ClusteringMethod(method)
        except ValueError:
            valid_methods = [m.value for m in ClusteringMethod]
            raise ValueError(
                f"Invalid method '{method}'. Must be one of: {valid_methods}"
            )

        nx_graph = graph.to_networkx()

        # Convert to undirected for community detection
        if nx_graph.is_directed():
            undirected = nx_graph.to_undirected()
        else:
            undirected = nx_graph

        if method_enum == ClusteringMethod.LOUVAIN:
            communities = self._louvain_communities(undirected, resolution)
        elif method_enum == ClusteringMethod.LABEL_PROPAGATION:
            communities = self._label_propagation_communities(undirected)
        elif method_enum == ClusteringMethod.GIRVAN_NEWMAN:
            communities = self._girvan_newman_communities(undirected)
        elif method_enum == ClusteringMethod.SPECTRAL:
            communities = self._spectral_communities(undirected)
        else:
            communities = []

        # Build TrustCluster objects with metrics
        clusters = []
        for i, node_set in enumerate(communities):
            node_ids = list(node_set)
            cluster = self._build_cluster(
                cluster_id=str(i),
                node_ids=node_ids,
                nx_graph=nx_graph,
                all_nodes=set(nx_graph.nodes()),
            )
            clusters.append(cluster)

        return clusters

    def _louvain_communities(
        self,
        nx_graph: nx.Graph,
        resolution: float,
    ) -> List[set]:
        """Detect communities using the Louvain algorithm."""
        try:
            from networkx.algorithms.community import louvain_communities

            return list(
                louvain_communities(
                    nx_graph,
                    weight=self.trust_weight,
                    resolution=resolution,
                )
            )
        except ImportError:
            # Fallback to greedy modularity
            from networkx.algorithms.community import greedy_modularity_communities

            return list(
                greedy_modularity_communities(nx_graph, weight=self.trust_weight)
            )

    def _label_propagation_communities(self, nx_graph: nx.Graph) -> List[set]:
        """Detect communities using label propagation."""
        from networkx.algorithms.community import label_propagation_communities

        return list(label_propagation_communities(nx_graph))

    def _girvan_newman_communities(
        self,
        nx_graph: nx.Graph,
        num_communities: int = None,
    ) -> List[set]:
        """Detect communities using Girvan-Newman algorithm."""
        from networkx.algorithms.community import girvan_newman

        # Get the generator
        communities_generator = girvan_newman(nx_graph)

        # If num_communities specified, iterate to that level
        if num_communities is not None:
            for communities in communities_generator:
                if len(communities) >= num_communities:
                    return [set(c) for c in communities]

        # Otherwise, use modularity to find best partition
        from networkx.algorithms.community import modularity

        best_communities = None
        best_modularity = -float("inf")

        # Limit iterations to avoid excessive computation
        max_iterations = min(nx_graph.number_of_edges(), 100)

        for i, communities in enumerate(communities_generator):
            if i >= max_iterations:
                break

            try:
                mod = modularity(nx_graph, communities)
                if mod > best_modularity:
                    best_modularity = mod
                    best_communities = communities
            except Exception:
                pass

        if best_communities is None:
            return [set(nx_graph.nodes())]

        return [set(c) for c in best_communities]

    def _spectral_communities(
        self,
        nx_graph: nx.Graph,
        num_clusters: int = None,
    ) -> List[set]:
        """Detect communities using spectral clustering."""
        try:
            from sklearn.cluster import SpectralClustering
        except ImportError:
            # Fallback to label propagation if sklearn not available
            return self._label_propagation_communities(nx_graph)

        nodes = list(nx_graph.nodes())
        if len(nodes) < 2:
            return [set(nodes)]

        # Build adjacency matrix
        adjacency = nx.to_numpy_array(nx_graph, nodelist=nodes, weight=self.trust_weight)

        # Estimate number of clusters if not specified
        if num_clusters is None:
            # Use eigenvalue gap heuristic
            num_clusters = min(max(2, len(nodes) // 5), 10)

        num_clusters = min(num_clusters, len(nodes))

        try:
            clustering = SpectralClustering(
                n_clusters=num_clusters,
                affinity="precomputed",
                assign_labels="kmeans",
                random_state=42,
            )
            labels = clustering.fit_predict(adjacency)

            # Group nodes by cluster
            communities: Dict[int, set] = {}
            for node, label in zip(nodes, labels):
                if label not in communities:
                    communities[label] = set()
                communities[label].add(node)

            return list(communities.values())

        except Exception:
            # Fallback on failure
            return [set(nodes)]

    def hierarchical_clustering(
        self,
        graph: "TrustGraph",
        num_clusters: int = None,
        linkage: str = "average",
    ) -> List[TrustCluster]:
        """Hierarchical clustering based on trust distances.

        Args:
            graph: The trust graph to analyze.
            num_clusters: Number of clusters to create (None for auto).
            linkage: Linkage method for hierarchical clustering:
                - "single": Minimum distance
                - "complete": Maximum distance
                - "average": Average distance (default)
                - "ward": Ward's method

        Returns:
            List of TrustCluster objects.
        """
        try:
            from scipy.cluster.hierarchy import linkage as scipy_linkage, fcluster
            from scipy.spatial.distance import squareform
        except ImportError:
            # Fallback to community detection
            return self.detect_communities(graph, method="louvain")

        nx_graph = graph.to_networkx()
        nodes = list(nx_graph.nodes())

        if len(nodes) < 2:
            return [
                self._build_cluster(
                    "0", nodes, nx_graph, set(nodes)
                )
            ]

        # Build distance matrix (1 - trust)
        n = len(nodes)
        distance_matrix = np.ones((n, n))

        node_to_idx = {node: i for i, node in enumerate(nodes)}

        for u, v, data in nx_graph.edges(data=True):
            trust = data.get(self.trust_weight, self.default_trust)
            distance = 1.0 - trust
            i, j = node_to_idx[u], node_to_idx[v]
            distance_matrix[i, j] = distance
            distance_matrix[j, i] = distance

        np.fill_diagonal(distance_matrix, 0)

        # Convert to condensed form
        condensed = squareform(distance_matrix)

        # Perform hierarchical clustering
        Z = scipy_linkage(condensed, method=linkage)

        # Determine number of clusters
        if num_clusters is None:
            # Use inconsistency to determine optimal cut
            from scipy.cluster.hierarchy import inconsistent

            inc = inconsistent(Z)
            # Cut at first major inconsistency
            threshold = np.mean(inc[:, 3]) + np.std(inc[:, 3])
            labels = fcluster(Z, t=threshold, criterion="inconsistent")
        else:
            labels = fcluster(Z, t=num_clusters, criterion="maxclust")

        # Group nodes by cluster
        communities: Dict[int, List[str]] = {}
        for node, label in zip(nodes, labels):
            if label not in communities:
                communities[label] = []
            communities[label].append(node)

        # Build cluster objects
        clusters = []
        for cluster_id, node_ids in communities.items():
            cluster = self._build_cluster(
                str(cluster_id),
                node_ids,
                nx_graph,
                set(nodes),
            )
            clusters.append(cluster)

        return clusters

    def _build_cluster(
        self,
        cluster_id: str,
        node_ids: List[str],
        nx_graph: nx.Graph,
        all_nodes: set,
    ) -> TrustCluster:
        """Build a TrustCluster with computed metrics."""
        node_set = set(node_ids)
        external_nodes = all_nodes - node_set

        # Calculate internal trust
        internal_trusts = []
        for u in node_ids:
            neighbors = (
                nx_graph.successors(u)
                if nx_graph.is_directed()
                else nx_graph.neighbors(u)
            )
            for v in neighbors:
                if v in node_set and u != v:
                    edge_data = nx_graph.get_edge_data(u, v, {})
                    trust = edge_data.get(self.trust_weight, self.default_trust)
                    internal_trusts.append(trust)

        internal_trust = (
            sum(internal_trusts) / len(internal_trusts) if internal_trusts else 0.0
        )

        # Calculate external trust
        external_trusts = []
        for u in node_ids:
            neighbors = (
                nx_graph.successors(u)
                if nx_graph.is_directed()
                else nx_graph.neighbors(u)
            )
            for v in neighbors:
                if v in external_nodes:
                    edge_data = nx_graph.get_edge_data(u, v, {})
                    trust = edge_data.get(self.trust_weight, self.default_trust)
                    external_trusts.append(trust)

        external_trust = (
            sum(external_trusts) / len(external_trusts) if external_trusts else 0.0
        )

        # Calculate cohesion (internal edge density)
        max_internal_edges = len(node_ids) * (len(node_ids) - 1)
        if nx_graph.is_directed():
            max_internal_edges = max_internal_edges  # Both directions
        else:
            max_internal_edges = max_internal_edges // 2

        actual_internal_edges = len(internal_trusts)
        cohesion = (
            actual_internal_edges / max_internal_edges
            if max_internal_edges > 0
            else 0.0
        )

        # Find central nodes (by degree within cluster)
        internal_degrees: Dict[str, int] = {node: 0 for node in node_ids}
        for u in node_ids:
            neighbors = (
                nx_graph.successors(u)
                if nx_graph.is_directed()
                else nx_graph.neighbors(u)
            )
            for v in neighbors:
                if v in node_set:
                    internal_degrees[u] += 1

        # Top 3 central nodes
        sorted_nodes = sorted(
            internal_degrees.items(), key=lambda x: -x[1]
        )
        central_nodes = [node for node, _ in sorted_nodes[:3]]

        return TrustCluster(
            cluster_id=cluster_id,
            node_ids=node_ids,
            internal_trust=internal_trust,
            external_trust=external_trust,
            cohesion=cohesion,
            central_nodes=central_nodes,
        )

    def compute_cluster_trust_matrix(
        self,
        graph: "TrustGraph",
        clusters: List[TrustCluster],
    ) -> np.ndarray:
        """Compute trust between clusters.

        Creates a matrix where entry (i, j) is the average trust
        from cluster i to cluster j.

        Args:
            graph: The trust graph to analyze.
            clusters: List of clusters to compute trust between.

        Returns:
            NumPy array of shape (num_clusters, num_clusters) with
            inter-cluster trust scores.
        """
        nx_graph = graph.to_networkx()
        num_clusters = len(clusters)

        # Create node to cluster mapping
        node_to_cluster: Dict[str, int] = {}
        for i, cluster in enumerate(clusters):
            for node in cluster.node_ids:
                node_to_cluster[node] = i

        # Initialize matrix
        trust_sums = np.zeros((num_clusters, num_clusters))
        edge_counts = np.zeros((num_clusters, num_clusters))

        # Aggregate trust scores
        for u, v, data in nx_graph.edges(data=True):
            if u not in node_to_cluster or v not in node_to_cluster:
                continue

            cluster_u = node_to_cluster[u]
            cluster_v = node_to_cluster[v]

            trust = data.get(self.trust_weight, self.default_trust)
            trust_sums[cluster_u, cluster_v] += trust
            edge_counts[cluster_u, cluster_v] += 1

        # Compute averages
        with np.errstate(divide="ignore", invalid="ignore"):
            trust_matrix = np.where(
                edge_counts > 0,
                trust_sums / edge_counts,
                0.0,
            )

        return trust_matrix

    def find_bridges(
        self,
        graph: "TrustGraph",
        clusters: List[TrustCluster],
    ) -> List[Tuple[str, List[str]]]:
        """Find nodes that bridge multiple clusters.

        Bridge nodes have significant connections to multiple clusters
        and may be important for inter-cluster trust propagation.

        Args:
            graph: The trust graph to analyze.
            clusters: List of clusters to analyze.

        Returns:
            List of tuples (node_id, connected_cluster_ids) for bridge nodes.
        """
        nx_graph = graph.to_networkx()

        # Create node to cluster mapping
        node_to_cluster: Dict[str, str] = {}
        for cluster in clusters:
            for node in cluster.node_ids:
                node_to_cluster[node] = cluster.cluster_id

        bridges = []

        for node in nx_graph.nodes():
            if node not in node_to_cluster:
                continue

            home_cluster = node_to_cluster[node]
            connected_clusters = set()

            neighbors = (
                list(nx_graph.successors(node)) + list(nx_graph.predecessors(node))
                if nx_graph.is_directed()
                else nx_graph.neighbors(node)
            )

            for neighbor in neighbors:
                if neighbor in node_to_cluster:
                    neighbor_cluster = node_to_cluster[neighbor]
                    if neighbor_cluster != home_cluster:
                        connected_clusters.add(neighbor_cluster)

            # A bridge connects to at least one other cluster
            if connected_clusters:
                bridges.append((node, sorted(connected_clusters)))

        # Sort by number of clusters connected (most connected first)
        bridges.sort(key=lambda x: -len(x[1]))

        return bridges

    def cluster_modularity(
        self,
        graph: "TrustGraph",
        clusters: List[TrustCluster],
    ) -> float:
        """Compute the modularity of a clustering.

        Modularity measures how good a division of the network is.
        Higher values (close to 1) indicate strong community structure.

        Args:
            graph: The trust graph to analyze.
            clusters: List of clusters to evaluate.

        Returns:
            Modularity score between -0.5 and 1.
        """
        nx_graph = graph.to_networkx()

        # Convert to undirected for modularity calculation
        if nx_graph.is_directed():
            undirected = nx_graph.to_undirected()
        else:
            undirected = nx_graph

        # Convert clusters to sets
        communities = [set(cluster.node_ids) for cluster in clusters]

        try:
            from networkx.algorithms.community import modularity

            return modularity(undirected, communities, weight=self.trust_weight)
        except Exception:
            return 0.0


__all__ = [
    "ClusteringMethod",
    "TrustCluster",
    "ClusterAnalyzer",
]
