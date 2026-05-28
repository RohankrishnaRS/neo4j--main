import networkx as nx
from pyvis.network import Network
import tempfile

# ── Colors for node types ───────────────────────────────────
TYPE_COLORS = {
    "PERSON": "#4e79a7",
    "ORG": "#f28e2b",
    "GPE": "#e15759",
    "LOC": "#76b7b2",
    "DATE": "#59a14f",
    "EVENT": "#edc948",
    "PRODUCT": "#b07aa1",
    "WORK_OF_ART": "#ff9da7",
    "Entity": "#9c755f",  # Neo4j default
    "default": "#9c755f",
}


# ── Build interactive graph ─────────────────────────────────
def build_pyvis_graph(nodes: dict, edges: list) -> str:
    """Build PyVis graph and return HTML file path."""

    net = Network(
        height="600px",
        width="100%",
        bgcolor="#1e1e2e",
        font_color="white",
        directed=True
    )

    net.barnes_hut()

    added_nodes = set()

    # Add nodes
    for name, etype in nodes.items():
        etype = etype or "Entity"
        color = TYPE_COLORS.get(etype, TYPE_COLORS["default"])

        net.add_node(
            name,
            label=name,
            title=f"Type: {etype}",
            color=color,
            size=20
        )

        added_nodes.add(name)

    # Add edges
    for src, rel, tgt in edges:
        src = str(src).strip()
        tgt = str(tgt).strip()
        rel = str(rel).replace("_", " ").title()  # Neo4j → readable

        # Ensure nodes exist
        for n in (src, tgt):
            if n not in added_nodes:
                net.add_node(
                    n,
                    label=n,
                    title="Type: Unknown",
                    color=TYPE_COLORS["default"],
                    size=20
                )
                added_nodes.add(n)

        net.add_edge(
            src,
            tgt,
            label=rel,
            title=rel,
            arrows="to"
        )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.save_graph(tmp.name)
    tmp.close()

    return tmp.name


# ── Graph summary (NetworkX) ────────────────────────────────
def build_networkx_summary(nodes: dict, edges: list) -> dict:
    """Return graph statistics."""

    G = nx.DiGraph()

    # Add nodes
    for name in nodes:
        G.add_node(name)

    # Add edges
    for src, rel, tgt in edges:
        G.add_edge(src, tgt, relation=rel)

    # Stats
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    density = nx.density(G) if num_nodes > 1 else 0

    # Top nodes by degree
    top_nodes = sorted(
        G.degree(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "density": round(density, 4),
        "top_nodes": top_nodes,
    }
