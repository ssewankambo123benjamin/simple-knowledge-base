---
trigger: model_decision
---

# Simple Knowledge Base - Project Overview

## Architecture Summary

A local-first semantic knowledge base with:
- **Backend**: FastAPI + LanceDB + Python 3.13
- **Frontend**: React 19 + Cloudscape Design + TypeScript

## Backend (`backend/app/`)

| Module | Purpose |
|--------|---------|
| [main.py](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/backend/app/main.py:0:0-0:0) | FastAPI app, 8 REST endpoints, exception handlers |
| [models.py](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/backend/app/models.py:0:0-0:0) | Pydantic models + LanceDB [ChunkSchema](cci:2://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/backend/app/models.py:15:0-30:5) (768-dim vectors) |
| [services.py](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/backend/app/services.py:0:0-0:0) | [ModelManager](cci:2://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/backend/app/services.py:31:0-145:47) (embeddings/reranker) + [DocumentProcessor](cci:2://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/backend/app/services.py:152:0-307:24) |
| [database.py](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/backend/app/database.py:0:0-0:0) | [LanceDBManager](cci:2://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/backend/app/database.py:27:0-264:32) with multi-index support |
| [config.py](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/backend/app/config.py:0:0-0:0) | Settings with `KB_` env prefix |
| [exceptions.py](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/backend/app/exceptions.py:0:0-0:0) | Custom exceptions for indexes, documents, directories |

### Key Dependencies
- FastAPI, LanceDB 0.19.0, sentence-transformers, semchunk
- Embedding: `Alibaba-NLP/gte-multilingual-base` (768-dim)
- Reranker: `Alibaba-NLP/gte-multilingual-reranker-base`

### API Endpoints
- `POST /create` — Create index
- `GET /indexes` — List indexes
- `POST /upload_doc` — Upload & encode file
- `POST /encode_batch` — Batch process directory (async)
- `POST /query` — Semantic search with reranking

## Frontend (`frontend/src/`)

| Component | Purpose |
|-----------|---------|
| [App.tsx](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/frontend/src/App.tsx:0:0-0:0) | Main app with tabs, health monitoring, notifications |
| [SearchInterface.tsx](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/frontend/src/components/SearchInterface.tsx:0:0-0:0) | Search form with index selector |
| [SearchResults.tsx](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/frontend/src/components/SearchResults.tsx:0:0-0:0) | Results with relevance badges, progress bars |
| [AddKnowledge.tsx](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/frontend/src/components/AddKnowledge.tsx:0:0-0:0) | Index creation + document upload workflow |
| [IndexSelector.tsx](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/frontend/src/components/IndexSelector.tsx:0:0-0:0) | Reusable index dropdown with record counts |
| [api/client.ts](cci:7://file:///Users/praveenc/dev/ai-ml/projects/simple-knowledge-base/frontend/src/api/client.ts:0:0-0:0) | Typed API client functions |

### Key Dependencies
- React 19, Vite 7, TypeScript 5.9, Cloudscape Design 3.x

## Development Commands

```bash
make install    # Install all deps (uv + pnpm)
make dev        # Start both servers
make test       # Run pytest
make lint       # Run ruff + eslint
```