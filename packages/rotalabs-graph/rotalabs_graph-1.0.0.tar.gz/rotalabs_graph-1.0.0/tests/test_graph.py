"""Tests for TrustGraph functionality."""

import pytest
from datetime import datetime


def test_create_empty_graph():
    """Test creating an empty graph."""
    from rotalabs_graph import TrustGraph

    graph = TrustGraph()

    assert graph.num_nodes == 0
    assert graph.num_edges == 0
    assert graph.is_directed is True


def test_add_node():
    """Test adding nodes to graph."""
    from rotalabs_graph import TrustGraph, TrustNode, NodeType

    graph = TrustGraph()

    node = TrustNode(
        id="model-1",
        name="GPT-4",
        node_type=NodeType.MODEL,
        base_trust=0.95,
        metadata={"provider": "openai"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    node_id = graph.add_node(node)

    assert node_id == "model-1"
    assert graph.num_nodes == 1
    assert graph.has_node("model-1")


def test_add_edge():
    """Test adding edges to graph."""
    from rotalabs_graph import TrustGraph, TrustNode, TrustEdge, NodeType, EdgeType

    graph = TrustGraph()
    now = datetime.utcnow()

    # Add nodes
    node1 = TrustNode(
        id="user-1", name="User", node_type=NodeType.USER,
        base_trust=1.0, created_at=now, updated_at=now
    )
    node2 = TrustNode(
        id="model-1", name="Model", node_type=NodeType.MODEL,
        base_trust=0.9, created_at=now, updated_at=now
    )

    graph.add_node(node1)
    graph.add_node(node2)

    # Add edge
    edge = TrustEdge(
        source_id="user-1",
        target_id="model-1",
        edge_type=EdgeType.TRUSTS,
        weight=0.85,
        created_at=now,
    )

    edge_id = graph.add_edge(edge)

    assert graph.num_edges == 1
    assert graph.has_edge("user-1", "model-1")


def test_get_neighbors():
    """Test getting node neighbors."""
    from rotalabs_graph import TrustGraph, TrustNode, TrustEdge, NodeType, EdgeType

    graph = TrustGraph()
    now = datetime.utcnow()

    # Create a chain: A -> B -> C
    for name in ["A", "B", "C"]:
        graph.add_node(TrustNode(
            id=name, name=name, node_type=NodeType.MODEL,
            base_trust=0.9, created_at=now, updated_at=now
        ))

    graph.add_edge(TrustEdge(
        source_id="A", target_id="B", edge_type=EdgeType.TRUSTS,
        weight=0.8, created_at=now
    ))
    graph.add_edge(TrustEdge(
        source_id="B", target_id="C", edge_type=EdgeType.TRUSTS,
        weight=0.7, created_at=now
    ))

    # A's successors should be [B]
    successors = graph.get_successors("A")
    assert len(successors) == 1
    assert successors[0].id == "B"

    # B's predecessors should be [A]
    predecessors = graph.get_predecessors("B")
    assert len(predecessors) == 1
    assert predecessors[0].id == "A"


def test_remove_node():
    """Test removing nodes from graph."""
    from rotalabs_graph import TrustGraph, TrustNode, NodeType

    graph = TrustGraph()
    now = datetime.utcnow()

    graph.add_node(TrustNode(
        id="test", name="Test", node_type=NodeType.MODEL,
        base_trust=0.9, created_at=now, updated_at=now
    ))

    assert graph.has_node("test")

    removed = graph.remove_node("test")

    assert removed is True
    assert not graph.has_node("test")
    assert graph.num_nodes == 0


def test_subgraph():
    """Test creating a subgraph."""
    from rotalabs_graph import TrustGraph, TrustNode, TrustEdge, NodeType, EdgeType

    graph = TrustGraph()
    now = datetime.utcnow()

    # Create 4 nodes
    for i in range(4):
        graph.add_node(TrustNode(
            id=f"node-{i}", name=f"Node {i}", node_type=NodeType.MODEL,
            base_trust=0.9, created_at=now, updated_at=now
        ))

    # Create edges
    for i in range(3):
        graph.add_edge(TrustEdge(
            source_id=f"node-{i}", target_id=f"node-{i+1}",
            edge_type=EdgeType.TRUSTS, weight=0.8, created_at=now
        ))

    # Create subgraph with only first 2 nodes
    sub = graph.subgraph(["node-0", "node-1"])

    assert sub.num_nodes == 2
    assert sub.num_edges == 1  # Only edge between node-0 and node-1


def test_to_dict_from_dict():
    """Test graph serialization."""
    from rotalabs_graph import TrustGraph, TrustNode, TrustEdge, NodeType, EdgeType

    graph = TrustGraph()
    now = datetime.utcnow()

    graph.add_node(TrustNode(
        id="n1", name="Node 1", node_type=NodeType.MODEL,
        base_trust=0.9, created_at=now, updated_at=now
    ))
    graph.add_node(TrustNode(
        id="n2", name="Node 2", node_type=NodeType.AGENT,
        base_trust=0.8, created_at=now, updated_at=now
    ))
    graph.add_edge(TrustEdge(
        source_id="n1", target_id="n2",
        edge_type=EdgeType.DELEGATES, weight=0.75, created_at=now
    ))

    # Serialize
    data = graph.to_dict()

    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1

    # Deserialize
    restored = TrustGraph.from_dict(data)

    assert restored.num_nodes == 2
    assert restored.num_edges == 1
    assert restored.has_node("n1")
    assert restored.has_edge("n1", "n2")
