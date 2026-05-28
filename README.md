# Knowledge Graph Builder

Upload unstructured documents → extract entities & relationships via NLP → store as a graph in Neo4j → explore interactively.

## Stack
- **Frontend**: Streamlit
- **NLP**: spaCy (`en_core_web_sm`)
- **Graph DB**: Neo4j
- **Visualization**: PyVis + NetworkX

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download spaCy model
python -m spacy download en_core_web_sm

# 3. Start Neo4j (Docker quickstart)
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# 4. Run the app
streamlit run app.py
```

## Supported file types
| Format | Notes |
|--------|-------|
| `.txt` | Plain text |
| `.pdf` | Text-based PDFs |
| `.docx` | Word documents |
| `.csv`  | Tabular data (converted to text) |

## How it works
1. Text is extracted from the uploaded file.
2. spaCy NER identifies named entities (people, orgs, locations, dates, …).
3. Dependency parsing extracts subject → verb → object triples as edges.
4. Nodes and edges are stored in Neo4j via `MERGE` (idempotent).
5. PyVis renders an interactive force-directed graph in the browser.
