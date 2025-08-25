# Writers Room X

Multi-agent AI manuscript editing system with canon consistency checking.

## Quick Start

### Docker Compose (Recommended)
```bash
# Copy environment variables
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env

# Start all services
docker compose up

# Access:
# - UI: http://localhost:3000
# - API: http://localhost:8080
# - Chroma: http://localhost:8000
```

### Local Development

#### Backend
```bash
cd api
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

#### Frontend
```bash
cd ui
npm install
npm run dev
```

## Project Structure
- `api/` - FastAPI backend with AI agents
- `ui/` - Next.js frontend with manuscript editor
- `artifacts/` - Generated patches and diffs (git-ignored)
- `data/` - SQLite database and local storage (git-ignored)
- `configs/` - Agent and metrics configurations

## Features
- Multi-agent processing (Lore Archivist, Grim Editor, Tone Metrics)
- Canon consistency validation with RAG
- Multiple patch variants (safe, bold, red-team)
- Unified diff generation and application
- Metrics analysis against ED targets