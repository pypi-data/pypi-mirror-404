"""Core TrustGraph implementation.

This module provides the main TrustGraph class, which is the central
data structure for representing and manipulating trust graphs.

Example:
    >>> from rotalabs_graph import TrustGraph, TrustNode, TrustEdge, NodeType, EdgeType
    >>>
    >>> # Create a graph
    >>> graph = TrustGraph()
    >>>
    >>> # Add nodes
    >>> user = TrustNode(id="user-1", name="Alice", node_type=NodeType.USER)
    >>> agent = TrustNode(id="agent-1", name="Assistant", node_type=NodeType.AGENT)
    >>> model = TrustNode(id="model-1", name="GPT-4", node_type=NodeType.MODEL, base_trust=0.95)
    >>>
    >>> graph.add_node(user)
    >>> graph.add_node(agent)
    >>> graph.add_node(model)
    >>>
    >>> # Add edges
    >>> graph.add_edge(TrustEdge(
    ...     source_id="user-1",
    ...     target_id="agent-1",
    ...     edge_type=EdgeType.TRUSTS,
    ...     weight=0.9
    ... ))
    >>> graph.add_edge(TrustEdge(
    ...     source_id="agent-1",
    ...     target_id="model-1",
    ...     edge_type=EdgeType.CALLS,
    ...     weight=0.85
    ... ))
    >>>
    >>> # Query the graph
    >>> print(f"Graph has {graph.num_nodes} nodes and {graph.num_edges} edges")
    Graph has 3 nodes and 2 edges
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import networkx as nx

from rotalabs_graph.core.config import GraphConfig
from rotalabs_graph.core.exceptions import (
    EdgeNotFoundError,
    NodeNotFoundError,
    ValidationError,
)
from rotalabs_graph.core.types import EdgeType, NodeType, TrustEdge, TrustNode, TrustScore


class TrustGraph:
    """Core trust graph data structure.

    TrustGraph provides a high-level interface for building and querying
    trust graphs in AI systems. It uses networkx internally for graph
    algorithms while providing type-safe access to trust-specific data.

    Attributes:
        config: Configuration for graph behavior.

    Example:
        >>> graph = TrustGraph()
        >>> graph.add_node(TrustNode(
        ...     id="model-1",
        ...     name="GPT-4",
        ...     node_type=NodeType.MODEL
        ... ))
        >>> graph.num_nodes
        1
    """

    def __init__(
        self,
        directed: bool = True,
        config: Optional[GraphConfig] = None,
    ) -> None:
        """Initialize a TrustGraph.

        Args:
            directed: Whether the graph is directed. In directed graphs,
                edges have a direction (source -> target). Default: True.
            config: Optional GraphConfig for additional settings. If not
                provided, default config is used with the specified
                directed parameter.

        Example:
            >>> graph = TrustGraph(directed=True)
            >>> undirected_graph = TrustGraph(directed=False)
        """
        if config is not None:
            self.config = config
            directed = config.directed
        else:
            self.config = GraphConfig(directed=directed)

        self._graph: Union[nx.DiGraph, nx.Graph] = (
            nx.DiGraph() if directed else nx.Graph()
        )
        self._nodes: Dict[str, TrustNode] = {}
        self._edges: Dict[str, TrustEdge] = {}
        self._trust_scores: Dict[str, TrustScore] = {}
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def add_node(self, node: TrustNode) -> str:
        """Add a node to the graph.

        If a node with the same ID already exists, it will be updated.

        Args:
            node: The TrustNode to add.

        Returns:
            The ID of the added node.

        Raises:
            ValidationError: If the node data is invalid.

        Example:
            >>> node = TrustNode(
            ...     id="model-gpt4",
            ...     name="GPT-4",
            ...     node_type=NodeType.MODEL,
            ...     base_trust=0.95
            ... )
            >>> node_id = graph.add_node(node)
            >>> print(node_id)
            'model-gpt4'
        """
        # Validate node
        if not node.id:
            raise ValidationError("id", node.id, "Node ID cannot be empty")

        # Update timestamps for existing nodes
        if node.id in self._nodes:
            node = TrustNode(
                id=node.id,
                name=node.name,
                node_type=node.node_type,
                base_trust=node.base_trust,
                metadata=node.metadata,
                created_at=self._nodes[node.id].created_at,
                updated_at=datetime.now(timezone.utc),
            )

        self._nodes[node.id] = node
        self._graph.add_node(
            node.id,
            name=node.name,
            node_type=node.node_type.value,
            base_trust=node.base_trust,
            metadata=node.metadata,
        )

        self.updated_at = datetime.now(timezone.utc)
        return node.id

    def add_edge(self, edge: TrustEdge) -> str:
        """Add an edge to the graph.

        Both source and target nodes must exist in the graph.

        Args:
            edge: The TrustEdge to add.

        Returns:
            The edge ID (format: "source_id|edge_type|target_id").

        Raises:
            NodeNotFoundError: If source or target node doesn't exist.
            ValidationError: If the edge would violate graph constraints.

        Example:
            >>> edge = TrustEdge(
            ...     source_id="user-1",
            ...     target_id="agent-1",
            ...     edge_type=EdgeType.TRUSTS,
            ...     weight=0.9
            ... )
            >>> edge_id = graph.add_edge(edge)
        """
        # Validate nodes exist
        if edge.source_id not in self._nodes:
            raise NodeNotFoundError(edge.source_id)
        if edge.target_id not in self._nodes:
            raise NodeNotFoundError(edge.target_id)

        # Check self-loop constraint
        if not self.config.allow_self_loops and edge.source_id == edge.target_id:
            raise ValidationError(
                "edge",
                f"{edge.source_id} -> {edge.target_id}",
                "Self-loops are not allowed",
            )

        # Check multi-edge constraint
        edge_id = edge.edge_id
        if not self.config.allow_multi_edges:
            # Check if any edge exists between these nodes
            for existing_id in self._edges:
                if existing_id.startswith(f"{edge.source_id}|") and existing_id.endswith(
                    f"|{edge.target_id}"
                ):
                    if existing_id != edge_id:
                        raise ValidationError(
                            "edge",
                            f"{edge.source_id} -> {edge.target_id}",
                            f"Multi-edges not allowed; edge already exists: {existing_id}",
                        )

        self._edges[edge_id] = edge
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            edge_type=edge.edge_type.value,
            weight=edge.weight,
            metadata=edge.metadata,
            edge_id=edge_id,
        )

        self.updated_at = datetime.now(timezone.utc)
        return edge_id

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its connected edges from the graph.

        Args:
            node_id: ID of the node to remove.

        Returns:
            True if the node was removed, False if it didn't exist.

        Example:
            >>> graph.remove_node("model-1")
            True
            >>> graph.remove_node("nonexistent")
            False
        """
        if node_id not in self._nodes:
            return False

        # Remove all edges connected to this node
        edges_to_remove = [
            edge_id
            for edge_id, edge in self._edges.items()
            if edge.source_id == node_id or edge.target_id == node_id
        ]
        for edge_id in edges_to_remove:
            del self._edges[edge_id]

        # Remove node
        del self._nodes[node_id]
        self._graph.remove_node(node_id)

        # Remove trust score if exists
        if node_id in self._trust_scores:
            del self._trust_scores[node_id]

        self.updated_at = datetime.now(timezone.utc)
        return True

    def remove_edge(
        self, source_id: str, target_id: str, edge_type: Optional[EdgeType] = None
    ) -> bool:
        """Remove an edge from the graph.

        Args:
            source_id: ID of the source node.
            target_id: ID of the target node.
            edge_type: Optional edge type. If not provided and multiple edges
                exist between the nodes, all will be removed.

        Returns:
            True if any edge was removed, False if no matching edge existed.

        Example:
            >>> graph.remove_edge("user-1", "agent-1")
            True
            >>> graph.remove_edge("user-1", "agent-1", EdgeType.TRUSTS)
            True
        """
        removed = False

        if edge_type is not None:
            # Remove specific edge type
            edge_id = f"{source_id}|{edge_type.value}|{target_id}"
            if edge_id in self._edges:
                del self._edges[edge_id]
                removed = True
        else:
            # Remove all edges between these nodes
            edges_to_remove = [
                edge_id
                for edge_id in self._edges
                if edge_id.startswith(f"{source_id}|") and edge_id.endswith(f"|{target_id}")
            ]
            for edge_id in edges_to_remove:
                del self._edges[edge_id]
                removed = True

        # Update networkx graph
        if removed and self._graph.has_edge(source_id, target_id):
            self._graph.remove_edge(source_id, target_id)

        if removed:
            self.updated_at = datetime.now(timezone.utc)

        return removed

    def get_node(self, node_id: str) -> Optional[TrustNode]:
        """Get a node by its ID.

        Args:
            node_id: ID of the node to retrieve.

        Returns:
            The TrustNode if found, None otherwise.

        Example:
            >>> node = graph.get_node("model-1")
            >>> if node:
            ...     print(f"Found: {node.name}")
        """
        return self._nodes.get(node_id)

    def get_node_or_raise(self, node_id: str) -> TrustNode:
        """Get a node by its ID, raising an exception if not found.

        Args:
            node_id: ID of the node to retrieve.

        Returns:
            The TrustNode.

        Raises:
            NodeNotFoundError: If the node doesn't exist.

        Example:
            >>> try:
            ...     node = graph.get_node_or_raise("model-1")
            ... except NodeNotFoundError:
            ...     print("Node not found!")
        """
        node = self._nodes.get(node_id)
        if node is None:
            raise NodeNotFoundError(node_id)
        return node

    def get_edge(
        self, source_id: str, target_id: str, edge_type: Optional[EdgeType] = None
    ) -> Optional[TrustEdge]:
        """Get an edge between two nodes.

        Args:
            source_id: ID of the source node.
            target_id: ID of the target node.
            edge_type: Optional edge type. If not provided and multiple edges
                exist, returns the first one found.

        Returns:
            The TrustEdge if found, None otherwise.

        Example:
            >>> edge = graph.get_edge("user-1", "agent-1")
            >>> edge = graph.get_edge("user-1", "agent-1", EdgeType.TRUSTS)
        """
        if edge_type is not None:
            edge_id = f"{source_id}|{edge_type.value}|{target_id}"
            return self._edges.get(edge_id)

        # Find any edge between these nodes
        for edge_id, edge in self._edges.items():
            if edge.source_id == source_id and edge.target_id == target_id:
                return edge

        return None

    def get_edge_or_raise(
        self, source_id: str, target_id: str, edge_type: Optional[EdgeType] = None
    ) -> TrustEdge:
        """Get an edge, raising an exception if not found.

        Args:
            source_id: ID of the source node.
            target_id: ID of the target node.
            edge_type: Optional edge type.

        Returns:
            The TrustEdge.

        Raises:
            EdgeNotFoundError: If the edge doesn't exist.
        """
        edge = self.get_edge(source_id, target_id, edge_type)
        if edge is None:
            raise EdgeNotFoundError(source_id, target_id)
        return edge

    def has_node(self, node_id: str) -> bool:
        """Check if a node exists in the graph.

        Args:
            node_id: ID of the node to check.

        Returns:
            True if the node exists.
        """
        return node_id in self._nodes

    def has_edge(self, source_id: str, target_id: str) -> bool:
        """Check if an edge exists between two nodes.

        Args:
            source_id: ID of the source node.
            target_id: ID of the target node.

        Returns:
            True if any edge exists between the nodes.
        """
        return self.get_edge(source_id, target_id) is not None

    def get_neighbors(self, node_id: str, direction: str = "out") -> List[TrustNode]:
        """Get neighboring nodes.

        Args:
            node_id: ID of the node.
            direction: Direction of edges to follow. Options:
                - "out": Nodes this node points to (successors).
                - "in": Nodes pointing to this node (predecessors).
                - "both": All connected nodes.

        Returns:
            List of neighboring TrustNodes.

        Raises:
            NodeNotFoundError: If the node doesn't exist.
            ValueError: If direction is invalid.

        Example:
            >>> successors = graph.get_neighbors("user-1", direction="out")
            >>> predecessors = graph.get_neighbors("model-1", direction="in")
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)

        if direction == "out":
            neighbor_ids = (
                list(self._graph.successors(node_id))
                if self.is_directed
                else list(self._graph.neighbors(node_id))
            )
        elif direction == "in":
            neighbor_ids = (
                list(self._graph.predecessors(node_id))
                if self.is_directed
                else list(self._graph.neighbors(node_id))
            )
        elif direction == "both":
            if self.is_directed:
                neighbor_ids = list(
                    set(self._graph.successors(node_id))
                    | set(self._graph.predecessors(node_id))
                )
            else:
                neighbor_ids = list(self._graph.neighbors(node_id))
        else:
            raise ValueError(
                f"Invalid direction: {direction}. Must be 'out', 'in', or 'both'"
            )

        return [self._nodes[nid] for nid in neighbor_ids]

    def get_predecessors(self, node_id: str) -> List[TrustNode]:
        """Get nodes that have edges pointing to this node.

        Args:
            node_id: ID of the node.

        Returns:
            List of predecessor TrustNodes.

        Raises:
            NodeNotFoundError: If the node doesn't exist.

        Example:
            >>> predecessors = graph.get_predecessors("model-1")
            >>> for p in predecessors:
            ...     print(f"{p.name} trusts {graph.get_node('model-1').name}")
        """
        return self.get_neighbors(node_id, direction="in")

    def get_successors(self, node_id: str) -> List[TrustNode]:
        """Get nodes that this node has edges pointing to.

        Args:
            node_id: ID of the node.

        Returns:
            List of successor TrustNodes.

        Raises:
            NodeNotFoundError: If the node doesn't exist.

        Example:
            >>> successors = graph.get_successors("user-1")
        """
        return self.get_neighbors(node_id, direction="out")

    def get_nodes_by_type(self, node_type: NodeType) -> List[TrustNode]:
        """Get all nodes of a specific type.

        Args:
            node_type: The type of nodes to retrieve.

        Returns:
            List of TrustNodes matching the type.

        Example:
            >>> models = graph.get_nodes_by_type(NodeType.MODEL)
            >>> agents = graph.get_nodes_by_type(NodeType.AGENT)
        """
        return [node for node in self._nodes.values() if node.node_type == node_type]

    def get_edges_by_type(self, edge_type: EdgeType) -> List[TrustEdge]:
        """Get all edges of a specific type.

        Args:
            edge_type: The type of edges to retrieve.

        Returns:
            List of TrustEdges matching the type.

        Example:
            >>> trust_edges = graph.get_edges_by_type(EdgeType.TRUSTS)
            >>> call_edges = graph.get_edges_by_type(EdgeType.CALLS)
        """
        return [edge for edge in self._edges.values() if edge.edge_type == edge_type]

    def get_all_edges_between(self, source_id: str, target_id: str) -> List[TrustEdge]:
        """Get all edges between two nodes.

        Args:
            source_id: ID of the source node.
            target_id: ID of the target node.

        Returns:
            List of all TrustEdges between the nodes.

        Example:
            >>> edges = graph.get_all_edges_between("agent-1", "model-1")
        """
        return [
            edge
            for edge in self._edges.values()
            if edge.source_id == source_id and edge.target_id == target_id
        ]

    def get_trust_score(self, node_id: str) -> Optional[TrustScore]:
        """Get the computed trust score for a node.

        Args:
            node_id: ID of the node.

        Returns:
            The TrustScore if computed, None otherwise.
        """
        return self._trust_scores.get(node_id)

    def set_trust_score(self, node_id: str, score: TrustScore) -> None:
        """Set the trust score for a node.

        Args:
            node_id: ID of the node.
            score: The TrustScore to set.

        Raises:
            NodeNotFoundError: If the node doesn't exist.
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        self._trust_scores[node_id] = score
        self.updated_at = datetime.now(timezone.utc)

    def get_trust_scores(self) -> Dict[str, TrustScore]:
        """Get all trust scores.

        Returns:
            Dictionary mapping node IDs to TrustScores.
        """
        return dict(self._trust_scores)

    def clear_trust_scores(self) -> None:
        """Clear all computed trust scores."""
        self._trust_scores.clear()
        self.updated_at = datetime.now(timezone.utc)

    def subgraph(self, node_ids: List[str]) -> "TrustGraph":
        """Create a subgraph containing only the specified nodes.

        The subgraph will include all edges between the specified nodes.

        Args:
            node_ids: List of node IDs to include in the subgraph.

        Returns:
            A new TrustGraph containing only the specified nodes and
            edges between them.

        Example:
            >>> # Get subgraph of just models and agents
            >>> model_agent_ids = [n.id for n in graph.get_nodes_by_type(NodeType.MODEL)]
            >>> model_agent_ids += [n.id for n in graph.get_nodes_by_type(NodeType.AGENT)]
            >>> subgraph = graph.subgraph(model_agent_ids)
        """
        new_graph = TrustGraph(directed=self.is_directed, config=self.config)

        # Add nodes
        node_id_set = set(node_ids)
        for node_id in node_ids:
            if node_id in self._nodes:
                new_graph.add_node(copy.deepcopy(self._nodes[node_id]))

        # Add edges between included nodes
        for edge in self._edges.values():
            if edge.source_id in node_id_set and edge.target_id in node_id_set:
                new_graph.add_edge(copy.deepcopy(edge))

        return new_graph

    def to_networkx(self) -> Union[nx.DiGraph, nx.Graph]:
        """Convert to a networkx graph.

        Returns a copy of the internal networkx graph with all node and
        edge attributes.

        Returns:
            A networkx DiGraph (if directed) or Graph (if undirected).

        Example:
            >>> G = graph.to_networkx()
            >>> nx.pagerank(G)
        """
        return copy.deepcopy(self._graph)

    @classmethod
    def from_networkx(
        cls,
        G: Union[nx.DiGraph, nx.Graph],
        config: Optional[GraphConfig] = None,
    ) -> "TrustGraph":
        """Create a TrustGraph from a networkx graph.

        Nodes must have 'name' and 'node_type' attributes.
        Edges must have 'edge_type' attributes.

        Args:
            G: A networkx DiGraph or Graph.
            config: Optional graph configuration.

        Returns:
            A new TrustGraph.

        Raises:
            ValidationError: If required attributes are missing.

        Example:
            >>> import networkx as nx
            >>> G = nx.DiGraph()
            >>> G.add_node("n1", name="Node 1", node_type="model", base_trust=0.9)
            >>> G.add_edge("n1", "n2", edge_type="trusts", weight=0.8)
            >>> graph = TrustGraph.from_networkx(G)
        """
        directed = isinstance(G, nx.DiGraph)
        if config is None:
            config = GraphConfig(directed=directed)

        graph = cls(directed=directed, config=config)

        # Add nodes
        for node_id, attrs in G.nodes(data=True):
            if "name" not in attrs:
                raise ValidationError("name", None, f"Node {node_id} missing 'name' attribute")
            if "node_type" not in attrs:
                raise ValidationError(
                    "node_type", None, f"Node {node_id} missing 'node_type' attribute"
                )

            node = TrustNode(
                id=str(node_id),
                name=attrs["name"],
                node_type=NodeType(attrs["node_type"]),
                base_trust=attrs.get("base_trust", config.default_node_trust),
                metadata=attrs.get("metadata", {}),
            )
            graph.add_node(node)

        # Add edges
        for source, target, attrs in G.edges(data=True):
            if "edge_type" not in attrs:
                raise ValidationError(
                    "edge_type",
                    None,
                    f"Edge {source}->{target} missing 'edge_type' attribute",
                )

            edge = TrustEdge(
                source_id=str(source),
                target_id=str(target),
                edge_type=EdgeType(attrs["edge_type"]),
                weight=attrs.get("weight", config.default_edge_weight),
                metadata=attrs.get("metadata", {}),
            )
            graph.add_edge(edge)

        return graph

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the graph to a dictionary.

        Returns:
            Dictionary representation of the graph, suitable for JSON
            serialization.

        Example:
            >>> data = graph.to_dict()
            >>> import json
            >>> json_str = json.dumps(data)
        """
        return {
            "directed": self.is_directed,
            "config": {
                "directed": self.config.directed,
                "allow_self_loops": self.config.allow_self_loops,
                "allow_multi_edges": self.config.allow_multi_edges,
                "default_edge_weight": self.config.default_edge_weight,
                "default_node_trust": self.config.default_node_trust,
            },
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustGraph":
        """Create a TrustGraph from a dictionary.

        Args:
            data: Dictionary representation (as produced by to_dict).

        Returns:
            A new TrustGraph.

        Example:
            >>> import json
            >>> with open("graph.json") as f:
            ...     data = json.load(f)
            >>> graph = TrustGraph.from_dict(data)
        """
        config_data = data.get("config", {})
        config = GraphConfig(
            directed=config_data.get("directed", data.get("directed", True)),
            allow_self_loops=config_data.get("allow_self_loops", False),
            allow_multi_edges=config_data.get("allow_multi_edges", False),
            default_edge_weight=config_data.get("default_edge_weight", 1.0),
            default_node_trust=config_data.get("default_node_trust", 1.0),
        )

        graph = cls(config=config)

        # Add nodes
        for node_data in data.get("nodes", []):
            graph.add_node(TrustNode.from_dict(node_data))

        # Add edges
        for edge_data in data.get("edges", []):
            graph.add_edge(TrustEdge.from_dict(edge_data))

        return graph

    def to_adjacency_matrix(self, weighted: bool = True) -> Tuple[List[str], Any]:
        """Convert graph to adjacency matrix.

        Args:
            weighted: Whether to use edge weights (default True).

        Returns:
            Tuple of (node_ids, adjacency_matrix as numpy array).

        Raises:
            ImportError: If numpy is not available.
        """
        try:
            import numpy as np
        except ImportError:
            raise ImportError("numpy is required for adjacency matrix conversion")

        node_ids = list(self._nodes.keys())
        n = len(node_ids)
        node_to_idx = {node_id: i for i, node_id in enumerate(node_ids)}

        matrix = np.zeros((n, n))
        for edge in self._edges.values():
            i = node_to_idx[edge.source_id]
            j = node_to_idx[edge.target_id]
            matrix[i, j] = edge.weight if weighted else 1.0

        return node_ids, matrix

    def copy(self) -> "TrustGraph":
        """Create a deep copy of this graph.

        Returns:
            A new TrustGraph with the same nodes and edges.
        """
        new_graph = TrustGraph(directed=self.is_directed, config=self.config)

        # Copy nodes
        for node in self._nodes.values():
            new_graph.add_node(copy.deepcopy(node))

        # Copy edges
        for edge in self._edges.values():
            new_graph.add_edge(copy.deepcopy(edge))

        # Copy trust scores
        for node_id, score in self._trust_scores.items():
            new_graph._trust_scores[node_id] = copy.deepcopy(score)

        return new_graph

    def __iter__(self) -> Iterator[TrustNode]:
        """Iterate over all nodes in the graph.

        Returns:
            Iterator of TrustNodes.

        Example:
            >>> for node in graph:
            ...     print(node.name)
        """
        return iter(self._nodes.values())

    def __len__(self) -> int:
        """Return the number of nodes in the graph.

        Returns:
            Number of nodes.
        """
        return len(self._nodes)

    def __contains__(self, node_id: str) -> bool:
        """Check if a node exists in the graph.

        Args:
            node_id: ID of the node to check.

        Returns:
            True if the node exists.

        Example:
            >>> if "model-1" in graph:
            ...     print("Node exists!")
        """
        return node_id in self._nodes

    @property
    def num_nodes(self) -> int:
        """Get the number of nodes in the graph.

        Returns:
            Number of nodes.

        Example:
            >>> print(f"Graph has {graph.num_nodes} nodes")
        """
        return len(self._nodes)

    @property
    def num_edges(self) -> int:
        """Get the number of edges in the graph.

        Returns:
            Number of edges.

        Example:
            >>> print(f"Graph has {graph.num_edges} edges")
        """
        return len(self._edges)

    @property
    def is_directed(self) -> bool:
        """Check if the graph is directed.

        Returns:
            True if the graph is directed.

        Example:
            >>> if graph.is_directed:
            ...     print("This is a directed graph")
        """
        return isinstance(self._graph, nx.DiGraph)

    @property
    def nodes(self) -> List[TrustNode]:
        """Get all nodes in the graph.

        Returns:
            List of all TrustNodes.

        Example:
            >>> for node in graph.nodes:
            ...     print(f"{node.id}: {node.name}")
        """
        return list(self._nodes.values())

    @property
    def edges(self) -> List[TrustEdge]:
        """Get all edges in the graph.

        Returns:
            List of all TrustEdges.

        Example:
            >>> for edge in graph.edges:
            ...     print(f"{edge.source_id} -> {edge.target_id}")
        """
        return list(self._edges.values())

    def node_ids(self) -> List[str]:
        """Get all node IDs in the graph.

        Returns:
            List of all node IDs.

        Example:
            >>> for node_id in graph.node_ids():
            ...     print(node_id)
        """
        return list(self._nodes.keys())

    @property
    def nx_graph(self) -> Union[nx.DiGraph, nx.Graph]:
        """Get the underlying NetworkX graph.

        Returns:
            The internal NetworkX graph (DiGraph or Graph).

        Example:
            >>> G = graph.nx_graph
            >>> nx.pagerank(G)
        """
        return self._graph

    def __repr__(self) -> str:
        """Return string representation of the graph."""
        graph_type = "directed" if self.is_directed else "undirected"
        return f"TrustGraph({graph_type}, nodes={self.num_nodes}, edges={self.num_edges})"
