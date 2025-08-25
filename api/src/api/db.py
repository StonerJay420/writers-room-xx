"""Database configuration and session management."""
from sqlalchemy import create_engine, text, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import asyncio

from .config import settings


# Create database engines
if settings.database_url.startswith("sqlite"):
    # SQLite specific settings
    primary_engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool,
        echo=settings.debug
    )
else:
    # PostgreSQL settings
    primary_engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.debug
    )

# Create replica engine (falls back to primary if not configured)
if settings.replica_db_url:
    replica_engine = create_engine(
        settings.replica_db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.debug
    )
else:
    replica_engine = primary_engine

# Session factories
PrimarySessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=primary_engine
)

ReplicaSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=replica_engine
)

# Base class for models
Base = declarative_base()


def get_write_session() -> Generator[Session, None, None]:
    """Get a database session for write operations."""
    db = PrimarySessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_read_session() -> Generator[Session, None, None]:
    """Get a database session for read operations (uses replica if available)."""
    db = ReplicaSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Alias for backward compatibility
get_db = get_write_session


async def init_database():
    """Initialize database on startup."""
    try:
        # Create pgvector extension if using PostgreSQL
        if not settings.database_url.startswith("sqlite"):
            with primary_engine.connect() as conn:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
                    print("pgvector extension created/verified")
                except Exception as e:
                    print(f"Could not create pgvector extension: {e}")
        
        # Run migrations if auto_migrate is enabled
        if settings.auto_migrate:
            try:
                from alembic import command
                from alembic.config import Config
                
                alembic_cfg = Config("alembic.ini")
                command.upgrade(alembic_cfg, "head")
                print("Database migrations completed")
            except Exception as e:
                print(f"Could not run migrations: {e}")
                # Create tables directly if migrations fail
                Base.metadata.create_all(bind=primary_engine)
                print("Database tables created directly")
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise