"""
Anomaly detection in trust graphs.

Identifies suspicious patterns that may indicate trust manipulation,
configuration errors, or compromised nodes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from enum import Enum

import networkx as nx

if TYPE_CHECKING:
    from ..core.graph import TrustGraph
    from ..core.scoring import TrustScore


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected in trust graphs."""

    CIRCULAR_TRUST = "circular_trust"  # A trusts B trusts A
    TRUST_ISLAND = "trust_island"  # Disconnected component
    SUSPICIOUS_CONCENTRATION = "suspicious_concentration"  # Too many edges to one node
    TRUST_CLIFF = "trust_cliff"  # Sudden trust drop in path
    ORPHAN_NODE = "orphan_node"  # Node with no connections
    SELF_LOOP = "self_loop"  # Node trusts itself


@dataclass
class TrustAnomaly:
    """Represents a detected anomaly in the trust graph.

    Attributes:
        anomaly_type: The type of anomaly detected.
        severity: Severity score from 0-1, higher is more severe.
        affected_nodes: List of node IDs involved in the anomaly.
        affected_edges: List of edges (source, target) involved.
        description: Human-readable description of the anomaly.
        metadata: Additional context about the anomaly.
    """

    anomaly_type: AnomalyType
    severity: float  # 0-1, higher is more severe
    affected_nodes: List[str]
    affected_edges: List[tuple]
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate severity is in valid range."""
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError(f"Severity must be between 0 and 1, got {self.severity}")


class AnomalyDetector:
    """Detect anomalies in trust graphs.

    Identifies suspicious patterns that may indicate:
    - Trust manipulation
    - Configuration errors
    - Compromised nodes

    Example:
        >>> from rotalabs_graph.analysis import AnomalyDetector
        >>> detector = AnomalyDetector()
        >>> anomalies = detector.detect_all(graph)
        >>> for a in anomalies:
        ...     print(f"{a.anomaly_type}: {a.description}")
        circular_trust: Circular trust dependency detected involving 3 nodes
        trust_island: Disconnected component with 2 nodes

    Attributes:
        min_severity: Minimum severity threshold for reporting anomalies.
        detect_cycles: Whether to detect circular trust dependencies.
        detect_islands: Whether to detect disconnected components.
        detect_concentration: Whether to detect suspicious trust concentration.
    """

    def __init__(
        self,
        min_severity: float = 0.0,
        detect_cycles: bool = True,
        detect_islands: bool = True,
        detect_concentration: bool = True,
    ):
        """Initialize the anomaly detector.

        Args:
            min_severity: Minimum severity threshold for reporting anomalies (0-1).
            detect_cycles: Whether to detect circular trust dependencies.
            detect_islands: Whether to detect disconnected components.
            detect_concentration: Whether to detect suspicious trust concentration.
        """
        if not 0.0 <= min_severity <= 1.0:
            raise ValueError(f"min_severity must be between 0 and 1, got {min_severity}")

        self.min_severity = min_severity
        self._detect_cycles = detect_cycles
        self._detect_islands = detect_islands
        self._detect_concentration = detect_concentration

    def detect_all(self, graph: "TrustGraph") -> List[TrustAnomaly]:
        """Run all enabled anomaly detections.

        Args:
            graph: The trust graph to analyze.

        Returns:
            List of detected anomalies, filtered by min_severity.
        """
        anomalies: List[TrustAnomaly] = []

        # Always detect self-loops and orphans
        anomalies.extend(self.detect_self_loops(graph))
        anomalies.extend(self.detect_orphans(graph))

        if self._detect_cycles:
            anomalies.extend(self.detect_cycles(graph))

        if self._detect_islands:
            anomalies.extend(self.detect_islands(graph))

        if self._detect_concentration:
            anomalies.extend(self.detect_concentration(graph))

        # Filter by minimum severity
        return [a for a in anomalies if a.severity >= self.min_severity]

    def detect_cycles(self, graph: "TrustGraph") -> List[TrustAnomaly]:
        """Detect circular trust dependencies.

        Uses networkx cycle detection to find cycles in the trust graph.
        Circular trust can indicate mutual trust arrangements that bypass
        normal trust hierarchies.

        Args:
            graph: The trust graph to analyze.

        Returns:
            List of TrustAnomaly objects for each cycle detected.
        """
        anomalies = []
        nx_graph = graph.to_networkx()

        try:
            # Find all simple cycles
            cycles = list(nx.simple_cycles(nx_graph))
        except nx.NetworkXError:
            # Graph might not support cycle detection
            return anomalies

        for cycle in cycles:
            # Calculate severity based on cycle length
            # Shorter cycles are more severe (direct circular trust)
            if len(cycle) == 2:
                severity = 1.0  # Direct mutual trust
            elif len(cycle) == 3:
                severity = 0.8
            else:
                severity = max(0.3, 1.0 - (len(cycle) - 2) * 0.1)

            # Get edges in the cycle
            edges = []
            for i in range(len(cycle)):
                source = cycle[i]
                target = cycle[(i + 1) % len(cycle)]
                edges.append((source, target))

            anomalies.append(
                TrustAnomaly(
                    anomaly_type=AnomalyType.CIRCULAR_TRUST,
                    severity=severity,
                    affected_nodes=list(cycle),
                    affected_edges=edges,
                    description=f"Circular trust dependency detected involving {len(cycle)} nodes",
                    metadata={
                        "cycle_length": len(cycle),
                        "cycle_path": " -> ".join(cycle + [cycle[0]]),
                    },
                )
            )

        return anomalies

    def detect_islands(self, graph: "TrustGraph") -> List[TrustAnomaly]:
        """Detect disconnected trust components (islands).

        Trust islands are groups of nodes that have no trust relationships
        with the rest of the graph. This may indicate segmentation issues
        or nodes that were incorrectly added.

        Args:
            graph: The trust graph to analyze.

        Returns:
            List of TrustAnomaly objects for disconnected components.
        """
        anomalies = []
        nx_graph = graph.to_networkx()

        # Use weakly connected components for directed graphs
        if nx_graph.is_directed():
            components = list(nx.weakly_connected_components(nx_graph))
        else:
            components = list(nx.connected_components(nx_graph))

        if len(components) <= 1:
            return anomalies

        # Find the main component (largest)
        main_component = max(components, key=len)
        total_nodes = nx_graph.number_of_nodes()

        for component in components:
            if component == main_component:
                continue

            nodes = list(component)
            # Severity based on relative size and isolation
            component_size = len(nodes)
            size_ratio = component_size / total_nodes

            # Smaller isolated components are more suspicious
            severity = min(1.0, 0.5 + (1.0 - size_ratio) * 0.5)

            anomalies.append(
                TrustAnomaly(
                    anomaly_type=AnomalyType.TRUST_ISLAND,
                    severity=severity,
                    affected_nodes=nodes,
                    affected_edges=[],
                    description=f"Disconnected component with {len(nodes)} nodes",
                    metadata={
                        "component_size": component_size,
                        "total_components": len(components),
                        "size_ratio": size_ratio,
                    },
                )
            )

        return anomalies

    def detect_concentration(
        self,
        graph: "TrustGraph",
        threshold: float = 0.5,
    ) -> List[TrustAnomaly]:
        """Detect suspicious trust concentration.

        Identifies nodes that receive a disproportionate number of incoming
        trust edges, which could indicate trust manipulation or a
        compromised central authority.

        Args:
            graph: The trust graph to analyze.
            threshold: Maximum fraction of edges to one node before flagging.

        Returns:
            List of TrustAnomaly objects for nodes with concentrated trust.
        """
        anomalies = []
        nx_graph = graph.to_networkx()

        total_edges = nx_graph.number_of_edges()
        if total_edges == 0:
            return anomalies

        # Calculate in-degree for each node
        if nx_graph.is_directed():
            in_degrees = dict(nx_graph.in_degree())
        else:
            in_degrees = dict(nx_graph.degree())

        for node, in_degree in in_degrees.items():
            edge_fraction = in_degree / total_edges

            if edge_fraction >= threshold:
                # Get all incoming edges
                if nx_graph.is_directed():
                    incoming_edges = [(u, node) for u in nx_graph.predecessors(node)]
                    source_nodes = list(nx_graph.predecessors(node))
                else:
                    incoming_edges = [(u, node) for u in nx_graph.neighbors(node)]
                    source_nodes = list(nx_graph.neighbors(node))

                # Severity increases with concentration
                severity = min(1.0, (edge_fraction - threshold) / (1.0 - threshold) + 0.5)

                anomalies.append(
                    TrustAnomaly(
                        anomaly_type=AnomalyType.SUSPICIOUS_CONCENTRATION,
                        severity=severity,
                        affected_nodes=[node] + source_nodes,
                        affected_edges=incoming_edges,
                        description=f"Node '{node}' receives {edge_fraction:.1%} of all trust edges",
                        metadata={
                            "central_node": node,
                            "in_degree": in_degree,
                            "total_edges": total_edges,
                            "edge_fraction": edge_fraction,
                            "threshold": threshold,
                        },
                    )
                )

        return anomalies

    def detect_trust_cliffs(
        self,
        graph: "TrustGraph",
        scores: Dict[str, "TrustScore"],
        threshold: float = 0.5,
    ) -> List[TrustAnomaly]:
        """Detect sudden trust drops along paths.

        Identifies edges where trust drops significantly, which may indicate
        compromised nodes or misconfigured trust relationships.

        Args:
            graph: The trust graph to analyze.
            scores: Dictionary mapping node IDs to their trust scores.
            threshold: Minimum trust drop to flag as a cliff.

        Returns:
            List of TrustAnomaly objects for trust cliffs.
        """
        anomalies = []
        nx_graph = graph.to_networkx()

        for u, v in nx_graph.edges():
            if u not in scores or v not in scores:
                continue

            source_trust = scores[u].score if hasattr(scores[u], "score") else float(scores[u])
            target_trust = scores[v].score if hasattr(scores[v], "score") else float(scores[v])

            trust_drop = source_trust - target_trust

            if trust_drop >= threshold:
                # Severity based on magnitude of drop
                severity = min(1.0, trust_drop / 1.0)

                anomalies.append(
                    TrustAnomaly(
                        anomaly_type=AnomalyType.TRUST_CLIFF,
                        severity=severity,
                        affected_nodes=[u, v],
                        affected_edges=[(u, v)],
                        description=f"Trust drops {trust_drop:.2f} from '{u}' to '{v}'",
                        metadata={
                            "source_trust": source_trust,
                            "target_trust": target_trust,
                            "trust_drop": trust_drop,
                            "threshold": threshold,
                        },
                    )
                )

        return anomalies

    def detect_orphans(self, graph: "TrustGraph") -> List[TrustAnomaly]:
        """Detect orphan nodes with no connections.

        Orphan nodes have no incoming or outgoing trust relationships,
        which may indicate incomplete graph construction.

        Args:
            graph: The trust graph to analyze.

        Returns:
            List of TrustAnomaly objects for orphan nodes.
        """
        anomalies = []
        nx_graph = graph.to_networkx()

        for node in nx_graph.nodes():
            degree = nx_graph.degree(node)
            if degree == 0:
                anomalies.append(
                    TrustAnomaly(
                        anomaly_type=AnomalyType.ORPHAN_NODE,
                        severity=0.6,
                        affected_nodes=[node],
                        affected_edges=[],
                        description=f"Node '{node}' has no trust connections",
                        metadata={"node_id": node},
                    )
                )

        return anomalies

    def detect_self_loops(self, graph: "TrustGraph") -> List[TrustAnomaly]:
        """Detect self-loops where a node trusts itself.

        Self-loops are typically configuration errors and should be flagged.

        Args:
            graph: The trust graph to analyze.

        Returns:
            List of TrustAnomaly objects for self-loops.
        """
        anomalies = []
        nx_graph = graph.to_networkx()

        for node in nx_graph.nodes():
            if nx_graph.has_edge(node, node):
                anomalies.append(
                    TrustAnomaly(
                        anomaly_type=AnomalyType.SELF_LOOP,
                        severity=0.9,
                        affected_nodes=[node],
                        affected_edges=[(node, node)],
                        description=f"Node '{node}' has a self-trust loop",
                        metadata={"node_id": node},
                    )
                )

        return anomalies


__all__ = [
    "AnomalyType",
    "TrustAnomaly",
    "AnomalyDetector",
]
