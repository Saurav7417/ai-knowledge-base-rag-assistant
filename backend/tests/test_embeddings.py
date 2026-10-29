import numpy as np
from app.rag.embeddings import DeterministicMockEmbeddingProvider


def test_embedding_dimension_and_norm():
    provider = DeterministicMockEmbeddingProvider(dimension=1536)
    vec = provider.embed_query("Disaster recovery and high availability")

    assert len(vec) == 1536
    norm = np.linalg.norm(np.array(vec))
    assert np.isclose(norm, 1.0, atol=1e-4)


def test_embedding_deterministic():
    provider = DeterministicMockEmbeddingProvider()
    v1 = provider.embed_query("Kubernetes pod autoscaling policy")
    v2 = provider.embed_query("Kubernetes pod autoscaling policy")

    assert v1 == v2


def test_semantic_similarity_separation():
    provider = DeterministicMockEmbeddingProvider()
    q_vec = np.array(provider.embed_query("database connection pool timeout"))
    rel_vec = np.array(provider.embed_query("database pgbouncer connections and timeout limits"))
    unrel_vec = np.array(provider.embed_query("astronomy black holes and galactic nebulae"))

    sim_rel = np.dot(q_vec, rel_vec)
    sim_unrel = np.dot(q_vec, unrel_vec)

    assert sim_rel > sim_unrel
    assert sim_rel > 0.15
