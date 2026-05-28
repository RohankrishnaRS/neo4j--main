import streamlit as st
import os
import streamlit.components.v1 as components
from dotenv import load_dotenv
from neo4j_client import Neo4jClient

load_dotenv()

# ── Neo4j init ───────────────────────────────────────────────
db = Neo4jClient()

# ── Neo4j helper functions ───────────────────────────────────

def neo_store_graph(entities, relations):
    try:
        for name, label in entities.items():
            if name:  # Skip empty names
                db.create_node(label or "Entity", {"name": name})

        for r in relations:
            if r.get("source") and r.get("target") and r.get("relation"):  # Validate
                db.create_relationship(
                    "Entity",
                    "Entity",
                    r["relation"],
                    {"name": r["source"]},
                    {"name": r["target"]},
                )
    except Exception as e:
        st.error(f"Error storing graph in Neo4j: {str(e)}")
        raise


def neo_fetch_graph():
    query = """
    MATCH (a)-[r]->(b)
    RETURN a.name AS source, type(r) AS relation, b.name AS target
    """
    result = db.query(query)

    nodes = set()
    edges = []

    for record in result:
        nodes.add(record["source"])
        nodes.add(record["target"])
        edges.append(
            (record["source"], record["relation"], record["target"])
        )

    return {"nodes": list(nodes), "edges": edges}


def neo_clear_graph():
    db.query("MATCH (n) DETACH DELETE n")


def neo_db_stats():
    result = db.query("""
    MATCH (n)
    OPTIONAL MATCH ()-[r]->()
    RETURN count(DISTINCT n) AS entities, count(DISTINCT r) AS relations
    """)
    return result[0] if result else {"entities": 0, "relations": 0}


# ── Existing imports ─────────────────────────────────────────
from graph_kb.extractor import extract_text, build_knowledge_graph, query_graph, index_exists
from graph_kb.visualizer import build_pyvis_graph, build_networkx_summary


# ── Streamlit UI ─────────────────────────────────────────────
st.set_page_config(page_title="Knowledge Graph Builder", page_icon="🕸️", layout="wide")

st.title("🕸️ Knowledge Graph Builder")
st.caption("Upload → Extract KG → Store in Neo4j → Explore")

# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.subheader("⚙️ Extraction settings")
    max_triplets = st.slider("Max triplets per chunk", 10, 50, 30)

    st.divider()
    st.subheader("🗄️ Database")

    stats = neo_db_stats()

    st.caption("Neo4j AuraDB (Cloud)")
    col_a, col_b = st.columns(2)
    col_a.metric("Entities", stats["entities"])
    col_b.metric("Relations", stats["relations"])

    if st.button("🗑️ Clear Graph"):
        neo_clear_graph()
        st.success("Graph cleared.")
        st.rerun()

# ── Tabs ────────────────────────────────────────────────────
tab_upload, tab_explore, tab_qa = st.tabs(["📤 Upload & Analyze", "🔍 Explore Graph", "💬 Ask the Graph"])


# ────────────────────────────────────────────────────────────
# TAB 1 – Upload & Analyze
# ────────────────────────────────────────────────────────────
with tab_upload:
    uploaded = st.file_uploader("Upload file", type=["txt", "pdf", "csv", "docx"])

    if uploaded:
        file_ext = uploaded.name.rsplit(".", 1)[-1].lower()

        raw_text = extract_text(uploaded, file_ext)

        with st.expander("📄 Extracted text"):
            st.text_area("", raw_text[:2000])

        if st.button("🧠 Build Knowledge Graph"):
            result = build_knowledge_graph(
                uploaded,
                file_ext,
                max_triplets_per_chunk=max_triplets
            )

            entities = result["entities"]
            relations = result["relations"]

            st.success("Graph extracted ✅")

            # ✅ STORE IN NEO4J
            neo_store_graph(entities, relations)

            st.success("Stored in Neo4j ✅")

            edges = [(r["source"], r["relation"], r["target"]) for r in relations]

            if edges:
                html_path = build_pyvis_graph(entities, edges)
                with open(html_path, "r", encoding="utf-8") as f:
                    components.html(f.read(), height=600)

                os.unlink(html_path)


# ────────────────────────────────────────────────────────────
# TAB 2 – Explore
# ────────────────────────────────────────────────────────────
with tab_explore:
    if st.button("🔄 Load Graph"):
        graph_data = neo_fetch_graph()

        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        if not nodes:
            st.warning("Graph empty")
        else:
            summary = build_networkx_summary(nodes, edges)

            c1, c2, c3 = st.columns(3)
            c1.metric("Nodes", summary["num_nodes"])
            c2.metric("Edges", summary["num_edges"])
            c3.metric("Density", summary["density"])

            html_path = build_pyvis_graph(nodes, edges)

            with open(html_path, "r", encoding="utf-8") as f:
                components.html(f.read(), height=600)

            os.unlink(html_path)


# ────────────────────────────────────────────────────────────
# TAB 3 – Q&A
# ────────────────────────────────────────────────────────────
with tab_qa:
    if not index_exists():
        st.info("Upload a document first")
    else:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        question = st.chat_input("Ask something...")

        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})

            with st.chat_message("assistant"):
                result = query_graph(question)

                st.markdown(result["answer"])

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["answer"]
            })

        if st.button("🗑️ Clear chat"):
            st.session_state.chat_history = []
            st.rerun()
