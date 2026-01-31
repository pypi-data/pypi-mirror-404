"""Trust history tracking for temporal analysis and auditing.

This module provides tools for recording and querying trust changes
over time. Every trust modification can be tracked with context,
enabling temporal analysis and audit trails.

Example:
    >>> from rotalabs_graph.temporal.history import TrustHistory
    >>> history = TrustHistory()
    >>> history.record_creation("agent-1", 0.9)
    >>> history.record_update("agent-1", 0.9, 0.7, "anomaly_detected")
    >>> events = history.get_events("agent-1")
    >>> len(events)
    2
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


@dataclass
class TrustEvent:
    """A single trust change event.

    Represents a point-in-time record of a trust modification,
    including the context and reason for the change.

    Attributes:
        timestamp: When the event occurred
        event_type: Type of event ("created", "updated", "computed", "decayed")
        node_id: ID of the affected node (if applicable)
        edge_key: Tuple of (source, target) for edge events (if applicable)
        old_value: Previous trust value (None for creation events)
        new_value: New trust value after the change
        reason: Human-readable explanation for the change
        metadata: Additional context (optional)

    Example:
        >>> from datetime import datetime
        >>> event = TrustEvent(
        ...     timestamp=datetime.now(),
        ...     event_type="updated",
        ...     node_id="agent-1",
        ...     edge_key=None,
        ...     old_value=0.9,
        ...     new_value=0.7,
        ...     reason="anomaly_detected"
        ... )
        >>> event.delta
        -0.2
    """

    timestamp: datetime
    event_type: str  # "created", "updated", "computed", "decayed", "edge_created", "edge_updated"
    node_id: Optional[str]
    edge_key: Optional[tuple]  # (source_id, target_id)
    old_value: Optional[float]
    new_value: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def delta(self) -> Optional[float]:
        """Calculate the change in trust value.

        Returns:
            The difference between new and old values,
            or None if there was no previous value.
        """
        if self.old_value is None:
            return None
        return self.new_value - self.old_value

    @property
    def is_node_event(self) -> bool:
        """Check if this event is for a node."""
        return self.node_id is not None

    @property
    def is_edge_event(self) -> bool:
        """Check if this event is for an edge."""
        return self.edge_key is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization.

        Returns:
            Dictionary representation of the event
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "node_id": self.node_id,
            "edge_key": list(self.edge_key) if self.edge_key else None,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrustEvent":
        """Create event from dictionary.

        Args:
            data: Dictionary representation of event

        Returns:
            TrustEvent instance
        """
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=data["event_type"],
            node_id=data.get("node_id"),
            edge_key=tuple(data["edge_key"]) if data.get("edge_key") else None,
            old_value=data.get("old_value"),
            new_value=data["new_value"],
            reason=data["reason"],
            metadata=data.get("metadata", {}),
        )


class TrustHistory:
    """Track trust changes over time.

    Maintains a history of trust events for auditing
    and temporal analysis. Events are stored in chronological
    order and can be queried by node, time range, or event type.

    The history has a configurable maximum size to prevent
    unbounded memory growth. When the limit is reached, oldest
    events are discarded.

    Attributes:
        max_events: Maximum number of events to retain

    Example:
        >>> history = TrustHistory(max_events=1000)
        >>> history.record_creation("node-1", 0.9)
        >>> history.record_update("node-1", 0.9, 0.7, "behavior_anomaly")
        >>> events = history.get_events("node-1")
        >>> len(events)
        2
        >>> timeline = history.get_trust_timeline("node-1")
        >>> timeline[-1]  # Most recent (timestamp, trust)
        (datetime(...), 0.7)
    """

    def __init__(self, max_events: int = 10000):
        """Initialize trust history tracker.

        Args:
            max_events: Maximum number of events to retain.
                When exceeded, oldest events are discarded.
        """
        self.max_events = max_events
        self._events: List[TrustEvent] = []
        self._node_index: Dict[str, List[int]] = {}  # node_id -> event indices
        self._edge_index: Dict[tuple, List[int]] = {}  # edge_key -> event indices

    def __len__(self) -> int:
        """Return the number of recorded events."""
        return len(self._events)

    def _add_event(self, event: TrustEvent) -> None:
        """Add an event and update indices.

        Args:
            event: The event to add
        """
        # Enforce max events limit
        if len(self._events) >= self.max_events:
            self._trim_oldest()

        idx = len(self._events)
        self._events.append(event)

        # Update node index
        if event.node_id:
            if event.node_id not in self._node_index:
                self._node_index[event.node_id] = []
            self._node_index[event.node_id].append(idx)

        # Update edge index
        if event.edge_key:
            if event.edge_key not in self._edge_index:
                self._edge_index[event.edge_key] = []
            self._edge_index[event.edge_key].append(idx)

    def _trim_oldest(self, trim_count: int = 1000) -> None:
        """Remove oldest events to stay within limit.

        Args:
            trim_count: Number of events to remove
        """
        # Remove oldest events
        self._events = self._events[trim_count:]

        # Rebuild indices
        self._node_index.clear()
        self._edge_index.clear()
        for idx, event in enumerate(self._events):
            if event.node_id:
                if event.node_id not in self._node_index:
                    self._node_index[event.node_id] = []
                self._node_index[event.node_id].append(idx)
            if event.edge_key:
                if event.edge_key not in self._edge_index:
                    self._edge_index[event.edge_key] = []
                self._edge_index[event.edge_key].append(idx)

    def record_creation(
        self,
        node_id: str,
        initial_trust: float,
        reason: str = "node_created",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TrustEvent:
        """Record a node creation event.

        Args:
            node_id: ID of the created node
            initial_trust: Initial trust score assigned
            reason: Explanation for the creation
            metadata: Additional context

        Returns:
            The recorded TrustEvent

        Example:
            >>> history = TrustHistory()
            >>> event = history.record_creation("agent-1", 0.5, "new_agent_onboarded")
            >>> event.event_type
            'created'
        """
        event = TrustEvent(
            timestamp=datetime.now(),
            event_type="created",
            node_id=node_id,
            edge_key=None,
            old_value=None,
            new_value=initial_trust,
            reason=reason,
            metadata=metadata or {},
        )
        self._add_event(event)
        return event

    def record_update(
        self,
        node_id: str,
        old_value: float,
        new_value: float,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TrustEvent:
        """Record a node trust update event.

        Args:
            node_id: ID of the updated node
            old_value: Previous trust score
            new_value: New trust score
            reason: Explanation for the update
            metadata: Additional context

        Returns:
            The recorded TrustEvent

        Example:
            >>> history = TrustHistory()
            >>> event = history.record_update(
            ...     "agent-1", 0.9, 0.7, "anomaly_detected",
            ...     metadata={"anomaly_type": "trust_spike"}
            ... )
            >>> event.delta
            -0.2
        """
        event = TrustEvent(
            timestamp=datetime.now(),
            event_type="updated",
            node_id=node_id,
            edge_key=None,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            metadata=metadata or {},
        )
        self._add_event(event)
        return event

    def record_decay(
        self,
        node_id: str,
        old_value: float,
        new_value: float,
        days_elapsed: float,
        decay_function: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TrustEvent:
        """Record a trust decay event.

        Args:
            node_id: ID of the node with decayed trust
            old_value: Trust before decay
            new_value: Trust after decay
            days_elapsed: Time since last update
            decay_function: Name of decay function used
            metadata: Additional context

        Returns:
            The recorded TrustEvent

        Example:
            >>> history = TrustHistory()
            >>> event = history.record_decay(
            ...     "agent-1", 0.8, 0.4, 30.0, "exponential"
            ... )
            >>> event.event_type
            'decayed'
        """
        event_metadata = {
            "days_elapsed": days_elapsed,
            "decay_function": decay_function,
            **(metadata or {}),
        }
        event = TrustEvent(
            timestamp=datetime.now(),
            event_type="decayed",
            node_id=node_id,
            edge_key=None,
            old_value=old_value,
            new_value=new_value,
            reason="trust_decay",
            metadata=event_metadata,
        )
        self._add_event(event)
        return event

    def record_computation(
        self,
        node_id: str,
        old_value: float,
        new_value: float,
        algorithm: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TrustEvent:
        """Record a trust computation/propagation event.

        Args:
            node_id: ID of the node with computed trust
            old_value: Trust before computation
            new_value: Trust after computation
            algorithm: Name of propagation algorithm used
            metadata: Additional context

        Returns:
            The recorded TrustEvent

        Example:
            >>> history = TrustHistory()
            >>> event = history.record_computation(
            ...     "agent-1", 0.5, 0.75, "pagerank"
            ... )
            >>> event.event_type
            'computed'
        """
        event_metadata = {
            "algorithm": algorithm,
            **(metadata or {}),
        }
        event = TrustEvent(
            timestamp=datetime.now(),
            event_type="computed",
            node_id=node_id,
            edge_key=None,
            old_value=old_value,
            new_value=new_value,
            reason="trust_propagation",
            metadata=event_metadata,
        )
        self._add_event(event)
        return event

    def record_edge_creation(
        self,
        source_id: str,
        target_id: str,
        initial_weight: float,
        reason: str = "edge_created",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TrustEvent:
        """Record an edge creation event.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            initial_weight: Initial edge weight/trust
            reason: Explanation for the creation
            metadata: Additional context

        Returns:
            The recorded TrustEvent

        Example:
            >>> history = TrustHistory()
            >>> event = history.record_edge_creation(
            ...     "agent-1", "agent-2", 0.8, "collaboration_started"
            ... )
            >>> event.edge_key
            ('agent-1', 'agent-2')
        """
        event = TrustEvent(
            timestamp=datetime.now(),
            event_type="edge_created",
            node_id=None,
            edge_key=(source_id, target_id),
            old_value=None,
            new_value=initial_weight,
            reason=reason,
            metadata=metadata or {},
        )
        self._add_event(event)
        return event

    def record_edge_update(
        self,
        source_id: str,
        target_id: str,
        old_value: float,
        new_value: float,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TrustEvent:
        """Record an edge trust update event.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            old_value: Previous edge weight
            new_value: New edge weight
            reason: Explanation for the update
            metadata: Additional context

        Returns:
            The recorded TrustEvent

        Example:
            >>> history = TrustHistory()
            >>> event = history.record_edge_update(
            ...     "agent-1", "agent-2", 0.8, 0.6, "negative_interaction"
            ... )
            >>> event.delta
            -0.2
        """
        event = TrustEvent(
            timestamp=datetime.now(),
            event_type="edge_updated",
            node_id=None,
            edge_key=(source_id, target_id),
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            metadata=metadata or {},
        )
        self._add_event(event)
        return event

    def get_events(
        self,
        node_id: Optional[str] = None,
        edge_key: Optional[tuple] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
    ) -> List[TrustEvent]:
        """Query events with filters.

        Args:
            node_id: Filter by node ID (optional)
            edge_key: Filter by edge key (source, target) (optional)
            since: Filter events after this time (optional)
            until: Filter events before this time (optional)
            event_types: Filter by event types (optional)

        Returns:
            List of matching TrustEvents in chronological order

        Example:
            >>> from datetime import datetime, timedelta
            >>> history = TrustHistory()
            >>> history.record_creation("agent-1", 0.9)
            >>> history.record_update("agent-1", 0.9, 0.7, "test")
            >>> yesterday = datetime.now() - timedelta(days=1)
            >>> events = history.get_events("agent-1", since=yesterday)
            >>> len(events)
            2
        """
        # Start with all events or filtered by node/edge
        if node_id:
            indices = self._node_index.get(node_id, [])
            events = [self._events[i] for i in indices]
        elif edge_key:
            indices = self._edge_index.get(edge_key, [])
            events = [self._events[i] for i in indices]
        else:
            events = list(self._events)

        # Apply time filters
        if since:
            events = [e for e in events if e.timestamp >= since]
        if until:
            events = [e for e in events if e.timestamp <= until]

        # Apply event type filter
        if event_types:
            events = [e for e in events if e.event_type in event_types]

        return events

    def get_trust_timeline(
        self,
        node_id: str,
        since: Optional[datetime] = None,
    ) -> List[tuple]:
        """Get trust value timeline for a node.

        Args:
            node_id: Node to get timeline for
            since: Start time for timeline (optional)

        Returns:
            List of (timestamp, trust_value) tuples in chronological order

        Example:
            >>> history = TrustHistory()
            >>> history.record_creation("agent-1", 0.9)
            >>> history.record_update("agent-1", 0.9, 0.7, "test")
            >>> timeline = history.get_trust_timeline("agent-1")
            >>> len(timeline)
            2
            >>> timeline[0][1]  # First trust value
            0.9
        """
        events = self.get_events(node_id=node_id, since=since)
        return [(e.timestamp, e.new_value) for e in events]

    def get_edge_timeline(
        self,
        source_id: str,
        target_id: str,
        since: Optional[datetime] = None,
    ) -> List[tuple]:
        """Get trust value timeline for an edge.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            since: Start time for timeline (optional)

        Returns:
            List of (timestamp, trust_value) tuples in chronological order
        """
        events = self.get_events(edge_key=(source_id, target_id), since=since)
        return [(e.timestamp, e.new_value) for e in events]

    def get_summary(
        self,
        node_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get summary statistics for the history.

        Args:
            node_id: Summarize only this node (optional)

        Returns:
            Dictionary with summary statistics

        Example:
            >>> history = TrustHistory()
            >>> history.record_creation("agent-1", 0.9)
            >>> history.record_update("agent-1", 0.9, 0.7, "test")
            >>> summary = history.get_summary("agent-1")
            >>> summary["total_events"]
            2
        """
        events = self.get_events(node_id=node_id)

        if not events:
            return {
                "total_events": 0,
                "event_types": {},
                "time_range": None,
            }

        event_type_counts = {}
        for event in events:
            event_type_counts[event.event_type] = (
                event_type_counts.get(event.event_type, 0) + 1
            )

        return {
            "total_events": len(events),
            "event_types": event_type_counts,
            "time_range": {
                "start": events[0].timestamp.isoformat(),
                "end": events[-1].timestamp.isoformat(),
            },
            "latest_value": events[-1].new_value if events else None,
        }

    def to_dataframe(self) -> "pd.DataFrame":
        """Convert history to pandas DataFrame.

        Requires pandas to be installed.

        Returns:
            DataFrame with one row per event

        Raises:
            ImportError: If pandas is not installed

        Example:
            >>> history = TrustHistory()
            >>> history.record_creation("agent-1", 0.9)
            >>> df = history.to_dataframe()
            >>> df.columns.tolist()
            ['timestamp', 'event_type', 'node_id', 'edge_source', 'edge_target', ...]
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install with: pip install pandas"
            )

        records = []
        for event in self._events:
            record = {
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "node_id": event.node_id,
                "edge_source": event.edge_key[0] if event.edge_key else None,
                "edge_target": event.edge_key[1] if event.edge_key else None,
                "old_value": event.old_value,
                "new_value": event.new_value,
                "delta": event.delta,
                "reason": event.reason,
            }
            records.append(record)

        return pd.DataFrame(records)

    def to_json(self, path: Optional[str] = None) -> str:
        """Serialize history to JSON.

        Args:
            path: Optional file path to write to

        Returns:
            JSON string representation

        Example:
            >>> history = TrustHistory()
            >>> history.record_creation("agent-1", 0.9)
            >>> json_str = history.to_json()
            >>> "agent-1" in json_str
            True
        """
        data = {
            "max_events": self.max_events,
            "events": [e.to_dict() for e in self._events],
        }
        json_str = json.dumps(data, indent=2)

        if path:
            with open(path, "w") as f:
                f.write(json_str)

        return json_str

    @classmethod
    def from_json(cls, data: str) -> "TrustHistory":
        """Deserialize history from JSON.

        Args:
            data: JSON string or file path

        Returns:
            TrustHistory instance

        Example:
            >>> history = TrustHistory()
            >>> history.record_creation("agent-1", 0.9)
            >>> json_str = history.to_json()
            >>> loaded = TrustHistory.from_json(json_str)
            >>> len(loaded)
            1
        """
        # Try to parse as JSON string first
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            # Assume it's a file path
            with open(data) as f:
                parsed = json.load(f)

        history = cls(max_events=parsed.get("max_events", 10000))
        for event_data in parsed.get("events", []):
            event = TrustEvent.from_dict(event_data)
            history._add_event(event)

        return history

    def clear(self) -> None:
        """Clear all recorded events.

        Example:
            >>> history = TrustHistory()
            >>> history.record_creation("agent-1", 0.9)
            >>> len(history)
            1
            >>> history.clear()
            >>> len(history)
            0
        """
        self._events.clear()
        self._node_index.clear()
        self._edge_index.clear()
