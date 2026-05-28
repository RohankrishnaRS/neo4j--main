import os
import tempfile
from pathlib import Path

from llama_index.core import (
    SimpleDirectoryReader,
    KnowledgeGraphIndex,
    Settings,
    load_index_from_storage,
)
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.azure_openai import AzureOpenAI

INDEX_PERSIST_DIR = Path("kg_index_store")


# ── LLM settings ─────────────────────────────────────────────
def _build_settings(chunk_size: int = 1024):
    Settings.llm = AzureOpenAI(
        model=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
    )
    Settings.embed_model = MockEmbedding(embed_dim=1)
    Settings.chunk_size = chunk_size
    Settings.chunk_overlap = chunk_size // 8


# ── KG extraction prompt ─────────────────────────────────────
KG_EXTRACT_PROMPT = PromptTemplate(
    "Extract as many (subject, predicate, object) triplets as possible.\n\n"
    "Rules:\n"
    "- Max {max_knowledge_triplets} triplets\n"
    "- Resolve pronouns\n"
    "- No vague entities\n"
    "- Use clean verb relations\n\n"
    "Format:\n(subject, predicate, object)\n\n"
    "Text:\n{text}\n\nTriplets:\n"
)


# ── Text extraction ─────────────────────────────────────────
def extract_text(file, file_type: str) -> str:
    if file_type == "txt":
        return file.read().decode("utf-8", errors="ignore")

    elif file_type == "pdf":
        import PyPDF2
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    elif file_type == "docx":
        from docx import Document
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)

    elif file_type == "csv":
        import pandas as pd
        df = pd.read_csv(file)
        return df.to_string(index=False)

    return ""


# ── Collect triplets ─────────────────────────────────────────
def _collect_triplets(index: KnowledgeGraphIndex):
    triplets_map = index.storage_context.graph_store.get_rel_map(
        subjs=None, depth=1, limit=100000
    )

    entities = {}
    relations = []
    seen = set()

    for subject, pairs in triplets_map.items():
        subject = subject.strip()

        if not subject:
            continue

        entities.setdefault(subject, "Entity")

        for pair in pairs:
            if len(pair) < 2:
                continue

            rel = pair[0].strip().replace(" ", "_").upper()
            obj = pair[1].strip()

            if not obj:
                continue

            entities.setdefault(obj, "Entity")

            if subject != obj:
                key = (subject, rel, obj)

                if key not in seen:
                    seen.add(key)

                    relations.append({
                        "source": subject,
                        "relation": rel,
                        "target": obj
                    })

    return entities, relations


# ── Build KG ────────────────────────────────────────────────
def build_knowledge_graph(
    file,
    file_type: str,
    max_triplets_per_chunk: int = 30,
    progress_callback=None,
):
    _build_settings()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / f"file.{file_type}"

        file.seek(0)
        path.write_bytes(file.read())

        if progress_callback:
            progress_callback("Loading document...")

        documents = SimpleDirectoryReader(tmpdir).load_data()

        graph_store = SimpleGraphStore()
        storage_context = StorageContext.from_defaults(graph_store=graph_store)

        index = KnowledgeGraphIndex.from_documents(
            documents,
            storage_context=storage_context,
            max_triplets_per_chunk=max_triplets_per_chunk,
            include_embeddings=False,
            kg_triple_extract_template=KG_EXTRACT_PROMPT,
        )

        INDEX_PERSIST_DIR.mkdir(exist_ok=True)
        index.storage_context.persist(persist_dir=str(INDEX_PERSIST_DIR))

        if progress_callback:
            progress_callback("Extracting triplets...")

        entities, relations = _collect_triplets(index)

    return {
        "entities": entities,
        "relations": relations,
        "batch_count": len(documents),
    }


# ── Query graph ─────────────────────────────────────────────
def query_graph(question: str):
    if not INDEX_PERSIST_DIR.exists():
        return {"answer": "No index found", "triplets": []}

    _build_settings()

    graph_store = SimpleGraphStore.from_persist_dir(str(INDEX_PERSIST_DIR))
    storage_context = StorageContext.from_defaults(
        graph_store=graph_store,
        persist_dir=str(INDEX_PERSIST_DIR),
    )

    index = load_index_from_storage(storage_context)

    engine = index.as_query_engine()

    response = engine.query(question)

    triplets = []

    for node in response.source_nodes:
        kg_map = node.node.metadata.get("kg_rel_map", {})

        for s, pairs in kg_map.items():
            for pair in pairs:
                if len(pair) >= 2:
                    triplets.append((s, pair[0], pair[1]))

    return {"answer": str(response), "triplets": triplets}


def index_exists() -> bool:
    return INDEX_PERSIST_DIR.exists() and any(INDEX_PERSIST_DIR.iterdir())