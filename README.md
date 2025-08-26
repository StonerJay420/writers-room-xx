# Writers Room X

A multi-agent AI system designed to assist authors and editors with manuscript editing and review. The system ingests novel manuscripts and codex files, processes them through specialized AI agents, and generates ranked patch suggestions for improving scenes with automatic codex referencing and consistency checking.

## Features

- **Multi-Agent AI System**: Specialized agents including Lore Archivist and Grim Editor
- **Automatic Codex Referencing**: AI recommendations automatically reference relevant world/character information
- **Codex Management**: Comprehensive system for characters, locations, and world-building items
- **Real-time Text Editor**: Side-by-side comparison interface with AI-powered suggestions
- **Consistency Checking**: RAG-based consistency checking against codex content
- **Mobile-Friendly**: Responsive design with touch-optimized interactions
- **Metrics Analysis**: Readability scores, structural metrics, and content analysis

## Architecture

### Backend (FastAPI)
- **API Endpoints**: Text recommendations, codex management, scene processing
- **AI Service Integration**: OpenRouter/OpenAI GPT models with BYOK (Bring Your Own Key)
- **Database**: PostgreSQL with vector search capabilities
- **Background Processing**: Redis queue for long-running AI tasks

### Frontend (Next.js)
- **React Components**: Text editor, codex manager, manuscript navigator
- **TypeScript**: Full type safety across the application
- **Tailwind CSS**: Modern responsive design system
- **API Integration**: Axios-based API client with authentication

## Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.11+
- PostgreSQL database
- Redis (for background tasks)
- OpenRouter API key (for AI features)

### Development Setup

1. **Clone and Install Dependencies**
   ```bash
   # Frontend dependencies are automatically managed
   cd frontend
   npm install
   
   # Backend dependencies are automatically managed in the Replit environment
   ```

2. **Environment Configuration**
   ```bash
   # Set up your OpenRouter API key in the application settings
   # Database and Redis are automatically configured in Replit
   ```

3. **Database Setup**
   ```bash
   # Database migrations run automatically on startup
   # PostgreSQL with pgvector extension is pre-configured
   ```

## Run Commands

### Development Mode

**Start Full Application (Recommended)**
```bash
# Both frontend and backend start automatically in Replit
# Frontend: http://localhost:5000
# Backend API: http://localhost:8000
```

**Frontend Only**
```bash
cd frontend
npm run dev
# Starts on http://localhost:5000
```

**Backend Only**
```bash
cd api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Starts on http://localhost:8000
```

### Production Build

**Frontend Production Build**
```bash
cd frontend
npm run build
npm run start
```

**Backend Production**
```bash
cd api
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

When running, visit:
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Frontend**: http://localhost:5000

## Key Dependencies

### Backend (Python)
- **FastAPI**: High-performance web framework
- **OpenAI**: AI model integration
- **SQLAlchemy**: Database ORM
- **ChromaDB**: Vector database for embeddings
- **TextStat**: Text analysis and readability metrics
- **Pydantic**: Data validation and settings management

### Frontend (TypeScript/React)
- **Next.js 14**: React framework with app router
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library
- **Axios**: HTTP client for API communication
- **React Diff Viewer**: Text comparison interface

## Project Structure

```
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── agents/        # AI agents
│   │   └── models.py      # Database models
│   └── requirements.txt   # Python dependencies
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── app/          # Next.js app router
│   │   └── lib/          # Utilities and API client
│   └── package.json      # Node dependencies
├── data/
│   ├── codex/            # Character and world files
│   └── manuscript/       # Story content
└── docker/               # Container configurations
```

## Usage

### Setting Up AI Features

1. **Configure OpenRouter API Key**
   - Click "Configure OpenRouter Key" in the application
   - Enter your OpenRouter API key
   - This enables AI recommendations and codex analysis

2. **Create Codex Entries**
   - Use the Codex Manager to add characters, locations, and world rules
   - These will automatically be referenced in AI recommendations

3. **Get AI Recommendations**
   - Write text in the editor
   - Click "Get AI Suggestions" for improvements
   - View automatic codex references and consistency checks

### AI Agents

- **Lore Archivist**: Maintains consistency with story codex
- **Grim Editor**: Provides line-by-line prose improvements
- **Tone & Metrics**: Analyzes text for readability and style

## Development

### Adding New Features

1. **Backend**: Add routes in `api/app/routers/`
2. **Frontend**: Add components in `frontend/src/components/`
3. **AI Agents**: Extend agents in `api/app/agents/`

### Testing

```bash
# Backend tests
cd api
python -m pytest

# Frontend linting
cd frontend
npm run lint
```

## Configuration

- **Agent Settings**: Configure AI models and parameters in the UI
- **Metrics Targets**: Customize readability and style targets
- **Database**: PostgreSQL with automatic migrations
- **File Storage**: Local file system for codex and manuscripts

## Troubleshooting

### Common Issues

1. **AI Recommendations Not Working**
   - Ensure OpenRouter API key is configured
   - Check API key validity in settings

2. **Database Connection Issues**
   - Database is automatically configured in Replit
   - Check logs for migration errors

3. **Frontend Build Errors**
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall: `rm -rf node_modules && npm install`

### Logs

- **Backend Logs**: Check console output or `api/logs/`
- **Frontend Logs**: Check browser console
- **Database**: Check migration logs on startup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is proprietary software for manuscript editing and AI-assisted writing.