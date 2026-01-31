"""Dynamic trust graph with temporal features.

This module extends the base TrustGraph with temporal dynamics:
- Trust decay over time
- History tracking for all changes
- Snapshot management for rollback/comparison

Example:
    >>> from rotalabs_graph.temporal import TemporalTrustGraph, DecayFunction
    >>> graph = TemporalTrustGraph(
    ...     decay_function=DecayFunction.EXPONENTIAL,
    ...     half_life_days=30.0
    ... )
    >>> graph.add_node("agent-1", initial_trust=0.9)
    >>> # 30 days later...
    >>> current_trust = graph.get_current_trust("agent-1")  # ~0.45
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import copy

from rotalabs_graph.temporal.decay import DecayFunction, get_decay_function
from rotalabs_graph.temporal.history import TrustHistory, TrustEvent


class TemporalTrustGraph:
    """Trust graph with temporal dynamics.

    Extends basic trust graph functionality with:
    - Automatic trust decay over time
    - Complete history tracking of all changes
    - Snapshot management for state preservation

    The graph maintains both the "last updated" timestamp for each
    node/edge and tracks all changes through the history system.

    Attributes:
        decay_function: Type of decay function to use
        half_life: Time in days for trust to decay to half
        history: TrustHistory instance (if tracking enabled)

    Example:
        >>> graph = TemporalTrustGraph(
        ...     decay_function=DecayFunction.EXPONENTIAL,
        ...     half_life_days=30.0,
        ...     track_history=True
        ... )
        >>> graph.add_node("agent-1", initial_trust=0.9)
        >>> graph.add_node("agent-2", initial_trust=0.8)
        >>> graph.add_edge("agent-1", "agent-2", weight=0.7)
        >>>
        >>> # Get current trust (with decay applied)
        >>> trust = graph.get_current_trust("agent-1")
        >>>
        >>> # Create snapshot before major changes
        >>> snapshot = graph.snapshot()
        >>> graph.update_trust("agent-1", 0.5, "manual_review")
        >>>
        >>> # Rollback if needed
        >>> graph.restore_snapshot(snapshot)
    """

    def __init__(
        self,
        decay_function: DecayFunction | str = DecayFunction.EXPONENTIAL,
        half_life_days: float = 30.0,
        track_history: bool = True,
        max_history_events: int = 10000,
    ):
        """Initialize a temporal trust graph.

        Args:
            decay_function: Type of decay function to use for trust decay.
                Can be a DecayFunction enum or string name.
            half_life_days: Number of days for trust to decay to half
                its original value.
            track_history: Whether to track all trust changes.
            max_history_events: Maximum history events to retain.

        Example:
            >>> graph = TemporalTrustGraph(
            ...     decay_function="exponential",
            ...     half_life_days=14.0,
            ...     track_history=True
            ... )
        """
        # Convert string to enum if needed
        if isinstance(decay_function, str):
            decay_function = DecayFunction(decay_function.lower())

        self.decay_function = decay_function
        self.half_life = half_life_days
        self._decay_fn = get_decay_function(decay_function)

        # History tracking
        self.history = TrustHistory(max_history_events) if track_history else None

        # Node data: {node_id: {"trust": float, "last_updated": datetime, "metadata": dict}}
        self._nodes: Dict[str, Dict[str, Any]] = {}

        # Edge data: {(source, target): {"weight": float, "last_updated": datetime, "metadata": dict}}
        self._edges: Dict[tuple, Dict[str, Any]] = {}

        # Creation timestamp
        self._created_at = datetime.now()

    @property
    def nodes(self) -> List[str]:
        """Get list of all node IDs."""
        return list(self._nodes.keys())

    @property
    def edges(self) -> List[tuple]:
        """Get list of all edge keys (source, target)."""
        return list(self._edges.keys())

    def add_node(
        self,
        node_id: str,
        initial_trust: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a node to the graph.

        Args:
            node_id: Unique identifier for the node
            initial_trust: Initial trust score (0.0 to 1.0)
            metadata: Additional node attributes

        Raises:
            ValueError: If node already exists or trust is invalid

        Example:
            >>> graph = TemporalTrustGraph()
            >>> graph.add_node("agent-1", initial_trust=0.9)
            >>> graph.add_node("agent-2", initial_trust=0.7, metadata={"type": "human"})
        """
        if node_id in self._nodes:
            raise ValueError(f"Node {node_id} already exists")

        initial_trust = self._validate_trust(initial_trust)

        now = datetime.now()
        self._nodes[node_id] = {
            "trust": initial_trust,
            "last_updated": now,
            "created_at": now,
            "metadata": metadata or {},
        }

        if self.history:
            self.history.record_creation(node_id, initial_trust)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an edge between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            weight: Edge weight/trust (0.0 to 1.0)
            metadata: Additional edge attributes

        Raises:
            ValueError: If edge exists or nodes don't exist

        Example:
            >>> graph = TemporalTrustGraph()
            >>> graph.add_node("agent-1", 0.9)
            >>> graph.add_node("agent-2", 0.8)
            >>> graph.add_edge("agent-1", "agent-2", weight=0.7)
        """
        if source_id not in self._nodes:
            raise ValueError(f"Source node {source_id} does not exist")
        if target_id not in self._nodes:
            raise ValueError(f"Target node {target_id} does not exist")

        edge_key = (source_id, target_id)
        if edge_key in self._edges:
            raise ValueError(f"Edge {edge_key} already exists")

        weight = self._validate_trust(weight)

        now = datetime.now()
        self._edges[edge_key] = {
            "weight": weight,
            "last_updated": now,
            "created_at": now,
            "metadata": metadata or {},
        }

        if self.history:
            self.history.record_edge_creation(source_id, target_id, weight)

    def get_raw_trust(self, node_id: str) -> float:
        """Get stored trust score without decay applied.

        Args:
            node_id: Node to get trust for

        Returns:
            Stored trust score

        Raises:
            KeyError: If node doesn't exist
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found")
        return self._nodes[node_id]["trust"]

    def get_current_trust(
        self,
        node_id: str,
        as_of: Optional[datetime] = None,
    ) -> float:
        """Get trust score with decay applied.

        Calculates the effective trust score at a point in time,
        accounting for temporal decay since the last update.

        Args:
            node_id: Node to get trust for
            as_of: Calculate trust as of this time (default: now)

        Returns:
            Decayed trust score

        Raises:
            KeyError: If node doesn't exist

        Example:
            >>> graph = TemporalTrustGraph(half_life_days=30)
            >>> graph.add_node("agent-1", initial_trust=0.8)
            >>> # Immediately after adding
            >>> graph.get_current_trust("agent-1")
            0.8
            >>> # Simulate 30 days later
            >>> from datetime import timedelta
            >>> future = datetime.now() + timedelta(days=30)
            >>> graph.get_current_trust("agent-1", as_of=future)
            0.4
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found")

        node = self._nodes[node_id]
        as_of = as_of or datetime.now()

        # Calculate time elapsed in days
        time_delta = as_of - node["last_updated"]
        days_elapsed = time_delta.total_seconds() / (24 * 3600)

        if days_elapsed < 0:
            # as_of is before last_updated, no decay
            days_elapsed = 0

        # Apply decay
        return self._decay_fn(node["trust"], days_elapsed, self.half_life)

    def get_edge_weight(
        self,
        source_id: str,
        target_id: str,
        as_of: Optional[datetime] = None,
    ) -> float:
        """Get edge weight with decay applied.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            as_of: Calculate weight as of this time (default: now)

        Returns:
            Decayed edge weight

        Raises:
            KeyError: If edge doesn't exist
        """
        edge_key = (source_id, target_id)
        if edge_key not in self._edges:
            raise KeyError(f"Edge {edge_key} not found")

        edge = self._edges[edge_key]
        as_of = as_of or datetime.now()

        time_delta = as_of - edge["last_updated"]
        days_elapsed = max(0, time_delta.total_seconds() / (24 * 3600))

        return self._decay_fn(edge["weight"], days_elapsed, self.half_life)

    def update_trust(
        self,
        node_id: str,
        new_trust: float,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Update a node's trust score.

        Updates the trust score and resets the decay timer.

        Args:
            node_id: Node to update
            new_trust: New trust score (0.0 to 1.0)
            reason: Explanation for the update
            metadata: Additional context for the update

        Returns:
            The old trust score (raw, not decayed)

        Raises:
            KeyError: If node doesn't exist

        Example:
            >>> graph = TemporalTrustGraph()
            >>> graph.add_node("agent-1", 0.9)
            >>> old = graph.update_trust("agent-1", 0.7, "behavior_anomaly")
            >>> old
            0.9
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found")

        new_trust = self._validate_trust(new_trust)
        old_trust = self._nodes[node_id]["trust"]

        self._nodes[node_id]["trust"] = new_trust
        self._nodes[node_id]["last_updated"] = datetime.now()

        if metadata:
            self._nodes[node_id]["metadata"].update(metadata)

        if self.history:
            self.history.record_update(node_id, old_trust, new_trust, reason, metadata)

        return old_trust

    def update_edge_weight(
        self,
        source_id: str,
        target_id: str,
        new_weight: float,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Update an edge's weight.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            new_weight: New edge weight (0.0 to 1.0)
            reason: Explanation for the update
            metadata: Additional context

        Returns:
            The old edge weight (raw, not decayed)
        """
        edge_key = (source_id, target_id)
        if edge_key not in self._edges:
            raise KeyError(f"Edge {edge_key} not found")

        new_weight = self._validate_trust(new_weight)
        old_weight = self._edges[edge_key]["weight"]

        self._edges[edge_key]["weight"] = new_weight
        self._edges[edge_key]["last_updated"] = datetime.now()

        if metadata:
            self._edges[edge_key]["metadata"].update(metadata)

        if self.history:
            self.history.record_edge_update(
                source_id, target_id, old_weight, new_weight, reason, metadata
            )

        return old_weight

    def apply_decay(
        self,
        as_of: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """Apply decay to all trust scores and update stored values.

        This persists the decayed values and resets the decay timers.
        Use this for periodic maintenance of the graph.

        Args:
            as_of: Calculate decay as of this time (default: now)

        Returns:
            Dictionary of {node_id: decayed_trust} for all nodes

        Example:
            >>> graph = TemporalTrustGraph()
            >>> graph.add_node("agent-1", 0.8)
            >>> # Simulate time passing
            >>> future = datetime.now() + timedelta(days=30)
            >>> decayed = graph.apply_decay(as_of=future)
            >>> decayed["agent-1"]
            0.4
        """
        as_of = as_of or datetime.now()
        results = {}

        for node_id in self._nodes:
            old_trust = self._nodes[node_id]["trust"]
            new_trust = self.get_current_trust(node_id, as_of=as_of)

            if new_trust != old_trust:
                time_delta = as_of - self._nodes[node_id]["last_updated"]
                days_elapsed = time_delta.total_seconds() / (24 * 3600)

                self._nodes[node_id]["trust"] = new_trust
                self._nodes[node_id]["last_updated"] = as_of

                if self.history:
                    self.history.record_decay(
                        node_id,
                        old_trust,
                        new_trust,
                        days_elapsed,
                        self.decay_function.value,
                    )

            results[node_id] = new_trust

        # Also decay edges
        for edge_key in self._edges:
            old_weight = self._edges[edge_key]["weight"]
            new_weight = self.get_edge_weight(*edge_key, as_of=as_of)

            if new_weight != old_weight:
                self._edges[edge_key]["weight"] = new_weight
                self._edges[edge_key]["last_updated"] = as_of

        return results

    def snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of current trust state.

        Captures the complete state of the graph including:
        - All nodes with their trust scores and metadata
        - All edges with their weights and metadata
        - Configuration parameters

        Returns:
            Dictionary containing full graph state

        Example:
            >>> graph = TemporalTrustGraph()
            >>> graph.add_node("agent-1", 0.9)
            >>> snapshot = graph.snapshot()
            >>> snapshot["nodes"]["agent-1"]["trust"]
            0.9
        """
        return {
            "created_at": datetime.now().isoformat(),
            "config": {
                "decay_function": self.decay_function.value,
                "half_life_days": self.half_life,
            },
            "nodes": {
                node_id: {
                    "trust": data["trust"],
                    "last_updated": data["last_updated"].isoformat(),
                    "created_at": data["created_at"].isoformat(),
                    "metadata": copy.deepcopy(data["metadata"]),
                }
                for node_id, data in self._nodes.items()
            },
            "edges": {
                f"{src}:{tgt}": {
                    "source": src,
                    "target": tgt,
                    "weight": data["weight"],
                    "last_updated": data["last_updated"].isoformat(),
                    "created_at": data["created_at"].isoformat(),
                    "metadata": copy.deepcopy(data["metadata"]),
                }
                for (src, tgt), data in self._edges.items()
            },
        }

    def restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore from a snapshot.

        Replaces the current graph state with the snapshot state.
        History is preserved but a restore event is not recorded.

        Args:
            snapshot: Snapshot dictionary from snapshot()

        Example:
            >>> graph = TemporalTrustGraph()
            >>> graph.add_node("agent-1", 0.9)
            >>> snapshot = graph.snapshot()
            >>> graph.update_trust("agent-1", 0.5, "test")
            >>> graph.restore_snapshot(snapshot)
            >>> graph.get_raw_trust("agent-1")
            0.9
        """
        # Clear current state
        self._nodes.clear()
        self._edges.clear()

        # Restore nodes
        for node_id, data in snapshot.get("nodes", {}).items():
            self._nodes[node_id] = {
                "trust": data["trust"],
                "last_updated": datetime.fromisoformat(data["last_updated"]),
                "created_at": datetime.fromisoformat(data["created_at"]),
                "metadata": copy.deepcopy(data.get("metadata", {})),
            }

        # Restore edges
        for edge_data in snapshot.get("edges", {}).values():
            edge_key = (edge_data["source"], edge_data["target"])
            self._edges[edge_key] = {
                "weight": edge_data["weight"],
                "last_updated": datetime.fromisoformat(edge_data["last_updated"]),
                "created_at": datetime.fromisoformat(edge_data["created_at"]),
                "metadata": copy.deepcopy(edge_data.get("metadata", {})),
            }

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "outgoing",
    ) -> List[str]:
        """Get neighboring nodes.

        Args:
            node_id: Node to get neighbors for
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of neighbor node IDs
        """
        neighbors = set()

        for (src, tgt) in self._edges:
            if direction in ("outgoing", "both") and src == node_id:
                neighbors.add(tgt)
            if direction in ("incoming", "both") and tgt == node_id:
                neighbors.add(src)

        return list(neighbors)

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges.

        Args:
            node_id: Node to remove

        Raises:
            KeyError: If node doesn't exist
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found")

        # Remove associated edges
        edges_to_remove = [
            key for key in self._edges
            if node_id in key
        ]
        for edge_key in edges_to_remove:
            del self._edges[edge_key]

        del self._nodes[node_id]

    def remove_edge(self, source_id: str, target_id: str) -> None:
        """Remove an edge.

        Args:
            source_id: Source node ID
            target_id: Target node ID

        Raises:
            KeyError: If edge doesn't exist
        """
        edge_key = (source_id, target_id)
        if edge_key not in self._edges:
            raise KeyError(f"Edge {edge_key} not found")
        del self._edges[edge_key]

    def _validate_trust(self, value: float) -> float:
        """Validate and clamp trust value to [0, 1]."""
        if not isinstance(value, (int, float)):
            raise TypeError(f"Trust must be numeric, got {type(value)}")
        return max(0.0, min(1.0, float(value)))

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary for serialization."""
        return self.snapshot()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemporalTrustGraph":
        """Create graph from dictionary.

        Args:
            data: Dictionary from to_dict() or snapshot()

        Returns:
            TemporalTrustGraph instance
        """
        config = data.get("config", {})
        graph = cls(
            decay_function=config.get("decay_function", "exponential"),
            half_life_days=config.get("half_life_days", 30.0),
            track_history=True,
        )
        graph.restore_snapshot(data)
        return graph

    def __len__(self) -> int:
        """Return the number of nodes."""
        return len(self._nodes)

    def __contains__(self, node_id: str) -> bool:
        """Check if node exists."""
        return node_id in self._nodes

    def __repr__(self) -> str:
        return (
            f"TemporalTrustGraph(nodes={len(self._nodes)}, "
            f"edges={len(self._edges)}, "
            f"decay={self.decay_function.value}, "
            f"half_life={self.half_life}d)"
        )
