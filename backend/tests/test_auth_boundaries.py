def test_unauthenticated_request_rejected(client):
    resp = client.get("/api/v1/knowledge-bases/")
    assert resp.status_code == 401


def test_cross_tenant_kb_isolation(client, token_a, token_b):
    # User A creates a KB
    resp_a = client.post(
        "/api/v1/knowledge-bases/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "Alpha Secret KB", "description": "Private to Alpha"}
    )
    assert resp_a.status_code == 201
    kb_a_id = resp_a.json()["id"]

    # User B tries to view User A's KB
    resp_b_view = client.get(
        f"/api/v1/knowledge-bases/{kb_a_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert resp_b_view.status_code == 404

    # User B tries to delete User A's KB
    resp_b_delete = client.delete(
        f"/api/v1/knowledge-bases/{kb_a_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert resp_b_delete.status_code == 404


def test_cross_tenant_document_isolation(client, token_a, token_b):
    # User A creates a KB
    kb_res = client.post(
        "/api/v1/knowledge-bases/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "Alpha KB", "description": "Docs"}
    )
    kb_id = kb_res.json()["id"]

    # User A uploads a document
    file_content = b"Confidential financial statement for Alpha Corporation."
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        data={"kb_id": kb_id},
        files={"file": ("alpha_financials.txt", file_content, "text/plain")}
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # User B tries to inspect User A's document chunks
    resp_b = client.get(
        f"/api/v1/documents/{doc_id}/chunks",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert resp_b.status_code == 404

    # User B tries to delete User A's document
    del_res = client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert del_res.status_code == 404
