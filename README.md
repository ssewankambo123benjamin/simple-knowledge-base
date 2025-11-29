# Knowledge Base

A semantic search application with document ingestion, chunking, embedding, and intelligent retrieval with reranking.

## Quick Start

```bash
# Install all dependencies
make install

# Start both frontend and backend
make dev
```

This launches:

- **Backend**: <http://localhost:8000> (FastAPI + LanceDB)
- **Frontend**: <http://localhost:5173> (React + Vite)
- **API Docs**: <http://localhost:8000/docs>

Press `Ctrl+C` to stop both services.

## Development Commands

```bash
make help       # Show all available commands
make dev        # Start both frontend and backend
make backend    # Start only backend
make frontend   # Start only frontend
make install    # Install all dependencies
make test       # Run backend tests
make lint       # Run linters
make clean      # Clean generated files
```

## Project Structure

```text
knowledge-base/
├── backend/          # FastAPI backend (Python 3.13)
│   ├── app/          # Application code
│   ├── tests/        # Test suite
│   └── README.md     # Backend documentation
├── frontend/         # React frontend (Vite + TypeScript)
├── scripts/          # Development scripts
│   ├── dev.sh        # Combined dev server
│   └── start-backend.sh
└── Makefile          # Development commands
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Vite, Cloudscape Design |
| Backend | FastAPI, Python 3.13 |
| Vector DB | LanceDB |
| Embeddings | Alibaba-NLP/gte-multilingual-base |
| Reranker | Alibaba-NLP/gte-multilingual-reranker-base |

## Documentation

- [Backend API Documentation](backend/README.md)
