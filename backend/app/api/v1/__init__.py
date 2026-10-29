from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.knowledge_bases import router as kb_router
from app.api.v1.documents import router as doc_router
from app.api.v1.rag import router as rag_router
from app.api.v1.conversations import router as conv_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(kb_router)
api_v1_router.include_router(doc_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(conv_router)

__all__ = ["api_v1_router"]
