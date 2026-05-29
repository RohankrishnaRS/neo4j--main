# 🕸️ Knowledge Graph Builder (AI + Neo4j Desktop)

Upload unstructured documents → extract entities & relationships using LLM → build a knowledge graph → explore and query interactively.

---

## 🚀 Features
- 📄 Upload documents (PDF, DOCX, CSV, TXT)
- 🧠 AI-based entity & relationship extraction (LlamaIndex + Azure OpenAI)
- 🔗 Automatic knowledge graph creation (triplets)
- 🗄️ Graph storage using Neo4j Desktop
- 📊 Interactive visualization (PyVis)
- 💬 Ask questions over graph (Graph-based Q&A)
- 📈 Graph analytics (NetworkX)

---

## 🧰 Tech Stack
- Frontend: Streamlit  
- AI/NLP: LlamaIndex + Azure OpenAI  
- File Processing: PyPDF2, python-docx, pandas  
- Graph DB: Neo4j Desktop  
- Visualization: PyVis, NetworkX  
- Config: python-dotenv  

---

## ⚙️ Setup

1. Create & Activate Virtual Environment
python -m venv venv
venv\Scripts\activate

2. Install Dependencies
pip install -r requirements.txt

3. Configure Environment (.env)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=your-endpoin

4. Start Neo4j Desktop
Open Neo4j Desktop
Create a Local DBMS (Project)
Set username: neo4j and your password
Start the database

5. Run the App
python -m streamlit run app.py

🧠 How It Works

1.Extract text from uploaded file

2.LLM processes text (Azure OpenAI)

3.Extract entities & relationships

4.Convert into triplets:
(Subject, Relation, Object)

5.Store graph in Neo4j using MERGE

6.Visualize graph using PyVis

7.Query graph using natural language

🔍 Graph Exploration
View nodes & edges
Highlight connected nodes
Filter relationships
Analyze graph


💬 Ask the Graph
Ask:
Who is the CEO of Microsoft?

✔ Answer generated from structured graph

⚡ Highlights

Converts unstructured text → structured graph
Uses LLM instead of rule-based NLP
Graph-based Q&A (Graph RAG)
Interactive visualization


🚀 Future Improvements

Add Cypher query UI
Multi-document linking
Cloud deployment
Semantic graph search


📌 Author

Rohan krishna R S
