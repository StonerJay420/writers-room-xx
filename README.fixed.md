# Writers Room XX

A multi-agent AI writing room for manuscript editing and enhancement.

## Overview

Writers Room XX is a sophisticated AI-powered writing assistant that uses multiple specialized agents to analyze, edit, and enhance manuscripts. The system includes:

- **Supervisor**: Orchestrates passes and agent routing
- **Lore Archivist**: RAG codex/manuscript retrieval with YAML front matter
- **Grim Editor**: Line edits with patch/diff output
- **Consistency Guardian**: Canon checks and contradiction flags
- **Metrics Engine**: Readability, verb dynamics, POS, emotion, and pacing analysis

## Architecture

The system consists of the following components:

- **FastAPI Backend**: Handles API requests, agent coordination, and database operations
- **ChromaDB**: Vector database for RAG (Retrieval Augmented Generation)
- **SQLite/PostgreSQL**: Relational database for structured data
- **Redis**: Job queue for background processing
- **Next.js Frontend**: User interface for manuscript management and editing

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- OpenRouter API key (for LLM functionality)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/StonerJay420/writers-room-xx.git
   cd writers-room-xx
   ```

2. Create a `.env` file with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenRouter API key and other settings
   ```

3. Start the development environment:
   ```bash
   make dev
   ```

4. Seed sample data:
   ```bash
   make seed-data
   ```

5. Access the UI at http://localhost:3000

## Development Setup

### Environment Variables

Key environment variables:

- `OPENROUTER_API_KEY`: Your OpenRouter API key (required for LLM functionality)
- `DATABASE_URL`: Database connection string (default: `sqlite:///data/app.db`)
- `CHROMA_HOST`: ChromaDB host (default: `chroma`)
- `CHROMA_PORT`: ChromaDB port (default: `8000`)
- `REDIS_URL`: Redis connection string (default: `redis://redis:6379`)
- `DEBUG`: Enable debug mode (default: `false`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### API Development

To run the API locally:

```bash
cd api
pip install -r requirements.fixed.txt
uvicorn app.main:app --reload --port 8080
```

API documentation will be available at http://localhost:8080/docs

### Frontend Development

To run the frontend locally:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

## Testing

Run all tests:

```bash
make test
```

Or run specific test categories:

```bash
cd api
python -m pytest tests/test_rag.py -v
python -m pytest tests/test_metrics.py -v
python -m pytest tests/test_agents.py -v
```

## Docker Deployment

The system is containerized for easy deployment:

```bash
# Build containers
docker compose -f docker-compose.fixed.yml build

# Start services
docker compose -f docker-compose.fixed.yml up -d

# Check logs
docker compose -f docker-compose.fixed.yml logs -f
```

## Agent System

### Supervisor

The Supervisor agent orchestrates the editing process by:
- Planning which agents to run
- Routing tasks between agents
- Managing variants (safe, bold, experimental)
- Collecting and organizing results

### Lore Archivist

The Lore Archivist ensures consistency with established canon by:
- Retrieving relevant context from the codex
- Identifying potential contradictions
- Providing citations and receipts
- Suggesting corrections

### Grim Editor

The Grim Editor improves prose quality by:
- Enhancing clarity and precision
- Adjusting sentence structure and flow
- Maintaining the author's voice
- Providing a unified diff of changes

### Consistency Guardian

The Consistency Guardian checks for internal consistency by:
- Tracking character traits and descriptions
- Monitoring plot elements and timelines
- Flagging contradictions within the manuscript
- Ensuring continuity across scenes

### Metrics Engine

The Metrics Engine analyzes text quality by measuring:
- Readability scores (Flesch, Flesch-Kincaid, etc.)
- Sentence length and variation
- Part-of-speech distribution
- Active vs. passive voice ratio
- Emotional tone and pacing

## RAG Pipeline

The RAG (Retrieval Augmented Generation) pipeline enhances agent capabilities by:
1. Chunking documents into manageable segments
2. Generating embeddings for each chunk
3. Storing embeddings and metadata in ChromaDB
4. Retrieving relevant context based on semantic similarity
5. Providing agents with context for informed decisions

## Job Queue

Background processing is handled by a Redis-based job queue:
- Long-running tasks are processed asynchronously
- Jobs can be monitored and managed through the API
- Failed jobs are automatically retried with exponential backoff
- Results are stored and accessible through the API

## Contributing

1. Create a new branch for your changes
2. Make your changes and add tests
3. Run tests to ensure everything works
4. Submit a pull request

## License

[MIT License](LICENSE)