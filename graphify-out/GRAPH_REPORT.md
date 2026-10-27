# Graph Report - agrivibe  (2026-10-27)

## Corpus Check
- Corpus is ~1,209 words - fits in a single context window. You may not need a graph.

## Summary
- 97 nodes · 164 edges · 14 communities (5 shown, 9 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 13 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- FieldOracle Agent & Schemas
- Search Tool & Vector Store
- HTTP Routes
- Knowledge Service & Models
- Settings & Dependency Wiring
- PDF Reading & Chunk IDs
- Package Root

## God Nodes (most connected - your core abstractions)
1. `Settings` - 10 edges
2. `KnowledgeService` - 10 edges
3. `search_chunks()` - 9 edges
4. `index_document()` - 7 edges
5. `IndexResponse` - 7 edges
6. `SearchResponse` - 7 edges
7. `make_search_tool()` - 6 edges
8. `search()` - 6 edges
9. `create_vector_store()` - 6 edges
10. `get_knowledge_service()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `index_document()` --uses--> `IndexResponse`  [INFERRED]
  src/agrivibe/api/knowledge.py → src/agrivibe/models/knowledge.py
- `search()` --uses--> `SearchRequest`  [INFERRED]
  src/agrivibe/api/knowledge.py → src/agrivibe/models/knowledge.py
- `search()` --uses--> `SearchResponse`  [INFERRED]
  src/agrivibe/api/knowledge.py → src/agrivibe/models/knowledge.py
- `create_chat_model()` --uses--> `Settings`  [INFERRED]
  src/agrivibe/core/llm.py → src/agrivibe/config.py
- `get_knowledge_service()` --uses--> `KnowledgeService`  [INFERRED]
  src/agrivibe/dependencies.py → src/agrivibe/service/knowledge.py

## Import Cycles
- None detected.

## Communities (14 total, 9 thin omitted)

### Community 0 - "FieldOracle Agent & Schemas"
Cohesion: 0.14
Nodes (4): build_fieldoracle_agent(), CitedAnswer, CitedSentence, create_chat_model()

### Community 1 - "Search Tool & Vector Store"
Cohesion: 0.15
Nodes (4): format_passages(), make_search_tool(), search_knowledge(), search_chunks()

### Community 2 - "HTTP Routes"
Cohesion: 0.16
Nodes (3): index_document(), search(), health()

### Community 3 - "Knowledge Service & Models"
Cohesion: 0.28
Nodes (6): IndexResponse, SearchHit, SearchRequest, SearchResponse, Source, KnowledgeService

### Community 4 - "Settings & Dependency Wiring"
Cohesion: 0.31
Nodes (5): Settings, create_vector_store(), get_knowledge_service(), get_settings(), get_vector_store()

## Knowledge Gaps
- **1 isolated node(s):** `agrivibe`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 45 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `search_chunks()` connect `Search Tool & Vector Store` to `Knowledge Service & Models`, `PDF Reading & Chunk IDs`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Settings` (e.g. with `create_chat_model()` and `create_vector_store()`) actually correct?**
  _`Settings` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `agrivibe` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `FieldOracle Agent & Schemas` be split into smaller, more focused modules?**
  _Cohesion score 0.1368421052631579 - nodes in this community are weakly interconnected._
- **Why does `index_document()` connect `HTTP Routes` to `Knowledge Service & Models`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `KnowledgeService` (e.g. with `get_knowledge_service()` and `IndexResponse`) actually correct?**
  _`KnowledgeService` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Why does `KnowledgeService` connect `Knowledge Service & Models` to `HTTP Routes`, `Settings & Dependency Wiring`, `PDF Reading & Chunk IDs`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._