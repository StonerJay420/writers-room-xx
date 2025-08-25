# Overview

Writers Room X is a multi-agent AI system designed to assist authors and editors with manuscript editing and review. The system ingests novel manuscripts and codex files, processes them through specialized AI agents (Lore Archivist and Grim Editor), and generates ranked patch suggestions for improving scenes. The application provides a side-by-side comparison interface for reviewing original text versus AI-generated improvements, with detailed metrics analysis and canon consistency checking.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
The backend is built using **FastAPI** with a modular service-oriented architecture. The main application (`main.py`) serves as the entry point, coordinating three primary router modules:
- **Ingest Router**: Handles file uploading and indexing of manuscript/codex content
- **Scenes Router**: Manages scene retrieval and listing operations
- **Patches Router**: Orchestrates AI agent passes and patch generation

## Database Design
The system uses **SQLite** as the primary database with **SQLAlchemy** ORM for data persistence. Key entities include:
- **Scenes**: Store manuscript scenes with metadata (chapter, POV, location, beats, character links)
- **Characters**: Maintain character profiles with voice tags, preferred/banned words, and arc flags
- **Jobs**: Track AI agent processing status and results
- **Patches**: Store generated editing suggestions and variants

## AI Service Integration
The system integrates with **OpenAI's GPT models** (currently configured for GPT-5) through a dedicated AI service layer. Two primary agents are implemented:
- **Lore Archivist**: Performs RAG-based consistency checking against codex content
- **Grim Editor**: Provides line-by-line editing suggestions for prose improvement

## File Processing Pipeline
Files are processed through a structured pipeline:
1. **Discovery**: Scans manuscript and codex directories for Markdown files
2. **Parsing**: Extracts scene metadata from file paths and content structure
3. **Indexing**: Stores content in database with relationships and metadata
4. **Analysis**: Builds character/location registries for lore consistency checking

## Metrics and Analysis
The system provides comprehensive text analysis through a dedicated metrics service:
- **Readability scores** (Flesch Reading Ease, Flesch-Kincaid Grade)
- **Structural metrics** (sentence length, word count, syllable analysis)
- **Content analysis** (dialogue proportion, active voice estimation)
- **Target comparison** against predefined editorial standards

## Frontend Architecture
The frontend is built with **Next.js 14** and **TypeScript**, featuring:
- **Responsive design** using Tailwind CSS
- **Component-based architecture** with reusable UI elements
- **API proxy configuration** routing frontend requests to backend
- **Real-time diff viewing** for comparing original and edited text

## Diff and Patch System
Text modifications are handled through a sophisticated diff service:
- **Unified diff generation** for version control integration
- **Suggestion application** with fuzzy line matching
- **Multi-variant support** (safe, bold, red-team editing approaches)
- **Rollback capabilities** for undoing changes

# External Dependencies

## AI Services
- **OpenAI API**: Primary language model provider for text analysis and generation
- **GPT-5**: Latest model used for all AI agent operations

## Text Analysis Libraries
- **textstat**: Readability and text complexity metrics
- **NLTK**: Natural language processing utilities
- **spaCy**: Advanced text processing and entity recognition
- **scikit-learn**: Machine learning utilities for text analysis

## Database and Storage
- **SQLite**: Primary database for development and small deployments
- **SQLAlchemy**: ORM and database abstraction layer
- **pgvector**: Vector similarity search capabilities (prepared for PostgreSQL scaling)

## Web Framework Dependencies
- **FastAPI**: High-performance Python web framework
- **Uvicorn**: ASGI server for running the FastAPI application
- **Pydantic**: Data validation and settings management

## Frontend Dependencies
- **Next.js**: React-based web application framework
- **TypeScript**: Static type checking for JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library for UI components
- **Axios**: HTTP client for API communication

## Development and Utilities
- **python-dotenv**: Environment variable management
- **GitPython**: Git repository interaction for version control
- **aiofiles**: Asynchronous file operations
- **rapidfuzz**: Fast string matching for text similarity