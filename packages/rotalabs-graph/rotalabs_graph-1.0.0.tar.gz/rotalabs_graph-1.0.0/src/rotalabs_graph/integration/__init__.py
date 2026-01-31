"""Integration with other rotalabs packages.

This module provides integration points between rotalabs-graph and
other packages in the rotalabs ecosystem:

- **rotalabs-comply**: Import compliance status as trust signals
- **rotalabs-audit**: Export trust decisions to audit logs
- **rotalabs-cascade**: Use trust scores for routing decisions
- **rotalabs-probe**: Update trust based on probe results

These integrations are optional and require the respective packages
to be installed.

Example:
    >>> from rotalabs_graph.integration import ComplyIntegration
    >>>
    >>> # Create integration (requires rotalabs-comply)
    >>> comply = ComplyIntegration()
    >>>
    >>> # Update trust graph based on compliance status
    >>> comply.sync_compliance_status(trust_graph)

Note:
    These are placeholder implementations. Full integration will be
    available when the respective packages are released.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional
from datetime import datetime

if TYPE_CHECKING:
    from rotalabs_graph.temporal import TemporalTrustGraph


class ComplyIntegration:
    """Import compliance status from rotalabs-comply.

    Syncs compliance evaluation results to trust scores:
    - Passing compliance checks maintain or boost trust
    - Failing compliance checks reduce trust
    - Critical violations can trigger trust revocation

    Example:
        >>> comply = ComplyIntegration()
        >>> comply.sync_compliance_status(trust_graph)

    Attributes:
        compliance_trust_mapping: Map of compliance status to trust delta
    """

    def __init__(
        self,
        pass_boost: float = 0.05,
        fail_penalty: float = 0.15,
        critical_penalty: float = 0.5,
    ):
        """Initialize comply integration.

        Args:
            pass_boost: Trust increase for passing checks
            fail_penalty: Trust decrease for failing checks
            critical_penalty: Trust decrease for critical violations
        """
        self.pass_boost = pass_boost
        self.fail_penalty = fail_penalty
        self.critical_penalty = critical_penalty
        self._comply_client = None

    def connect(self, comply_instance: Any = None) -> None:
        """Connect to rotalabs-comply instance.

        Args:
            comply_instance: Optional rotalabs-comply client instance.
                If not provided, attempts to create a default client.

        Raises:
            ImportError: If rotalabs-comply is not installed
        """
        if comply_instance is not None:
            self._comply_client = comply_instance
            return

        try:
            from rotalabs_comply import ComplyClient
            self._comply_client = ComplyClient()
        except ImportError:
            raise ImportError(
                "rotalabs-comply is required for ComplyIntegration. "
                "Install with: pip install rotalabs-comply"
            )

    def sync_compliance_status(
        self,
        graph: "TemporalTrustGraph",
        node_ids: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Sync compliance status to trust graph.

        Queries compliance status for nodes and updates trust
        scores accordingly.

        Args:
            graph: Trust graph to update
            node_ids: Specific nodes to sync (default: all nodes)

        Returns:
            Dictionary of {node_id: new_trust} for updated nodes

        Note:
            This is a placeholder. Full implementation requires
            rotalabs-comply to be available.
        """
        # Placeholder implementation
        results = {}

        target_nodes = node_ids or graph.nodes
        for node_id in target_nodes:
            if node_id in graph:
                # In full implementation, would query comply for status
                results[node_id] = graph.get_raw_trust(node_id)

        return results

    def on_compliance_event(
        self,
        graph: "TemporalTrustGraph",
        node_id: str,
        event_type: str,
        severity: str = "normal",
    ) -> Optional[float]:
        """Handle a compliance event.

        Called when rotalabs-comply emits a compliance event.

        Args:
            graph: Trust graph to update
            node_id: Node that triggered the event
            event_type: Type of compliance event ("pass", "fail", "critical")
            severity: Severity level of the event

        Returns:
            New trust score if updated, None otherwise
        """
        if node_id not in graph:
            return None

        current_trust = graph.get_raw_trust(node_id)

        if event_type == "pass":
            new_trust = min(1.0, current_trust + self.pass_boost)
            reason = "compliance_check_passed"
        elif event_type == "fail":
            new_trust = max(0.0, current_trust - self.fail_penalty)
            reason = "compliance_check_failed"
        elif event_type == "critical":
            new_trust = max(0.0, current_trust - self.critical_penalty)
            reason = "critical_compliance_violation"
        else:
            return None

        graph.update_trust(node_id, new_trust, reason, {"severity": severity})
        return new_trust


class AuditIntegration:
    """Export trust events to rotalabs-audit.

    Sends trust graph events to the audit system for:
    - Compliance reporting
    - Security analysis
    - Historical tracking

    Example:
        >>> audit = AuditIntegration()
        >>> audit.connect()
        >>> audit.export_trust_events(trust_graph.history)

    Note:
        Requires rotalabs-audit to be installed.
    """

    def __init__(self, audit_namespace: str = "trust_graph"):
        """Initialize audit integration.

        Args:
            audit_namespace: Namespace for audit events
        """
        self.namespace = audit_namespace
        self._audit_client = None

    def connect(self, audit_instance: Any = None) -> None:
        """Connect to rotalabs-audit instance.

        Args:
            audit_instance: Optional rotalabs-audit client instance

        Raises:
            ImportError: If rotalabs-audit is not installed
        """
        if audit_instance is not None:
            self._audit_client = audit_instance
            return

        try:
            from rotalabs_audit import AuditLogger
            self._audit_client = AuditLogger(namespace=self.namespace)
        except ImportError:
            raise ImportError(
                "rotalabs-audit is required for AuditIntegration. "
                "Install with: pip install rotalabs-audit"
            )

    def export_trust_events(
        self,
        history: Any,
        since: Optional[datetime] = None,
    ) -> int:
        """Export trust history events to audit log.

        Args:
            history: TrustHistory instance
            since: Export events after this time (optional)

        Returns:
            Number of events exported

        Note:
            Placeholder implementation.
        """
        if self._audit_client is None:
            raise RuntimeError("Not connected. Call connect() first.")

        events = history.get_events(since=since)
        # In full implementation, would send to audit client
        return len(events)

    def log_trust_decision(
        self,
        node_id: str,
        decision: str,
        trust_score: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a trust-based decision.

        Args:
            node_id: Node the decision was made about
            decision: Decision made (e.g., "granted", "denied")
            trust_score: Trust score at time of decision
            context: Additional decision context
        """
        # Placeholder - would send to audit client
        pass


class CascadeIntegration:
    """Provide trust scores to rotalabs-cascade.

    Enables cascade routing decisions based on trust:
    - Route to high-trust agents for sensitive operations
    - Fallback routing when trust is insufficient
    - Trust-weighted load balancing

    Example:
        >>> cascade = CascadeIntegration(trust_graph)
        >>> router = cascade.create_trust_router()

    Note:
        Requires rotalabs-cascade to be installed.
    """

    def __init__(self, graph: Optional["TemporalTrustGraph"] = None):
        """Initialize cascade integration.

        Args:
            graph: Trust graph to use for routing decisions
        """
        self._graph = graph
        self._cascade_client = None

    def set_graph(self, graph: "TemporalTrustGraph") -> None:
        """Set the trust graph for routing.

        Args:
            graph: Trust graph to use
        """
        self._graph = graph

    def connect(self, cascade_instance: Any = None) -> None:
        """Connect to rotalabs-cascade instance.

        Args:
            cascade_instance: Optional rotalabs-cascade client

        Raises:
            ImportError: If rotalabs-cascade is not installed
        """
        if cascade_instance is not None:
            self._cascade_client = cascade_instance
            return

        try:
            from rotalabs_cascade import CascadeRouter
            self._cascade_client = CascadeRouter()
        except ImportError:
            raise ImportError(
                "rotalabs-cascade is required for CascadeIntegration. "
                "Install with: pip install rotalabs-cascade"
            )

    def get_trust_score(self, node_id: str) -> Optional[float]:
        """Get current trust score for routing.

        Args:
            node_id: Node to get trust for

        Returns:
            Current trust score, or None if node not found
        """
        if self._graph is None:
            return None

        if node_id not in self._graph:
            return None

        return self._graph.get_current_trust(node_id)

    def get_trusted_nodes(
        self,
        min_trust: float = 0.5,
    ) -> List[str]:
        """Get all nodes meeting trust threshold.

        Args:
            min_trust: Minimum trust score required

        Returns:
            List of node IDs meeting threshold
        """
        if self._graph is None:
            return []

        return [
            node_id
            for node_id in self._graph.nodes
            if self._graph.get_current_trust(node_id) >= min_trust
        ]

    def create_trust_router(self) -> Any:
        """Create a trust-aware router for cascade.

        Returns:
            Router instance configured with trust scoring

        Note:
            Placeholder - returns None until cascade is available
        """
        # Would return configured cascade router
        return None


class ProbeIntegration:
    """Update trust based on rotalabs-probe results.

    Integrates probe/monitoring results into trust scoring:
    - Successful probes maintain trust
    - Failed probes reduce trust
    - Anomalous probe results trigger investigations

    Example:
        >>> probe = ProbeIntegration()
        >>> probe.on_probe_result(trust_graph, "agent-1", probe_result)

    Note:
        Requires rotalabs-probe to be installed.
    """

    def __init__(
        self,
        success_boost: float = 0.02,
        failure_penalty: float = 0.1,
        anomaly_penalty: float = 0.2,
    ):
        """Initialize probe integration.

        Args:
            success_boost: Trust increase for successful probes
            failure_penalty: Trust decrease for failed probes
            anomaly_penalty: Trust decrease for anomalous results
        """
        self.success_boost = success_boost
        self.failure_penalty = failure_penalty
        self.anomaly_penalty = anomaly_penalty
        self._probe_client = None

    def connect(self, probe_instance: Any = None) -> None:
        """Connect to rotalabs-probe instance.

        Args:
            probe_instance: Optional rotalabs-probe client

        Raises:
            ImportError: If rotalabs-probe is not installed
        """
        if probe_instance is not None:
            self._probe_client = probe_instance
            return

        try:
            from rotalabs_probe import ProbeRunner
            self._probe_client = ProbeRunner()
        except ImportError:
            raise ImportError(
                "rotalabs-probe is required for ProbeIntegration. "
                "Install with: pip install rotalabs-probe"
            )

    def on_probe_result(
        self,
        graph: "TemporalTrustGraph",
        node_id: str,
        result: Dict[str, Any],
    ) -> Optional[float]:
        """Handle a probe result.

        Args:
            graph: Trust graph to update
            node_id: Node that was probed
            result: Probe result dictionary with "status" key

        Returns:
            New trust score if updated, None otherwise
        """
        if node_id not in graph:
            return None

        status = result.get("status", "unknown")
        current_trust = graph.get_raw_trust(node_id)

        if status == "success":
            new_trust = min(1.0, current_trust + self.success_boost)
            reason = "probe_success"
        elif status == "failure":
            new_trust = max(0.0, current_trust - self.failure_penalty)
            reason = "probe_failure"
        elif status == "anomaly":
            new_trust = max(0.0, current_trust - self.anomaly_penalty)
            reason = "probe_anomaly"
        else:
            return None

        graph.update_trust(node_id, new_trust, reason, {"probe_result": result})
        return new_trust

    def schedule_trust_probes(
        self,
        graph: "TemporalTrustGraph",
        min_trust: float = 0.3,
        max_trust: float = 0.7,
    ) -> List[str]:
        """Schedule probes for nodes in trust range.

        Nodes with uncertain trust (middle range) benefit most
        from probing.

        Args:
            graph: Trust graph to analyze
            min_trust: Lower bound of target range
            max_trust: Upper bound of target range

        Returns:
            List of node IDs scheduled for probing
        """
        candidates = []

        for node_id in graph.nodes:
            trust = graph.get_current_trust(node_id)
            if min_trust <= trust <= max_trust:
                candidates.append(node_id)

        # In full implementation, would schedule with probe client
        return candidates


__all__ = [
    "ComplyIntegration",
    "AuditIntegration",
    "CascadeIntegration",
    "ProbeIntegration",
]
