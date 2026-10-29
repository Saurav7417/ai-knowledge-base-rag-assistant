def test_end_to_end_rag_query_and_abstention(client, token_a):
    # 1. Create KB
    kb_res = client.post(
        "/api/v1/knowledge-bases/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "Engineering Specs", "description": "Tech Docs"}
    )
    assert kb_res.status_code == 201
    kb_id = kb_res.json()["id"]

    # 2. Upload and index document
    doc_text = (
        "# High Availability Specifications\n\n"
        "The production database failover target RTO is fixed at exactly 15 minutes.\n"
        "Automatic cross-region replication is active between us-east-1 and us-west-2."
    ).encode("utf-8")

    upload_res = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        data={"kb_id": kb_id},
        files={"file": ("specs.md", doc_text, "text/markdown")}
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    assert doc_data["processing_status"] == "COMPLETED"
    assert doc_data["chunk_count"] >= 1

    # 3. Query answerable question
    q_res = client.post(
        "/api/v1/rag/query",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "kb_id": kb_id,
            "query": "What is the failover target RTO?",
            "top_k": 3
        }
    )
    assert q_res.status_code == 200
    res_data = q_res.json()
    assert not res_data["is_abstained"]
    assert "15 minutes" in res_data["answer"]
    assert len(res_data["citations"]) >= 1
    assert res_data["citations"][0]["document_name"] == "specs.md"

    # 4. Query unanswerable question -> must abstain!
    unans_res = client.post(
        "/api/v1/rag/query",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "kb_id": kb_id,
            "query": "What is the corporate travel allowance per diem for international flights?",
            "top_k": 3
        }
    )
    assert unans_res.status_code == 200
    unans_data = unans_res.json()
    assert unans_data["is_abstained"]
    ans_low = unans_data["answer"].lower()
    assert "sufficient" in ans_low or "insufficient" in ans_low
    assert len(unans_data["citations"]) == 0
