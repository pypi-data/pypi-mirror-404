"""GNN-based trust propagation using learned message passing."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from rotalabs_graph.core.config import GNNConfig, PropagationConfig
from rotalabs_graph.core.exceptions import GNNError, GNNNotFittedError, PropagationError
from rotalabs_graph.core.graph import TrustGraph
from rotalabs_graph.core.types import TrustScore

from .base import BasePropagator

# Optional imports with fallback
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None
    nn = None
    F = None

try:
    from torch_geometric.nn import GATConv, GCNConv, SAGEConv
    from torch_geometric.data import Data

    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False
    GATConv = None
    GCNConv = None
    SAGEConv = None
    Data = None


def _check_torch_geometric() -> None:
    """Check if torch-geometric is available."""
    if not HAS_TORCH:
        raise ImportError(
            "GNN propagation requires PyTorch. "
            "Install with: pip install torch"
        )
    if not HAS_TORCH_GEOMETRIC:
        raise ImportError(
            "GNN propagation requires torch-geometric. "
            "Install with: pip install rotalabs-graph[gnn] "
            "or: pip install torch-geometric"
        )


class TrustGNN(nn.Module if HAS_TORCH else object):
    """PyTorch module for trust propagation GNN.

    Supports three architectures:
    - GCN: Graph Convolutional Network (Kipf & Welling, 2017)
    - GAT: Graph Attention Network (Velickovic et al., 2018)
    - GraphSAGE: Sample and Aggregate (Hamilton et al., 2017)

    The network takes node features and graph structure as input,
    and outputs a trust score for each node.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1,
        architecture: str = "gcn",
        heads: int = 4,
    ) -> None:
        """Initialize TrustGNN.

        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden layer dimension
            num_layers: Number of GNN layers
            dropout: Dropout probability
            architecture: GNN architecture (gcn, gat, sage)
            heads: Number of attention heads (for GAT)
        """
        _check_torch_geometric()
        super().__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout
        self.architecture = architecture
        self.heads = heads

        # Build layers
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()

        # Input layer
        if architecture == "gcn":
            self.convs.append(GCNConv(input_dim, hidden_dim))
        elif architecture == "gat":
            self.convs.append(GATConv(input_dim, hidden_dim // heads, heads=heads))
        elif architecture == "sage":
            self.convs.append(SAGEConv(input_dim, hidden_dim))
        else:
            raise ValueError(f"Unknown architecture: {architecture}")

        self.norms.append(nn.LayerNorm(hidden_dim))

        # Hidden layers
        for _ in range(num_layers - 1):
            if architecture == "gcn":
                self.convs.append(GCNConv(hidden_dim, hidden_dim))
            elif architecture == "gat":
                self.convs.append(GATConv(hidden_dim, hidden_dim // heads, heads=heads))
            elif architecture == "sage":
                self.convs.append(SAGEConv(hidden_dim, hidden_dim))

            self.norms.append(nn.LayerNorm(hidden_dim))

        # Output head for trust score prediction
        self.trust_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid(),  # Output in [0, 1]
        )

    def forward(
        self,
        x: "torch.Tensor",
        edge_index: "torch.Tensor",
        edge_weight: Optional["torch.Tensor"] = None,
    ) -> "torch.Tensor":
        """Forward pass.

        Args:
            x: Node features [num_nodes, input_dim]
            edge_index: Edge indices [2, num_edges]
            edge_weight: Optional edge weights [num_edges]

        Returns:
            Trust scores [num_nodes, 1]
        """
        # Message passing layers
        for i, (conv, norm) in enumerate(zip(self.convs, self.norms)):
            if self.architecture == "gcn" and edge_weight is not None:
                x = conv(x, edge_index, edge_weight)
            else:
                x = conv(x, edge_index)

            x = norm(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        # Trust score prediction
        trust_scores = self.trust_head(x)
        return trust_scores.squeeze(-1)


class GNNPropagator(BasePropagator):
    """GNN-based trust propagation using learned message passing.

    Uses Graph Neural Networks to learn trust propagation patterns
    from labeled data. The GNN learns to predict trust scores by
    aggregating information from neighboring nodes through multiple
    layers of message passing.

    Supports three architectures:
    - GCN: Simple and efficient, good for homogeneous graphs
    - GAT: Uses attention for weighted aggregation, better for heterogeneous
    - GraphSAGE: Samples neighbors, scales to large graphs

    Requires: pip install rotalabs-graph[gnn]

    Example:
        >>> # Create and train propagator
        >>> propagator = GNNPropagator(architecture="gat", hidden_dim=64)
        >>> propagator.fit(
        ...     train_graph,
        ...     labels={"model-a": 0.9, "model-b": 0.3, "model-c": 0.7}
        ... )
        >>>
        >>> # Predict trust scores
        >>> scores = propagator.propagate(test_graph)
        >>> print(scores["model-d"].value)
        0.65

        >>> # Save and load model
        >>> propagator.save("trust_gnn.pt")
        >>> new_propagator = GNNPropagator.load("trust_gnn.pt")
    """

    def __init__(
        self,
        config: Optional[PropagationConfig] = None,
        gnn_config: Optional[GNNConfig] = None,
        architecture: Optional[str] = None,
        hidden_dim: Optional[int] = None,
        num_layers: Optional[int] = None,
        dropout: Optional[float] = None,
    ) -> None:
        """Initialize GNN propagator.

        Args:
            config: General propagation configuration
            gnn_config: GNN-specific configuration
            architecture: GNN architecture (gcn, gat, sage). Overrides gnn_config.
            hidden_dim: Hidden dimension. Overrides gnn_config.
            num_layers: Number of layers. Overrides gnn_config.
            dropout: Dropout probability. Overrides gnn_config.
        """
        _check_torch_geometric()
        super().__init__(config)

        self.gnn_config = gnn_config or GNNConfig()

        # Override with explicit parameters
        if architecture is not None:
            self.gnn_config.architecture = architecture
        if hidden_dim is not None:
            self.gnn_config.hidden_dim = hidden_dim
        if num_layers is not None:
            self.gnn_config.num_layers = num_layers
        if dropout is not None:
            self.gnn_config.dropout = dropout

        # Model will be initialized on first fit
        self.model: Optional[TrustGNN] = None
        self._fitted = False
        self._feature_dim: Optional[int] = None
        self._node_features_config: Dict[str, Any] = {}

        # Training history
        self.training_history: List[Dict[str, float]] = []

    @property
    def is_fitted(self) -> bool:
        """Check if the model has been fitted."""
        return self._fitted and self.model is not None

    def fit(
        self,
        graph: TrustGraph,
        labels: Dict[str, float],
        validation_graph: Optional[TrustGraph] = None,
        validation_labels: Optional[Dict[str, float]] = None,
        epochs: Optional[int] = None,
        lr: Optional[float] = None,
        verbose: bool = True,
    ) -> "GNNPropagator":
        """Train the GNN on labeled trust data.

        Args:
            graph: Training graph
            labels: Dictionary mapping node_id to known trust score
            validation_graph: Optional validation graph
            validation_labels: Optional validation labels
            epochs: Number of training epochs (overrides config)
            lr: Learning rate (overrides config)
            verbose: Whether to print training progress

        Returns:
            self for chaining
        """
        self._validate_graph(graph)

        if not labels:
            raise GNNError("No training labels provided")

        epochs = epochs or self.gnn_config.epochs
        lr = lr or self.gnn_config.learning_rate

        # Convert graph to PyTorch Geometric format
        data = self._graph_to_pyg(graph)

        # Initialize model if needed
        if self.model is None:
            self._feature_dim = data.x.shape[1]
            self.model = TrustGNN(
                input_dim=self._feature_dim,
                hidden_dim=self.gnn_config.hidden_dim,
                num_layers=self.gnn_config.num_layers,
                dropout=self.gnn_config.dropout,
                architecture=self.gnn_config.architecture,
                heads=self.gnn_config.heads,
            )

        # Move to device
        device = torch.device(self.gnn_config.device)
        self.model = self.model.to(device)
        data = data.to(device)

        # Create label tensor and mask
        node_ids = graph.node_ids()
        node_to_idx = {node_id: i for i, node_id in enumerate(node_ids)}

        label_tensor = torch.zeros(len(node_ids), device=device)
        label_mask = torch.zeros(len(node_ids), dtype=torch.bool, device=device)

        for node_id, score in labels.items():
            if node_id in node_to_idx:
                idx = node_to_idx[node_id]
                label_tensor[idx] = score
                label_mask[idx] = True

        # Setup optimizer
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

        # Validation data
        val_data = None
        val_labels_tensor = None
        val_mask = None

        if validation_graph and validation_labels:
            val_data = self._graph_to_pyg(validation_graph).to(device)
            val_node_ids = validation_graph.node_ids()
            val_node_to_idx = {nid: i for i, nid in enumerate(val_node_ids)}

            val_labels_tensor = torch.zeros(len(val_node_ids), device=device)
            val_mask = torch.zeros(len(val_node_ids), dtype=torch.bool, device=device)

            for node_id, score in validation_labels.items():
                if node_id in val_node_to_idx:
                    idx = val_node_to_idx[node_id]
                    val_labels_tensor[idx] = score
                    val_mask[idx] = True

        # Training loop
        best_val_loss = float("inf")
        patience_counter = 0
        self.training_history = []

        for epoch in range(epochs):
            # Training
            self.model.train()
            optimizer.zero_grad()

            predictions = self.model(data.x, data.edge_index, data.edge_weight)
            train_loss = F.mse_loss(predictions[label_mask], label_tensor[label_mask])

            train_loss.backward()
            optimizer.step()

            # Validation
            val_loss = None
            if val_data is not None:
                self.model.eval()
                with torch.no_grad():
                    val_preds = self.model(
                        val_data.x, val_data.edge_index, val_data.edge_weight
                    )
                    val_loss = F.mse_loss(
                        val_preds[val_mask], val_labels_tensor[val_mask]
                    ).item()

            # Record history
            history_entry = {
                "epoch": epoch + 1,
                "train_loss": train_loss.item(),
            }
            if val_loss is not None:
                history_entry["val_loss"] = val_loss
            self.training_history.append(history_entry)

            # Early stopping
            if val_loss is not None:
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self.gnn_config.early_stopping_patience:
                        if verbose:
                            print(f"Early stopping at epoch {epoch + 1}")
                        break

            if verbose and (epoch + 1) % 10 == 0:
                msg = f"Epoch {epoch + 1}/{epochs}, Train Loss: {train_loss.item():.4f}"
                if val_loss is not None:
                    msg += f", Val Loss: {val_loss:.4f}"
                print(msg)

        self._fitted = True
        return self

    def propagate(
        self,
        graph: TrustGraph,
        source_nodes: Optional[List[str]] = None,
    ) -> Dict[str, TrustScore]:
        """Use trained GNN to predict trust scores.

        Args:
            graph: The graph to predict on
            source_nodes: Ignored for GNN (uses learned patterns)

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        if not self.is_fitted:
            raise GNNNotFittedError()

        self._validate_graph(graph)
        self.last_run_time = datetime.now()

        # Convert graph to PyG format
        data = self._graph_to_pyg(graph)

        # Move to device
        device = torch.device(self.gnn_config.device)
        self.model = self.model.to(device)
        data = data.to(device)

        # Predict
        self.model.eval()
        with torch.no_grad():
            predictions = self.model(data.x, data.edge_index, data.edge_weight)

        # Convert to dictionary
        node_ids = graph.node_ids()
        scores = {
            node_id: float(predictions[i].cpu())
            for i, node_id in enumerate(node_ids)
        }

        # Post-process
        if self.config.normalize:
            scores = self._normalize_scores(scores)

        scores = self._clamp_scores(scores)

        return self._scores_to_trust_scores(
            scores,
            source="gnn",
            confidence=self._compute_confidence(),
        )

    def propagate_from(
        self,
        graph: TrustGraph,
        source_id: str,
    ) -> Dict[str, TrustScore]:
        """Propagate from a source node using GNN predictions.

        Note: GNN predictions are based on learned patterns, not explicit
        source-based propagation. This method adds the source node as a
        feature signal.

        Args:
            graph: The trust graph
            source_id: ID of the source node

        Returns:
            Dictionary mapping node_id to TrustScore
        """
        if not self.is_fitted:
            raise GNNNotFittedError()

        self._validate_source(graph, source_id)

        # For GNN, we can incorporate source information by setting
        # the source node's initial trust high and re-predicting
        # This creates a source-biased prediction

        # Clone graph and set source trust
        modified_graph = graph.copy()
        source_node = modified_graph.get_node(source_id)
        if source_node:
            # Temporarily boost source's attributes
            source_node.attributes["is_source"] = True
            source_node.base_trust = 1.0

        scores = self.propagate(modified_graph, source_nodes=None)

        # Update source info
        for node_id, score in scores.items():
            score.source = f"gnn_from_{source_id}"

        return scores

    def _graph_to_pyg(self, graph: TrustGraph) -> "Data":
        """Convert TrustGraph to PyTorch Geometric Data object.

        Args:
            graph: The trust graph

        Returns:
            PyG Data object
        """
        node_ids = graph.node_ids()
        n = len(node_ids)
        node_to_idx = {node_id: i for i, node_id in enumerate(node_ids)}

        # Build node features
        features = self._build_node_features(graph, node_ids)

        # Build edge index
        edges = list(graph.edges())
        if edges:
            edge_index = torch.tensor(
                [
                    [node_to_idx[e.source_id] for e in edges],
                    [node_to_idx[e.target_id] for e in edges],
                ],
                dtype=torch.long,
            )
            edge_weight = torch.tensor(
                [e.weight for e in edges],
                dtype=torch.float,
            )
        else:
            # Handle graph with no edges
            edge_index = torch.zeros((2, 0), dtype=torch.long)
            edge_weight = torch.zeros(0, dtype=torch.float)

        return Data(
            x=features,
            edge_index=edge_index,
            edge_weight=edge_weight,
        )

    def _build_node_features(
        self,
        graph: TrustGraph,
        node_ids: List[str],
    ) -> "torch.Tensor":
        """Build node feature matrix.

        Features include:
        - Initial trust (if set)
        - Node type (one-hot encoded)
        - In-degree and out-degree
        - Average edge weight

        Args:
            graph: The trust graph
            node_ids: List of node IDs

        Returns:
            Feature tensor [num_nodes, feature_dim]
        """
        from rotalabs_graph.core.types import NodeType

        n = len(node_ids)
        node_types = list(NodeType)
        num_node_types = len(node_types)

        # Feature dimension: 1 (trust) + num_types (one-hot) + 3 (degree features)
        feature_dim = 1 + num_node_types + 3
        features = np.zeros((n, feature_dim))

        for i, node_id in enumerate(node_ids):
            node = graph.get_node(node_id)
            if node is None:
                continue

            # Initial trust
            features[i, 0] = (
                node.base_trust
                if node.base_trust is not None
                else self.config.initial_trust
            )

            # Node type one-hot
            try:
                type_idx = node_types.index(node.node_type)
                features[i, 1 + type_idx] = 1.0
            except ValueError:
                pass  # Unknown type

            # Degree features
            in_deg = graph.in_degree(node_id)
            out_deg = graph.out_degree(node_id)
            features[i, 1 + num_node_types] = in_deg / max(1, n - 1)
            features[i, 2 + num_node_types] = out_deg / max(1, n - 1)

            # Average incoming edge weight
            incoming_weights = [
                graph.get_edge(pred, node_id).weight
                for pred in graph.predecessors(node_id)
                if graph.get_edge(pred, node_id)
            ]
            features[i, 3 + num_node_types] = (
                np.mean(incoming_weights) if incoming_weights else 0.5
            )

        return torch.tensor(features, dtype=torch.float)

    def _compute_confidence(self) -> float:
        """Compute confidence in GNN predictions."""
        if not self.training_history:
            return 0.5

        # Based on final training loss
        final_loss = self.training_history[-1].get("train_loss", 1.0)
        loss_confidence = max(0.0, 1.0 - final_loss)

        # Based on training completion
        epochs_run = len(self.training_history)
        completion_ratio = epochs_run / self.gnn_config.epochs

        return 0.7 * loss_confidence + 0.3 * completion_ratio

    def save(self, path: str) -> None:
        """Save the trained model to disk.

        Args:
            path: Path to save the model
        """
        if not self.is_fitted:
            raise GNNNotFittedError()

        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "config": self.config,
                "gnn_config": self.gnn_config,
                "feature_dim": self._feature_dim,
                "training_history": self.training_history,
            },
            path,
        )

    @classmethod
    def load(cls, path: str) -> "GNNPropagator":
        """Load a trained model from disk.

        Args:
            path: Path to load the model from

        Returns:
            Loaded GNNPropagator
        """
        _check_torch_geometric()

        checkpoint = torch.load(path, map_location="cpu")

        propagator = cls(
            config=checkpoint["config"],
            gnn_config=checkpoint["gnn_config"],
        )

        propagator._feature_dim = checkpoint["feature_dim"]
        propagator.training_history = checkpoint["training_history"]

        propagator.model = TrustGNN(
            input_dim=propagator._feature_dim,
            hidden_dim=propagator.gnn_config.hidden_dim,
            num_layers=propagator.gnn_config.num_layers,
            dropout=propagator.gnn_config.dropout,
            architecture=propagator.gnn_config.architecture,
            heads=propagator.gnn_config.heads,
        )
        propagator.model.load_state_dict(checkpoint["model_state_dict"])
        propagator._fitted = True

        return propagator
