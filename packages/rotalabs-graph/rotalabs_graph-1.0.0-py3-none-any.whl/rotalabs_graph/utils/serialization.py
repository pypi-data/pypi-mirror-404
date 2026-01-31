"""Serialization utilities for rotalabs-graph.

This module provides functions for serializing and deserializing
trust graphs in various formats:

- JSON: Human-readable, portable format
- GraphML: Standard graph exchange format
- Adjacency Matrix: Numerical representation for analysis

Example:
    >>> from rotalabs_graph.temporal import TemporalTrustGraph
    >>> from rotalabs_graph.utils.serialization import to_json, from_json
    >>>
    >>> graph = TemporalTrustGraph()
    >>> graph.add_node("agent-1", 0.9)
    >>> graph.add_node("agent-2", 0.8)
    >>> graph.add_edge("agent-1", "agent-2", 0.7)
    >>>
    >>> # Save to JSON
    >>> json_str = to_json(graph)
    >>> to_json(graph, path="graph.json")
    >>>
    >>> # Load from JSON
    >>> loaded = from_json(json_str)
"""

import json
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from rotalabs_graph.temporal import TemporalTrustGraph
    import numpy as np


def to_json(
    graph: "TemporalTrustGraph",
    path: Optional[str] = None,
    indent: int = 2,
    include_history: bool = False,
) -> str:
    """Serialize trust graph to JSON format.

    Converts the graph to a JSON representation that can be
    stored, transmitted, and later deserialized.

    Args:
        graph: Trust graph to serialize
        path: Optional file path to write JSON to
        indent: JSON indentation level (None for compact)
        include_history: Whether to include trust history events

    Returns:
        JSON string representation of the graph

    Example:
        >>> from rotalabs_graph.temporal import TemporalTrustGraph
        >>> graph = TemporalTrustGraph()
        >>> graph.add_node("agent-1", 0.9)
        >>> json_str = to_json(graph)
        >>> '"agent-1"' in json_str
        True
        >>> to_json(graph, path="graph.json")
        '...'
    """
    data = {
        "format": "rotalabs-graph",
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "config": {
            "decay_function": graph.decay_function.value,
            "half_life_days": graph.half_life,
        },
        "nodes": [],
        "edges": [],
    }

    # Serialize nodes
    for node_id in graph.nodes:
        node_data = graph._nodes[node_id]
        data["nodes"].append({
            "id": node_id,
            "trust": node_data["trust"],
            "last_updated": node_data["last_updated"].isoformat(),
            "created_at": node_data["created_at"].isoformat(),
            "metadata": node_data.get("metadata", {}),
        })

    # Serialize edges
    for edge_key in graph.edges:
        source, target = edge_key
        edge_data = graph._edges[edge_key]
        data["edges"].append({
            "source": source,
            "target": target,
            "weight": edge_data["weight"],
            "last_updated": edge_data["last_updated"].isoformat(),
            "created_at": edge_data["created_at"].isoformat(),
            "metadata": edge_data.get("metadata", {}),
        })

    # Optionally include history
    if include_history and graph.history:
        data["history"] = [
            event.to_dict()
            for event in graph.history._events
        ]

    json_str = json.dumps(data, indent=indent)

    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(json_str)

    return json_str


def from_json(data: str) -> "TemporalTrustGraph":
    """Deserialize trust graph from JSON format.

    Loads a graph from JSON data (string or file path).

    Args:
        data: JSON string or path to JSON file

    Returns:
        TemporalTrustGraph instance

    Raises:
        ValueError: If JSON format is invalid

    Example:
        >>> json_str = '{"format": "rotalabs-graph", "version": "1.0", ...}'
        >>> graph = from_json(json_str)
        >>> graph = from_json("graph.json")  # From file
    """
    from rotalabs_graph.temporal import TemporalTrustGraph

    # Try to parse as JSON string first
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        # Assume it's a file path
        with open(data, "r", encoding="utf-8") as f:
            parsed = json.load(f)

    # Validate format
    if parsed.get("format") != "rotalabs-graph":
        raise ValueError("Invalid format: expected 'rotalabs-graph'")

    config = parsed.get("config", {})
    graph = TemporalTrustGraph(
        decay_function=config.get("decay_function", "exponential"),
        half_life_days=config.get("half_life_days", 30.0),
        track_history=True,
    )

    # Load nodes
    for node_data in parsed.get("nodes", []):
        node_id = node_data["id"]
        # Directly set node data to preserve timestamps
        graph._nodes[node_id] = {
            "trust": node_data["trust"],
            "last_updated": datetime.fromisoformat(node_data["last_updated"]),
            "created_at": datetime.fromisoformat(node_data["created_at"]),
            "metadata": node_data.get("metadata", {}),
        }

    # Load edges
    for edge_data in parsed.get("edges", []):
        edge_key = (edge_data["source"], edge_data["target"])
        graph._edges[edge_key] = {
            "weight": edge_data["weight"],
            "last_updated": datetime.fromisoformat(edge_data["last_updated"]),
            "created_at": datetime.fromisoformat(edge_data["created_at"]),
            "metadata": edge_data.get("metadata", {}),
        }

    # Load history if present
    if "history" in parsed and graph.history:
        from rotalabs_graph.temporal.history import TrustEvent
        for event_data in parsed["history"]:
            event = TrustEvent.from_dict(event_data)
            graph.history._add_event(event)

    return graph


def to_graphml(graph: "TemporalTrustGraph", path: str) -> None:
    """Export trust graph to GraphML format.

    GraphML is an XML-based format for graphs that is supported
    by many graph analysis tools (Gephi, NetworkX, etc.).

    Args:
        graph: Trust graph to export
        path: File path to write GraphML to

    Example:
        >>> from rotalabs_graph.temporal import TemporalTrustGraph
        >>> graph = TemporalTrustGraph()
        >>> graph.add_node("a", 0.9)
        >>> graph.add_node("b", 0.8)
        >>> graph.add_edge("a", "b", 0.7)
        >>> to_graphml(graph, "graph.graphml")
    """
    # Build GraphML XML
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"',
        '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns',
        '         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">',
        '',
        '  <!-- Node attributes -->',
        '  <key id="trust" for="node" attr.name="trust" attr.type="double"/>',
        '  <key id="last_updated" for="node" attr.name="last_updated" attr.type="string"/>',
        '',
        '  <!-- Edge attributes -->',
        '  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>',
        '',
        '  <graph id="trust_graph" edgedefault="directed">',
    ]

    # Add nodes
    for node_id in graph.nodes:
        node_data = graph._nodes[node_id]
        lines.append(f'    <node id="{_escape_xml(node_id)}">')
        lines.append(f'      <data key="trust">{node_data["trust"]}</data>')
        lines.append(f'      <data key="last_updated">{node_data["last_updated"].isoformat()}</data>')
        lines.append('    </node>')

    # Add edges
    for i, edge_key in enumerate(graph.edges):
        source, target = edge_key
        edge_data = graph._edges[edge_key]
        lines.append(f'    <edge id="e{i}" source="{_escape_xml(source)}" target="{_escape_xml(target)}">')
        lines.append(f'      <data key="weight">{edge_data["weight"]}</data>')
        lines.append('    </edge>')

    lines.append('  </graph>')
    lines.append('</graphml>')

    with open(path, "w", encoding="utf-8") as f:
        f.write('\n'.join(lines))


def from_graphml(path: str) -> "TemporalTrustGraph":
    """Import trust graph from GraphML format.

    Args:
        path: Path to GraphML file

    Returns:
        TemporalTrustGraph instance

    Example:
        >>> graph = from_graphml("graph.graphml")
        >>> graph.nodes
        ['a', 'b']
    """
    from rotalabs_graph.temporal import TemporalTrustGraph
    import xml.etree.ElementTree as ET

    tree = ET.parse(path)
    root = tree.getroot()

    # Handle GraphML namespace
    ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}

    graph = TemporalTrustGraph(track_history=False)

    # Find the graph element
    graph_elem = root.find('.//graphml:graph', ns)
    if graph_elem is None:
        # Try without namespace
        graph_elem = root.find('.//graph')

    if graph_elem is None:
        raise ValueError("No graph element found in GraphML file")

    # Parse nodes
    for node_elem in graph_elem.findall('graphml:node', ns) or graph_elem.findall('node'):
        node_id = node_elem.get('id')

        # Get trust value from data elements
        trust = 0.5  # Default
        for data_elem in node_elem.findall('graphml:data', ns) or node_elem.findall('data'):
            if data_elem.get('key') == 'trust':
                trust = float(data_elem.text or 0.5)
                break

        graph.add_node(node_id, trust)

    # Parse edges
    for edge_elem in graph_elem.findall('graphml:edge', ns) or graph_elem.findall('edge'):
        source = edge_elem.get('source')
        target = edge_elem.get('target')

        # Get weight from data elements
        weight = 1.0  # Default
        for data_elem in edge_elem.findall('graphml:data', ns) or edge_elem.findall('data'):
            if data_elem.get('key') == 'weight':
                weight = float(data_elem.text or 1.0)
                break

        if source in graph and target in graph:
            graph.add_edge(source, target, weight)

    return graph


def to_adjacency_matrix(
    graph: "TemporalTrustGraph",
    node_order: Optional[List[str]] = None,
    use_current_trust: bool = True,
) -> "np.ndarray":
    """Convert graph to adjacency matrix representation.

    Creates a weighted adjacency matrix where entry [i,j] is the
    edge weight from node i to node j, or 0 if no edge exists.

    Args:
        graph: Trust graph to convert
        node_order: Order of nodes in matrix (default: sorted)
        use_current_trust: Whether to apply decay to edge weights

    Returns:
        NumPy ndarray of shape (n_nodes, n_nodes)

    Raises:
        ImportError: If numpy is not installed

    Example:
        >>> from rotalabs_graph.temporal import TemporalTrustGraph
        >>> graph = TemporalTrustGraph()
        >>> graph.add_node("a", 0.9)
        >>> graph.add_node("b", 0.8)
        >>> graph.add_edge("a", "b", 0.7)
        >>> matrix = to_adjacency_matrix(graph)
        >>> matrix.shape
        (2, 2)
        >>> matrix[0, 1]
        0.7
    """
    try:
        import numpy as np
    except ImportError:
        raise ImportError(
            "numpy is required for to_adjacency_matrix(). "
            "Install with: pip install numpy"
        )

    if node_order is None:
        node_order = sorted(graph.nodes)

    n = len(node_order)
    node_to_idx = {node: i for i, node in enumerate(node_order)}

    matrix = np.zeros((n, n), dtype=np.float64)

    for edge_key in graph.edges:
        source, target = edge_key
        if source in node_to_idx and target in node_to_idx:
            i = node_to_idx[source]
            j = node_to_idx[target]

            if use_current_trust:
                weight = graph.get_edge_weight(source, target)
            else:
                weight = graph._edges[edge_key]["weight"]

            matrix[i, j] = weight

    return matrix


def from_adjacency_matrix(
    matrix: "np.ndarray",
    node_ids: Optional[List[str]] = None,
    threshold: float = 0.0,
) -> "TemporalTrustGraph":
    """Create graph from adjacency matrix.

    Args:
        matrix: Weighted adjacency matrix
        node_ids: IDs for each node (default: "node_0", "node_1", ...)
        threshold: Minimum weight to create an edge

    Returns:
        TemporalTrustGraph instance

    Example:
        >>> import numpy as np
        >>> matrix = np.array([[0, 0.7], [0, 0]])
        >>> graph = from_adjacency_matrix(matrix, ["a", "b"])
        >>> graph.get_edge_weight("a", "b")
        0.7
    """
    from rotalabs_graph.temporal import TemporalTrustGraph

    n = matrix.shape[0]
    if matrix.shape[1] != n:
        raise ValueError("Adjacency matrix must be square")

    if node_ids is None:
        node_ids = [f"node_{i}" for i in range(n)]

    if len(node_ids) != n:
        raise ValueError(f"Expected {n} node IDs, got {len(node_ids)}")

    graph = TemporalTrustGraph(track_history=False)

    # Add nodes (use diagonal for self-trust, or default 0.5)
    for i, node_id in enumerate(node_ids):
        diagonal_value = matrix[i, i]
        trust = diagonal_value if diagonal_value > 0 else 0.5
        graph.add_node(node_id, trust)

    # Add edges
    for i in range(n):
        for j in range(n):
            if i != j and matrix[i, j] > threshold:
                graph.add_edge(node_ids[i], node_ids[j], matrix[i, j])

    return graph


def to_networkx(graph: "TemporalTrustGraph") -> "nx.DiGraph":
    """Convert to NetworkX directed graph.

    Args:
        graph: Trust graph to convert

    Returns:
        NetworkX DiGraph with trust as node attribute
        and weight as edge attribute

    Raises:
        ImportError: If networkx is not installed

    Example:
        >>> from rotalabs_graph.temporal import TemporalTrustGraph
        >>> graph = TemporalTrustGraph()
        >>> graph.add_node("a", 0.9)
        >>> nx_graph = to_networkx(graph)
        >>> nx_graph.nodes["a"]["trust"]
        0.9
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError(
            "networkx is required for to_networkx(). "
            "Install with: pip install networkx"
        )

    G = nx.DiGraph()

    # Add nodes with attributes
    for node_id in graph.nodes:
        node_data = graph._nodes[node_id]
        G.add_node(
            node_id,
            trust=node_data["trust"],
            last_updated=node_data["last_updated"].isoformat(),
            **node_data.get("metadata", {}),
        )

    # Add edges with attributes
    for edge_key in graph.edges:
        source, target = edge_key
        edge_data = graph._edges[edge_key]
        G.add_edge(
            source,
            target,
            weight=edge_data["weight"],
            last_updated=edge_data["last_updated"].isoformat(),
            **edge_data.get("metadata", {}),
        )

    return G


def from_networkx(G: "nx.DiGraph") -> "TemporalTrustGraph":
    """Create trust graph from NetworkX graph.

    Args:
        G: NetworkX DiGraph with 'trust' node attribute
           and 'weight' edge attribute

    Returns:
        TemporalTrustGraph instance

    Example:
        >>> import networkx as nx
        >>> G = nx.DiGraph()
        >>> G.add_node("a", trust=0.9)
        >>> G.add_node("b", trust=0.8)
        >>> G.add_edge("a", "b", weight=0.7)
        >>> graph = from_networkx(G)
    """
    from rotalabs_graph.temporal import TemporalTrustGraph

    graph = TemporalTrustGraph(track_history=False)

    # Add nodes
    for node_id in G.nodes():
        node_attrs = dict(G.nodes[node_id])
        trust = node_attrs.pop("trust", 0.5)
        node_attrs.pop("last_updated", None)  # Remove internal attrs
        graph.add_node(node_id, trust, metadata=node_attrs if node_attrs else None)

    # Add edges
    for source, target in G.edges():
        edge_attrs = dict(G.edges[source, target])
        weight = edge_attrs.pop("weight", 1.0)
        edge_attrs.pop("last_updated", None)
        graph.add_edge(source, target, weight, metadata=edge_attrs if edge_attrs else None)

    return graph


def _escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
