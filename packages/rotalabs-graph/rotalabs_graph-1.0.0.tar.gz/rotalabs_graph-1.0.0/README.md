# rotalabs-graph

[![PyPI version](https://img.shields.io/pypi/v/rotalabs-graph.svg)](https://pypi.org/project/rotalabs-graph/)
[![Python versions](https://img.shields.io/pypi/pyversions/rotalabs-graph.svg)](https://pypi.org/project/rotalabs-graph/)
[![License](https://img.shields.io/pypi/l/rotalabs-graph.svg)](https://github.com/rotalabs/rotalabs-graph/blob/main/LICENSE)

GNN-based trust propagation for AI systems.

## Features

- **Trust Graph Data Structure**: Model trust relationships between AI components
- **Multiple Propagation Algorithms**: PageRank, EigenTrust, weighted propagation, and GNN-based
- **Anomaly Detection**: Detect circular trust, trust islands, and suspicious patterns
- **Path Analysis**: Find trust paths and bottlenecks between nodes
- **Cluster Analysis**: Identify trust communities using Louvain, label propagation, etc.
- **Temporal Trust**: Trust decay over time with history tracking
- **Graph Metrics**: Comprehensive metrics for trust health analysis

## Installation

```bash
pip install rotalabs-graph
```

With GNN support (requires PyTorch):

```bash
pip install rotalabs-graph[gnn]
```

With visualization:

```bash
pip install rotalabs-graph[viz]
```

## Quick Start

### Create a Trust Graph

```python
from datetime import datetime
from rotalabs_graph import TrustGraph, TrustNode, TrustEdge, NodeType, EdgeType

# Create graph
graph = TrustGraph()

# Add nodes
now = datetime.now()
graph.add_node(TrustNode(
    id="user-1",
    name="User",
    node_type=NodeType.USER,
    base_trust=1.0,
    created_at=now,
    updated_at=now,
))

graph.add_node(TrustNode(
    id="model-gpt4",
    name="GPT-4",
    node_type=NodeType.MODEL,
    base_trust=0.95,
    created_at=now,
    updated_at=now,
))

# Add trust edge
graph.add_edge(TrustEdge(
    source_id="user-1",
    target_id="model-gpt4",
    edge_type=EdgeType.TRUSTS,
    weight=0.9,
    created_at=now,
))

print(f"Graph: {graph.num_nodes} nodes, {graph.num_edges} edges")
```

### Detect Anomalies

```python
from rotalabs_graph import AnomalyDetector

detector = AnomalyDetector()
anomalies = detector.detect_all(graph)

for anomaly in anomalies:
    print(f"{anomaly.anomaly_type}: {anomaly.description}")
```

### Find Trust Paths

```python
from rotalabs_graph import PathAnalyzer

analyzer = PathAnalyzer()
paths = analyzer.find_all_paths(graph, "user-1", "model-gpt4")

for path in paths:
    print(f"Path: {' -> '.join(path.node_ids)}, trust: {path.path_trust:.3f}")
```

### Temporal Trust with Decay

```python
from rotalabs_graph import TemporalTrustGraph, DecayFunction

# Create temporal graph with exponential decay
graph = TemporalTrustGraph(
    decay_function=DecayFunction.EXPONENTIAL,
    half_life_days=30.0,
    track_history=True,
)

# Add node
graph.add_node("agent-1", initial_trust=0.9)

# Get current trust (with decay applied)
current = graph.get_current_trust("agent-1")
```

## Node Types

| Type | Description |
|------|-------------|
| `MODEL` | AI/ML models |
| `AGENT` | AI agents |
| `USER` | Human users |
| `DATA_SOURCE` | Data sources |
| `TOOL` | Tools and APIs |
| `SERVICE` | External services |

## Edge Types

| Type | Description |
|------|-------------|
| `TRUSTS` | General trust relationship |
| `DELEGATES` | Delegates authority to |
| `VERIFIES` | Verifies outputs of |
| `VALIDATES` | Validates results from |
| `DEPENDS_ON` | Depends on for operation |
| `CALLS` | Calls/invokes |
| `OWNS` | Owns/controls |

## Propagation Algorithms

| Algorithm | Description |
|-----------|-------------|
| `PageRankPropagator` | Trust as voting, with damping |
| `EigenTrustPropagator` | Stationary distribution (Kamvar et al., 2003) |
| `WeightedPropagator` | BFS with decay per hop |
| `GNNPropagator` | Learned propagation with GCN/GAT/SAGE |

## Anomaly Types

| Type | Description |
|------|-------------|
| `CIRCULAR_TRUST` | A trusts B trusts A |
| `TRUST_ISLAND` | Disconnected component |
| `SUSPICIOUS_CONCENTRATION` | Too many edges to one node |
| `TRUST_CLIFF` | Sudden trust drop in path |
| `ORPHAN_NODE` | Node with no connections |

## API Reference

### Core Types

- `TrustGraph` - Main graph data structure
- `TrustNode` - Node representing an entity
- `TrustEdge` - Directed trust relationship
- `TrustScore` - Computed trust value
- `NodeType`, `EdgeType` - Type enumerations

### Propagation

- `PageRankPropagator` - PageRank-based trust
- `EigenTrustPropagator` - EigenTrust algorithm
- `WeightedPropagator` - Weighted path propagation
- `GNNPropagator` - GNN-based (requires torch-geometric)

### Analysis

- `AnomalyDetector` - Detect trust anomalies
- `PathAnalyzer` - Analyze trust paths
- `ClusterAnalyzer` - Community detection
- `MetricsCalculator` - Graph-level metrics

### Temporal

- `TemporalTrustGraph` - Trust with decay
- `TrustHistory` - Track trust changes
- `DecayFunction` - Decay function types

## Links

- Documentation: https://rotalabs.github.io/rotalabs-graph/
- PyPI: https://pypi.org/project/rotalabs-graph/
- GitHub: https://github.com/rotalabs/rotalabs-graph
- Website: https://rotalabs.ai
- Contact: research@rotalabs.ai

## License

MIT License - see LICENSE file for details.
