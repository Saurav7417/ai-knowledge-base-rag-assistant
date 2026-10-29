import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base, engine, get_db, is_sqlite
from app.core.logging import get_logger
from app.api.v1 import api_v1_router
from app.rag.embeddings import get_embedding_provider
from app.rag.llm import get_llm_provider

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Initialize DB schema
    logger.info("Initializing database schema...")
    try:
        # If postgres, try creating vector extension
        if not is_sqlite:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("PostgreSQL pgvector extension verified.")
    except Exception as e:
        logger.warning(f"Could not initialize pgvector extension: {e}")

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    
    yield
    
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-grade, modular RAG (Retrieval-Augmented Generation) knowledge base and research assistant API. "
        "Features multi-tenant isolation, recursive chunking with page tracking, pgvector & SQLite-vector retrieval, "
        "indirect prompt injection defense, threshold-based abstention, conflict detection, and deterministic citation validation."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint providing DB connectivity, provider configuration, and vector storage mode."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    emb_provider = get_embedding_provider()
    llm_provider = get_llm_provider()

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": {
            "status": db_status,
            "engine": "sqlite" if is_sqlite else "postgresql",
            "url_masked": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "local_sqlite"
        },
        "rag": {
            "embedding_provider": emb_provider.__class__.__name__,
            "embedding_dimension": emb_provider.dimension,
            "llm_provider": llm_provider.__class__.__name__,
            "similarity_threshold": settings.SIMILARITY_THRESHOLD,
            "reranker_enabled": settings.RERANKER_ENABLED,
            "default_chunk_size": settings.DEFAULT_CHUNK_SIZE,
            "default_chunk_overlap": settings.DEFAULT_CHUNK_OVERLAP
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
