"""Custom exceptions for rotalabs-graph.

This module defines the exception hierarchy for the trust graph system.
All exceptions inherit from GraphError, making it easy to catch any
graph-related exception.

Example:
    >>> from rotalabs_graph.core.exceptions import NodeNotFoundError
    >>> try:
    ...     graph.get_node("nonexistent")
    ... except NodeNotFoundError as e:
    ...     print(f"Node not found: {e.node_id}")
"""

from __future__ import annotations

from typing import Any, List, Optional


class GraphError(Exception):
    """Base exception for all graph-related errors.

    All other exceptions in this module inherit from GraphError,
    allowing callers to catch any graph error with a single except clause.

    Attributes:
        message: Human-readable error description.
        details: Optional dictionary with additional error context.

    Example:
        >>> try:
        ...     graph.some_operation()
        ... except GraphError as e:
        ...     logger.error(f"Graph operation failed: {e}")
    """

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """Initialize GraphError.

        Args:
            message: Human-readable error description.
            details: Optional dictionary with additional error context.
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class NodeNotFoundError(GraphError):
    """Raised when a requested node does not exist in the graph.

    Attributes:
        node_id: The ID of the node that was not found.

    Example:
        >>> try:
        ...     node = graph.get_node("model-123")
        ... except NodeNotFoundError as e:
        ...     print(f"Could not find node: {e.node_id}")
    """

    def __init__(self, node_id: str) -> None:
        """Initialize NodeNotFoundError.

        Args:
            node_id: The ID of the node that was not found.
        """
        self.node_id = node_id
        super().__init__(
            message=f"Node not found: '{node_id}'",
            details={"node_id": node_id},
        )


class EdgeNotFoundError(GraphError):
    """Raised when a requested edge does not exist in the graph.

    Attributes:
        source_id: The source node ID of the edge.
        target_id: The target node ID of the edge.

    Example:
        >>> try:
        ...     edge = graph.get_edge("model-1", "agent-1")
        ... except EdgeNotFoundError as e:
        ...     print(f"No edge from {e.source_id} to {e.target_id}")
    """

    def __init__(self, source_id: str, target_id: str) -> None:
        """Initialize EdgeNotFoundError.

        Args:
            source_id: The source node ID of the edge.
            target_id: The target node ID of the edge.
        """
        self.source_id = source_id
        self.target_id = target_id
        super().__init__(
            message=f"Edge not found: '{source_id}' -> '{target_id}'",
            details={"source_id": source_id, "target_id": target_id},
        )


class CycleDetectedError(GraphError):
    """Raised when an operation would create or has detected a cycle.

    This exception is raised during operations that require an acyclic
    graph, such as topological sorting or certain trust propagation
    algorithms.

    Attributes:
        cycle_nodes: List of node IDs forming the cycle.
        operation: The operation that detected/would create the cycle.

    Example:
        >>> try:
        ...     graph.add_edge(edge)  # Would create cycle
        ... except CycleDetectedError as e:
        ...     print(f"Cycle detected: {' -> '.join(e.cycle_nodes)}")
    """

    def __init__(
        self,
        cycle_nodes: List[str],
        operation: Optional[str] = None,
    ) -> None:
        """Initialize CycleDetectedError.

        Args:
            cycle_nodes: List of node IDs forming the cycle.
            operation: The operation that detected/would create the cycle.
        """
        self.cycle_nodes = cycle_nodes
        self.operation = operation
        cycle_str = " -> ".join(cycle_nodes)
        message = f"Cycle detected: {cycle_str}"
        if operation:
            message = f"Cycle detected during {operation}: {cycle_str}"
        super().__init__(
            message=message,
            details={"cycle_nodes": cycle_nodes, "operation": operation},
        )


class PropagationError(GraphError):
    """Raised when trust propagation fails.

    This exception covers various propagation failures including
    convergence issues, numerical instability, and invalid configurations.

    Attributes:
        reason: Specific reason for the propagation failure.
        iterations: Number of iterations completed before failure.
        last_delta: The last computed delta (if applicable).

    Example:
        >>> try:
        ...     scores = propagator.compute_trust(graph)
        ... except PropagationError as e:
        ...     print(f"Propagation failed: {e.reason}")
        ...     print(f"Completed {e.iterations} iterations")
    """

    def __init__(
        self,
        reason: str,
        iterations: Optional[int] = None,
        last_delta: Optional[float] = None,
    ) -> None:
        """Initialize PropagationError.

        Args:
            reason: Specific reason for the propagation failure.
            iterations: Number of iterations completed before failure.
            last_delta: The last computed delta (if applicable).
        """
        self.reason = reason
        self.iterations = iterations
        self.last_delta = last_delta

        details: dict[str, Any] = {"reason": reason}
        if iterations is not None:
            details["iterations"] = iterations
        if last_delta is not None:
            details["last_delta"] = last_delta

        message = f"Trust propagation failed: {reason}"
        if iterations is not None:
            message += f" (after {iterations} iterations)"

        super().__init__(message=message, details=details)


class ConvergenceError(PropagationError):
    """Raised when iterative algorithm fails to converge.

    Attributes:
        iterations: Number of iterations performed.
        delta: Final delta value when stopped.
        threshold: Convergence threshold that was not met.

    Example:
        >>> try:
        ...     scores = propagator.compute_trust(graph)
        ... except ConvergenceError as e:
        ...     print(f"Failed to converge after {e.iterations} iterations")
        ...     print(f"Final delta: {e.delta}, threshold: {e.threshold}")
    """

    def __init__(self, iterations: int, delta: float, threshold: float) -> None:
        """Initialize ConvergenceError.

        Args:
            iterations: Number of iterations performed.
            delta: Final delta value when stopped.
            threshold: Convergence threshold that was not met.
        """
        self.delta = delta
        self.threshold = threshold
        super().__init__(
            reason=f"Failed to converge. Delta: {delta:.6f}, threshold: {threshold:.6f}",
            iterations=iterations,
            last_delta=delta,
        )


class InvalidGraphError(GraphError):
    """Raised when graph structure is invalid for the requested operation.

    Example:
        >>> try:
        ...     propagator.compute_trust(empty_graph)
        ... except InvalidGraphError as e:
        ...     print(f"Invalid graph: {e}")
    """

    def __init__(self, reason: str) -> None:
        """Initialize InvalidGraphError.

        Args:
            reason: Description of why the graph is invalid.
        """
        super().__init__(
            message=f"Invalid graph structure: {reason}",
            details={"reason": reason},
        )


class ValidationError(GraphError):
    """Raised when validation of graph data fails.

    This exception is raised when nodes, edges, or other graph data
    fail validation checks (e.g., invalid trust scores, malformed IDs).

    Attributes:
        field: The field or attribute that failed validation.
        value: The invalid value.
        constraint: Description of the validation constraint violated.

    Example:
        >>> try:
        ...     node = TrustNode(id="", name="test", ...)
        ... except ValidationError as e:
        ...     print(f"Invalid {e.field}: {e.constraint}")
    """

    def __init__(
        self,
        field: str,
        value: Any,
        constraint: str,
    ) -> None:
        """Initialize ValidationError.

        Args:
            field: The field or attribute that failed validation.
            value: The invalid value.
            constraint: Description of the validation constraint violated.
        """
        self.field = field
        self.value = value
        self.constraint = constraint

        # Truncate value representation for display
        value_repr = repr(value)
        if len(value_repr) > 50:
            value_repr = value_repr[:47] + "..."

        super().__init__(
            message=f"Validation failed for '{field}': {constraint} (got {value_repr})",
            details={"field": field, "value": value, "constraint": constraint},
        )


class GNNError(GraphError):
    """Raised when GNN-related operations fail.

    Example:
        >>> try:
        ...     gnn_propagator.fit(graph)
        ... except GNNError as e:
        ...     print(f"GNN error: {e}")
    """

    def __init__(self, reason: str) -> None:
        """Initialize GNNError.

        Args:
            reason: Description of the GNN-related failure.
        """
        super().__init__(
            message=f"GNN operation failed: {reason}",
            details={"reason": reason},
        )


class GNNNotFittedError(GNNError):
    """Raised when trying to use an unfitted GNN model.

    Example:
        >>> try:
        ...     scores = gnn_propagator.propagate(graph)
        ... except GNNNotFittedError:
        ...     print("Model needs to be trained first")
    """

    def __init__(self) -> None:
        """Initialize GNNNotFittedError."""
        super().__init__(
            reason="GNN model has not been fitted. Call fit() before propagate()."
        )
