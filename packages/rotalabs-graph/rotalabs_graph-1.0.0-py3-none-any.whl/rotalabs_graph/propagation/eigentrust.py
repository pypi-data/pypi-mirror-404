"""EigenTrust algorithm for trust propagation."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

import numpy as np

from rotalabs_graph.core.config import EigenTrustConfig, PropagationConfig
from rotalabs_graph.core.exceptions import ConvergenceError, PropagationError
from rotalabs_graph.core.graph import TrustGraph
from rotalabs_graph.core.types import TrustScore

from .base import BasePropagator


class EigenTrustPropagator(BasePropagator):
    """Trust propagation using EigenTrust algorithm.

    EigenTrust computes global trust values as the stationary distribution
    of a Markov chain defined by normalized local trust values. It was
    originally designed for P2P networks to identify trustworthy peers.

    Key features:
    - Normalizes local trust to create a probability distribution
    - Uses pre-trusted nodes to bootstrap trust and prevent manipulation
    - Iteratively computes global trust until convergence

    Reference:
        "The EigenTrust Algorithm for Reputation Management in P2P Networks"
        Kamvar, Schlosser, and Garcia-Molina (WWW 2003)

    Trust computation:
        1. Normalize local trust: c_ij = max(s_ij, 0) / sum_j(max(s_ij, 0))
        2. Form transition matrix C where C_ij = c_ji (transpose)
        3. Iterate: t(k+1) = (1-a) * C * t(k) + a * p
           where p is pre-trust vector, a is pre_trust_weight
        4. Converge to stationary distribution

    Example:
        >>> propagator = EigenTrustPropagator(
        ...     pre_trust_weight=0.1,
        ...     pre_trusted_nodes=["trusted-authority"]
        ... )
        >>> scores = propagator.propagate(graph)
        >>> print(scores["model-a"].value)
        0.287
    """

    def __init__(
        self,
        config: Optional[PropagationConfig] = None,
        eigentrust_config: Optional[EigenTrustConfig] = None,
        pre_trust_weight: Optional[float] = None,
        pre_trusted_nodes: Optional[List[str]] = None,
    ) -> None:
        """Initialize EigenTrust propagator.

        Args:
            config: General propagation configuration
            eigentrust_config: EigenTrust-specific configuration
            pre_trust_weight: Weight for pre-trusted nodes (alpha parameter).
                            Overrides eigentrust_config if provided.
            pre_trusted_nodes: List of node IDs that are pre-trusted.
                             Overrides eigentrust_config if provided.
        """
        super().__init__(config)
        self.eigentrust_config = eigentrust_config or EigenTrustConfig()

        # Override with explicit parameters
        if pre_trust_weight is not None:
            if not 0.0 <= pre_trust_weight <= 1.0:
                raise ValueError(
                    f"pre_trust_weight must be in [0, 1], got {pre_trust_weight}"
                )
            self.eigentrust_config.pre_trust_weight = pre_trust_weight

        if pre_trusted_nodes is not None:
            self.eigentrust_config.pre_trusted_nodes = list(pre_trusted_nodes)

    def propagate(
        self,
        graph: TrustGraph,
        source_nodes: Optional[List[str]] = None,
    ) -> Dict[str, TrustScore]:
        """Propagate trust using EigenTrust algorithm.

        Args:
            graph: The trust graph
            source_nodes: If provided, use as pre-trusted nodes instead of
                         the ones specified in config.

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        self._validate_graph(graph)
        self.last_run_time = datetime.now()

        # Determine pre-trusted nodes
        pre_trusted = source_nodes or self.eigentrust_config.pre_trusted_nodes

        # Validate pre-trusted nodes
        for node_id in pre_trusted:
            self._validate_source(graph, node_id)

        # Build normalized transition matrix
        node_ids, transition_matrix = self._build_transition_matrix(graph)
        n = len(node_ids)
        node_to_idx = {node_id: i for i, node_id in enumerate(node_ids)}

        # Build pre-trust vector
        pre_trust = self._build_pre_trust_vector(node_ids, pre_trusted)

        # Initialize trust vector (uniform or from initial values)
        trust = self._initialize_trust_vector(graph, node_ids)

        # Iterate until convergence
        alpha = self.eigentrust_config.pre_trust_weight
        converged = False

        for iteration in range(self.config.max_iterations):
            # t(k+1) = (1-a) * C * t(k) + a * p
            new_trust = (1 - alpha) * transition_matrix @ trust + alpha * pre_trust

            # Check convergence
            delta = np.linalg.norm(new_trust - trust, ord=1)
            trust = new_trust

            if delta < self.config.convergence_threshold:
                converged = True
                self.last_iterations = iteration + 1
                break

        if not converged:
            raise ConvergenceError(
                iterations=self.config.max_iterations,
                delta=delta,
                threshold=self.config.convergence_threshold,
            )

        # Convert to dictionary
        scores = {node_ids[i]: float(trust[i]) for i in range(n)}

        # Post-process
        if self.config.normalize:
            scores = self._normalize_scores(scores)

        scores = self._clamp_scores(scores)

        return self._scores_to_trust_scores(
            scores,
            source="eigentrust",
            confidence=self._compute_confidence(graph, converged, self.last_iterations),
        )

    def propagate_from(
        self,
        graph: TrustGraph,
        source_id: str,
    ) -> Dict[str, TrustScore]:
        """Propagate trust from a single source using EigenTrust.

        Uses the source node as the sole pre-trusted node with full
        pre-trust weight.

        Args:
            graph: The trust graph
            source_id: ID of the source node

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        self._validate_source(graph, source_id)

        # Use source as the only pre-trusted node
        return self.propagate(graph, source_nodes=[source_id])

    def _build_transition_matrix(
        self,
        graph: TrustGraph,
    ) -> tuple:
        """Build the normalized transition matrix.

        The transition matrix C is built by normalizing local trust values
        so that each row sums to 1 (or is uniform for nodes with no outgoing edges).

        Args:
            graph: The trust graph

        Returns:
            Tuple of (node_ids, transition_matrix)
        """
        node_ids = graph.node_ids()
        n = len(node_ids)
        node_to_idx = {node_id: i for i, node_id in enumerate(node_ids)}

        # Build local trust matrix (edge weights)
        local_trust = np.zeros((n, n))
        for edge in graph.edges():
            i = node_to_idx[edge.source_id]
            j = node_to_idx[edge.target_id]
            # Use max(0, weight) to handle any negative weights
            weight = max(0, edge.weight) if self.config.use_edge_weights else 1.0
            if weight >= self.eigentrust_config.trust_threshold:
                local_trust[i, j] = weight

        # Normalize rows to create transition probabilities
        transition = np.zeros((n, n))
        for i in range(n):
            row_sum = local_trust[i].sum()
            if row_sum > 0:
                transition[i] = local_trust[i] / row_sum
            else:
                # No outgoing edges: uniform distribution (teleport)
                transition[i] = np.ones(n) / n

        # Transpose for column-stochastic matrix
        # (trust flows from source to target, so we want C @ t)
        return node_ids, transition.T

    def _build_pre_trust_vector(
        self,
        node_ids: List[str],
        pre_trusted: List[str],
    ) -> np.ndarray:
        """Build the pre-trust vector.

        Pre-trusted nodes receive equal share of pre-trust weight.

        Args:
            node_ids: List of all node IDs
            pre_trusted: List of pre-trusted node IDs

        Returns:
            Pre-trust vector as numpy array
        """
        n = len(node_ids)
        node_to_idx = {node_id: i for i, node_id in enumerate(node_ids)}

        if not pre_trusted:
            # Uniform pre-trust if no pre-trusted nodes specified
            return np.ones(n) / n

        pre_trust = np.zeros(n)
        for node_id in pre_trusted:
            if node_id in node_to_idx:
                pre_trust[node_to_idx[node_id]] = 1.0

        # Normalize
        total = pre_trust.sum()
        if total > 0:
            pre_trust /= total
        else:
            pre_trust = np.ones(n) / n

        return pre_trust

    def _initialize_trust_vector(
        self,
        graph: TrustGraph,
        node_ids: List[str],
    ) -> np.ndarray:
        """Initialize the trust vector.

        Uses initial trust values from nodes if available, otherwise uniform.

        Args:
            graph: The trust graph
            node_ids: List of node IDs

        Returns:
            Initial trust vector as numpy array
        """
        n = len(node_ids)
        initial_scores = self._get_initial_scores(graph)

        trust = np.array([initial_scores.get(node_id, 0.5) for node_id in node_ids])

        # Normalize to sum to 1
        total = trust.sum()
        if total > 0:
            trust /= total
        else:
            trust = np.ones(n) / n

        return trust

    def _compute_confidence(
        self,
        graph: TrustGraph,
        converged: bool,
        iterations: int,
    ) -> float:
        """Compute confidence in EigenTrust results.

        Args:
            graph: The trust graph
            converged: Whether the algorithm converged
            iterations: Number of iterations taken

        Returns:
            Confidence value in [0, 1]
        """
        if not converged:
            return 0.3  # Low confidence if didn't converge

        # Higher confidence if converged quickly
        iteration_factor = 1.0 - (iterations / self.config.max_iterations)

        # Graph connectivity factor
        if graph.num_nodes > 1:
            max_edges = graph.num_nodes * (graph.num_nodes - 1)
            density = graph.num_edges / max_edges
        else:
            density = 0.5

        # Pre-trust factor (having pre-trusted nodes increases confidence)
        has_pretrust = len(self.eigentrust_config.pre_trusted_nodes) > 0
        pretrust_factor = 0.8 if has_pretrust else 0.5

        # Combine factors
        confidence = 0.4 * iteration_factor + 0.3 * density + 0.3 * pretrust_factor
        return min(1.0, max(0.0, confidence))
