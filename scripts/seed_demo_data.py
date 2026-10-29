"""
Seed script to populate the database with a pre-configured demo user,
sample knowledge base, and indexed synthetic documents for immediate testing.
"""

import os
import sys
import uuid

# Ensure backend root is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_path)

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.core.security import hash_password
from app.rag.pipeline import RAGPipeline


def seed():
    print("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    demo_email = "demo.researcher@antigravity.ai"
    demo_pass = "DemoPassword123!"

    print(f"\n1. Ensuring demo user '{demo_email}' exists...")
    user = db.execute(select(User).where(User.email == demo_email)).scalar_one_or_none()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=demo_email,
            hashed_password=hash_password(demo_pass),
            full_name="Demo AI Researcher"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"   Created user: {user.email} (Password: {demo_pass})")
    else:
        print(f"   User already exists: {user.email}")

    print("\n2. Ensuring demo Knowledge Base exists...")
    kb = db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.user_id == user.id,
            KnowledgeBase.name == "Production Engineering & Compliance"
        )
    ).scalar_one_or_none()

    if not kb:
        kb = KnowledgeBase(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="Production Engineering & Compliance",
            description="Production architecture handbooks, SOC2 compliance policies, and distributed systems specifications."
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        print(f"   Created Knowledge Base: '{kb.name}'")
    else:
        print(f"   Knowledge Base already exists: '{kb.name}'")

    print("\n3. Indexing synthetic research documents...")
    docs_dir = os.path.join(backend_path, "evaluation", "synthetic_docs")
    sample_files = [
        "cloud_architecture_handbook.md",
        "security_compliance_policy.md",
        "distributed_systems_guide.txt",
        "conflicting_retention_policy.md"
    ]

    pipeline = RAGPipeline(db=db)

    for filename in sample_files:
        filepath = os.path.join(docs_dir, filename)
        if not os.path.exists(filepath):
            continue

        existing_doc = db.execute(
            select(Document).where(
                Document.kb_id == kb.id,
                Document.filename == filename
            )
        ).scalar_one_or_none()

        if existing_doc:
            print(f"   Document '{filename}' already indexed ({existing_doc.chunk_count} chunks).")
            continue

        file_size = os.path.getsize(filepath)
        ext = os.path.splitext(filename)[1].replace(".", "")

        doc = Document(
            id=str(uuid.uuid4()),
            kb_id=kb.id,
            user_id=user.id,
            filename=filename,
            file_type=ext,
            file_size_bytes=file_size,
            file_path=filepath
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        pipeline.ingest_document(doc.id)
        print(f"   Indexed '{filename}' -> {doc.chunk_count} chunks, {doc.total_pages} page(s).")

    db.close()
    print("\nDemo dataset seeding completed successfully!")
    print(f"Login credentials:\n  Email:    {demo_email}\n  Password: {demo_pass}\n")


if __name__ == "__main__":
    seed()
