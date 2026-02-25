"""
Graph Agent — extracts concepts and relationships from course material
and returns structured data for building an interactive knowledge graph.
"""

import os
import json
import re
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage


SYSTEM_PROMPT = """You are an expert Knowledge Graph Builder for academic content.
Your job is to analyze course material and extract a rich, structured knowledge graph.

Respond ONLY with a valid JSON object in this exact format:
{
  "title": "Topic title derived from the content",
  "nodes": [
    {
      "id": "unique_snake_case_id",
      "label": "Display Name",
      "category": "core|concept|method|example|definition|person|formula",
      "description": "One sentence description of this concept",
      "importance": 1-5
    }
  ],
  "edges": [
    {
      "source": "node_id",
      "target": "node_id",
      "relation": "short relation label (e.g. 'uses', 'leads to', 'is part of', 'defined by', 'enables')",
      "strength": 1-3
    }
  ]
}

Rules:
- Extract 15-35 nodes for rich graphs (aim for 20+)
- Extract 20-50 edges showing meaningful relationships
- Categories:
  * core: the main top-level subject (1-3 nodes max)
  * concept: key ideas and theories
  * method: algorithms, processes, techniques
  * definition: formal definitions and terms
  * example: concrete examples or use cases
  * person: researchers, authors
  * formula: equations or formulas
- Importance: 5=central to understanding, 1=supplementary
- Relations should be specific and directional: "enables", "is a type of", "requires", "produces", "contrasts with", "derived from"
- Every node must appear in at least one edge
- Do NOT include any text outside the JSON object"""


CATEGORY_COLORS = {
    "core":       "#6366f1",   # Indigo
    "concept":    "#38bdf8",   # Sky blue
    "method":     "#34d399",   # Emerald
    "definition": "#f59e0b",   # Amber
    "example":    "#f472b6",   # Pink
    "person":     "#a78bfa",   # Violet
    "formula":    "#fb923c",   # Orange
}

CATEGORY_SHAPES = {
    "core":       "star",
    "concept":    "dot",
    "method":     "diamond",
    "definition": "square",
    "example":    "triangle",
    "person":     "ellipse",
    "formula":    "database",
}


def get_llm():
    return ChatMistralAI(
        model="mistral-large-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.2,
    )


def extract_graph_data(content: str, user_hint: str = "") -> dict:
    """
    Use Mistral to extract nodes and edges from course content.
    Returns parsed JSON graph data.
    """
    llm = get_llm()

    max_chars = 10000
    if len(content) > max_chars:
        content = content[:max_chars] + "\n[Content truncated...]"

    hint = f"\nFocus especially on: {user_hint}" if user_hint else ""

    prompt = f"""Analyze this course material and extract a comprehensive knowledge graph.{hint}

--- COURSE MATERIAL ---
{content}
--- END ---

Extract all key concepts, their relationships, and build a rich knowledge graph.
Remember: respond with ONLY the JSON object, no other text."""

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    raw = response.content.strip()

    # Strip markdown code blocks if present
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        data = json.loads(raw)
        return data
    except json.JSONDecodeError:
        # Try to extract JSON object
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        return {"title": "Knowledge Graph", "nodes": [], "edges": [], "error": "Parse failed"}


def build_pyvis_html(graph_data: dict) -> str:
    """
    Build an interactive pyvis graph and return it as an HTML string.
    """
    try:
        import networkx as nx
        from pyvis.network import Network
    except ImportError:
        return "<p>Please install pyvis and networkx: pip install pyvis networkx</p>"

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    if not nodes:
        return "<p>No graph data to display.</p>"

    # Create pyvis network
    net = Network(
        height="620px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#1e293b",
        directed=True,
    )

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.01,
          "springLength": 120,
          "springConstant": 0.08,
          "damping": 0.6
        },
        "solver": "forceAtlas2Based",
        "stabilization": { "iterations": 150 }
      },
      "edges": {
        "arrows": { "to": { "enabled": true, "scaleFactor": 0.6 } },
        "smooth": { "type": "dynamic" },
        "font": { "size": 10, "color": "#64748b", "strokeWidth": 0 },
        "color": { "opacity": 0.7 }
      },
      "nodes": {
        "font": { "size": 13, "face": "Inter, sans-serif" },
        "borderWidth": 2,
        "shadow": true
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": false,
        "keyboard": true
      }
    }
    """)

    # Build node id lookup
    node_ids = {n["id"] for n in nodes}

    for node in nodes:
        category = node.get("category", "concept")
        importance = node.get("importance", 3)
        color = CATEGORY_COLORS.get(category, "#38bdf8")
        shape = CATEGORY_SHAPES.get(category, "dot")

        # Size based on importance (5 → 40px, 1 → 15px)
        size = 15 + (importance - 1) * 7

        net.add_node(
            node["id"],
            label=node.get("label", node["id"]),
            title=f"<b>{node.get('label', '')}</b><br><i>{category}</i><br>{node.get('description', '')}",
            color={
                "background": color,
                "border": "#ffffff30",
                "highlight": {"background": color, "border": "#ffffff"},
                "hover": {"background": color, "border": "#ffffff80"},
            },
            size=size,
            shape=shape,
            font={"color": "#1e293b", "size": max(11, importance * 2 + 8)},
        )

    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if src not in node_ids or tgt not in node_ids:
            continue

        strength = edge.get("strength", 1)
        width = strength * 1.5

        net.add_edge(
            src, tgt,
            label=edge.get("relation", ""),
            width=width,
            color={"color": "#4f6272", "highlight": "#818cf8", "hover": "#818cf8"},
        )

    # Generate HTML
    html = net.generate_html()
    return html


def build_stats(graph_data: dict) -> dict:
    """Compute basic graph statistics for display."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    categories = {}
    for n in nodes:
        cat = n.get("category", "concept")
        categories[cat] = categories.get(cat, 0) + 1

    # Find most connected nodes
    connections = {}
    for e in edges:
        connections[e.get("source", "")] = connections.get(e.get("source", ""), 0) + 1
        connections[e.get("target", "")] = connections.get(e.get("target", ""), 0) + 1

    top_nodes = sorted(connections.items(), key=lambda x: x[1], reverse=True)[:5]

    # Map IDs to labels
    id_to_label = {n["id"]: n.get("label", n["id"]) for n in nodes}
    top_concepts = [(id_to_label.get(nid, nid), count) for nid, count in top_nodes]

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "categories": categories,
        "top_concepts": top_concepts,
    }


def run_graph_agent(content: str, user_hint: str = "") -> dict:
    """
    Full pipeline: extract graph data from content and build visualization.

    Returns:
        {
          "graph_data": dict,      # Raw nodes/edges JSON
          "html": str,             # Pyvis HTML for rendering
          "stats": dict,           # Graph statistics
          "title": str,            # Graph title
        }
    """
    graph_data = extract_graph_data(content, user_hint)

    return {
        "graph_data": graph_data,
        "html": build_pyvis_html(graph_data),
        "stats": build_stats(graph_data),
        "title": graph_data.get("title", "Knowledge Graph"),
    }
