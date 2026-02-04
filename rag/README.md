# RAG

RAG Workflow

```
Document Upload
   ↓
[DocParser] Extract text, images, tables
   ↓
[Splitter] Text splitting
   ↓
[Embedding] Generate vector embeddings
   ↓
[Vector Store] Store vectors (Qdrant/Postgres/pgvector)
   ↓
[Full-text Index] Full-text indexing (Elasticsearch/ParadeDB)
   ↓
[KG Extraction] Knowledge graph extraction (optional Neo4j)
   ↓
Knowledge base indexing complete
```