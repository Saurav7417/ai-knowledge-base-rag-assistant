import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Knowledge Base & Research Assistant"
    API_V1_STR: str = "/api/v1"
    
    # Security & JWT
    SECRET_KEY: str = Field(default="dev-insecure-secret-key-change-in-production-rag-2026", validation_alias="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database
    # Default to SQLite for zero-setup local execution; use postgresql+psycopg:// for pgvector
    DATABASE_URL: str = Field(
        default="sqlite:///./knowledge_base.db",
        validation_alias="DATABASE_URL"
    )
    
    # RAG & Embeddings Configuration
    # Options: "openai", "deterministic_mock"
    EMBEDDING_PROVIDER: str = Field(default="deterministic_mock", validation_alias="EMBEDDING_PROVIDER")
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    
    # Options: "openai", "mock"
    LLM_PROVIDER: str = Field(default="mock", validation_alias="LLM_PROVIDER")
    LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    OPENAI_BASE_URL: str = Field(default="https://api.openai.com/v1", validation_alias="OPENAI_BASE_URL")
    
    # Chunking Defaults
    DEFAULT_CHUNK_SIZE: int = 600  # characters
    DEFAULT_CHUNK_OVERLAP: int = 120  # characters
    
    # Retrieval Defaults
    DEFAULT_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.10  # cosine similarity minimum score for abstention (calibrated for feature-hashing / mock; 0.40 for OpenAI)
    RERANKER_ENABLED: bool = True
    
    # Storage & Upload Limits
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".md", ".markdown"]
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
