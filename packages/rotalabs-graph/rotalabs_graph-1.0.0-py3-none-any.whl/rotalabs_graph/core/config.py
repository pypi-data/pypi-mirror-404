"""Configuration classes for rotalabs-graph.

This module provides dataclasses for configuring graph behavior and
trust propagation algorithms.

Example:
    >>> from rotalabs_graph.core.config import PropagationConfig, GraphConfig
    >>> prop_config = PropagationConfig(
    ...     max_iterations=50,
    ...     damping_factor=0.9,
    ...     aggregation="max"
    ... )
    >>> graph_config = GraphConfig(directed=True, allow_self_loops=False)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal


@dataclass
class PropagationConfig:
    """Configuration for trust propagation algorithms.

    This class controls how trust scores are propagated through the graph,
    including convergence criteria, damping factors, and aggregation methods.

    Attributes:
        max_iterations: Maximum number of propagation iterations. The algorithm
            will stop after this many iterations even if not converged.
            Default: 100.
        convergence_threshold: The algorithm converges when the maximum change
            in any node's trust score is below this threshold. Default: 1e-6.
        damping_factor: For PageRank-style algorithms, this controls the
            probability of following edges vs. jumping to random nodes.
            Higher values mean more weight on graph structure. Default: 0.85.
        decay_per_hop: Amount of trust decay applied at each hop during
            propagation. A value of 0.1 means 10% decay per hop. Default: 0.1.
        aggregation: Method for aggregating trust from multiple sources.
            Options: "mean" (average), "max" (maximum), "min" (minimum),
            "product" (multiply all). Default: "mean".

    Example:
        >>> config = PropagationConfig(
        ...     max_iterations=50,
        ...     convergence_threshold=1e-4,
        ...     damping_factor=0.9,
        ...     decay_per_hop=0.15,
        ...     aggregation="max"
        ... )
        >>> # Use with a propagation algorithm
        >>> propagator = TrustPropagator(config=config)
    """

    max_iterations: int = 100
    convergence_threshold: float = 1e-6
    damping_factor: float = 0.85
    decay_per_hop: float = 0.1
    aggregation: Literal["mean", "max", "min", "product"] = "mean"

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        if self.convergence_threshold <= 0:
            raise ValueError("convergence_threshold must be positive")
        if not 0 <= self.damping_factor <= 1:
            raise ValueError("damping_factor must be between 0 and 1")
        if not 0 <= self.decay_per_hop <= 1:
            raise ValueError("decay_per_hop must be between 0 and 1")
        if self.aggregation not in ("mean", "max", "min", "product"):
            raise ValueError(
                f"aggregation must be one of: mean, max, min, product. "
                f"Got: {self.aggregation}"
            )


@dataclass
class GraphConfig:
    """Configuration for TrustGraph behavior.

    This class controls the fundamental properties and constraints
    of the trust graph structure.

    Attributes:
        directed: Whether the graph is directed. In a directed graph,
            edges have a direction (source -> target). Default: True.
        allow_self_loops: Whether to allow edges from a node to itself.
            Default: False.
        allow_multi_edges: Whether to allow multiple edges between the
            same pair of nodes. Default: False.
        default_edge_weight: Default weight for edges when not specified.
            Must be between 0 and 1. Default: 1.0.
        default_node_trust: Default base trust for nodes when not specified.
            Must be between 0 and 1. Default: 1.0.

    Example:
        >>> config = GraphConfig(
        ...     directed=True,
        ...     allow_self_loops=False,
        ...     default_edge_weight=0.8
        ... )
        >>> graph = TrustGraph(config=config)
    """

    directed: bool = True
    allow_self_loops: bool = False
    allow_multi_edges: bool = False
    default_edge_weight: float = 1.0
    default_node_trust: float = 1.0

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if not 0 <= self.default_edge_weight <= 1:
            raise ValueError("default_edge_weight must be between 0 and 1")
        if not 0 <= self.default_node_trust <= 1:
            raise ValueError("default_node_trust must be between 0 and 1")


@dataclass
class GNNConfig:
    """Configuration for GNN-based propagation.

    Controls the architecture and training of graph neural networks
    used for trust propagation.

    Attributes:
        architecture: GNN architecture to use. Options: "gcn", "gat", "sage".
            Default: "gcn".
        hidden_dim: Dimension of hidden layers. Default: 64.
        num_layers: Number of GNN layers. Default: 2.
        dropout: Dropout probability during training. Default: 0.1.
        heads: Number of attention heads (for GAT). Default: 4.
        learning_rate: Learning rate for training. Default: 0.01.
        epochs: Number of training epochs. Default: 100.
        batch_size: Batch size for training. Default: 32.
        early_stopping_patience: Number of epochs to wait for improvement
            before stopping. Default: 10.
        device: Device to use for computation. Options: "cpu", "cuda", "mps".
            Default: "cpu".

    Example:
        >>> config = GNNConfig(
        ...     architecture="gat",
        ...     hidden_dim=128,
        ...     num_layers=3,
        ...     heads=8
        ... )
    """

    architecture: str = "gcn"
    hidden_dim: int = 64
    num_layers: int = 2
    dropout: float = 0.1
    heads: int = 4
    learning_rate: float = 0.01
    epochs: int = 100
    batch_size: int = 32
    early_stopping_patience: int = 10
    device: str = "cpu"

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        valid_architectures = {"gcn", "gat", "sage"}
        if self.architecture not in valid_architectures:
            raise ValueError(
                f"architecture must be one of {valid_architectures}, "
                f"got {self.architecture}"
            )
        if self.hidden_dim < 1:
            raise ValueError("hidden_dim must be >= 1")
        if self.num_layers < 1:
            raise ValueError("num_layers must be >= 1")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")
        if self.heads < 1:
            raise ValueError("heads must be >= 1")


@dataclass
class EigenTrustConfig:
    """Configuration specific to EigenTrust algorithm.

    Attributes:
        pre_trust_weight: Weight for pre-trusted nodes (alpha parameter).
            Default: 0.1.
        pre_trusted_nodes: List of node IDs that are pre-trusted.
            Default: empty list.
        trust_threshold: Minimum normalized local trust to consider.
            Default: 0.0.

    Example:
        >>> config = EigenTrustConfig(
        ...     pre_trust_weight=0.2,
        ...     pre_trusted_nodes=["trusted-model-1", "trusted-model-2"]
        ... )
    """

    pre_trust_weight: float = 0.1
    pre_trusted_nodes: List[str] = field(default_factory=list)
    trust_threshold: float = 0.0

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if not 0.0 <= self.pre_trust_weight <= 1.0:
            raise ValueError("pre_trust_weight must be in [0, 1]")
        if not 0.0 <= self.trust_threshold <= 1.0:
            raise ValueError("trust_threshold must be in [0, 1]")


@dataclass
class SerializationConfig:
    """Configuration for graph serialization.

    Controls how graphs are serialized to and from various formats.

    Attributes:
        include_metadata: Whether to include node/edge metadata in
            serialization. Default: True.
        datetime_format: Format string for datetime serialization.
            Default: ISO 8601 format.
        float_precision: Number of decimal places for float values.
            Default: 6.

    Example:
        >>> config = SerializationConfig(
        ...     include_metadata=False,
        ...     float_precision=4
        ... )
    """

    include_metadata: bool = True
    datetime_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"
    float_precision: int = 6

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if self.float_precision < 0:
            raise ValueError("float_precision must be non-negative")


@dataclass
class VisualizationConfig:
    """Configuration for graph visualization.

    Controls visual appearance when rendering trust graphs.

    Attributes:
        node_size_base: Base size for nodes. Default: 300.
        node_size_scale_by_trust: Whether to scale node size by trust score.
            Default: True.
        edge_width_base: Base width for edges. Default: 1.0.
        edge_width_scale_by_weight: Whether to scale edge width by weight.
            Default: True.
        colormap: Matplotlib colormap name for trust scores. Default: "RdYlGn".
        layout_algorithm: Graph layout algorithm. Options: "spring", "circular",
            "kamada_kawai", "spectral". Default: "spring".
        show_labels: Whether to show node labels. Default: True.
        show_edge_labels: Whether to show edge labels. Default: False.
        figure_size: Figure size as (width, height) tuple. Default: (12, 8).

    Example:
        >>> config = VisualizationConfig(
        ...     colormap="viridis",
        ...     layout_algorithm="kamada_kawai",
        ...     show_edge_labels=True
        ... )
    """

    node_size_base: int = 300
    node_size_scale_by_trust: bool = True
    edge_width_base: float = 1.0
    edge_width_scale_by_weight: bool = True
    colormap: str = "RdYlGn"
    layout_algorithm: Literal["spring", "circular", "kamada_kawai", "spectral"] = "spring"
    show_labels: bool = True
    show_edge_labels: bool = False
    figure_size: tuple[int, int] = field(default_factory=lambda: (12, 8))

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if self.node_size_base < 1:
            raise ValueError("node_size_base must be at least 1")
        if self.edge_width_base <= 0:
            raise ValueError("edge_width_base must be positive")
        if len(self.figure_size) != 2:
            raise ValueError("figure_size must be a tuple of (width, height)")
        if self.figure_size[0] < 1 or self.figure_size[1] < 1:
            raise ValueError("figure_size dimensions must be at least 1")
