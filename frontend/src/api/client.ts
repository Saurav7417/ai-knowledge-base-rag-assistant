import type {
  KnowledgeBase,
  DocumentItem,
  DocumentChunk,
  RAGQueryResponse,
  ConversationItem,
  User
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem("rag_auth_token");
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem("rag_auth_token", token);
    } else {
      localStorage.removeItem("rag_auth_token");
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers = new Headers(options.headers || {});

    if (this.token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${this.token}`);
    }

    if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      this.setToken(null);
      window.dispatchEvent(new CustomEvent("auth-unauthorized"));
      throw new Error("Session expired. Please log in again.");
    }

    if (!response.ok) {
      let errorMsg = `Request failed (${response.status})`;
      try {
        const errJson = await response.json();
        errorMsg = errJson.detail || errorMsg;
      } catch (_) {}
      throw new Error(errorMsg);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // --- Auth ---
  async register(email: string, password: string, fullName?: string): Promise<{ access_token: string; user_id: string; email: string }> {
    const res = await this.request<{ access_token: string; user_id: string; email: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName })
    });
    this.setToken(res.access_token);
    return res;
  }

  async login(email: string, password: string): Promise<{ access_token: string; user_id: string; email: string }> {
    const res = await this.request<{ access_token: string; user_id: string; email: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  logout() {
    this.setToken(null);
  }

  // --- Knowledge Bases ---
  async getKnowledgeBases(): Promise<KnowledgeBase[]> {
    return this.request<KnowledgeBase[]>("/knowledge-bases/");
  }

  async createKnowledgeBase(name: string, description?: string): Promise<KnowledgeBase> {
    return this.request<KnowledgeBase>("/knowledge-bases/", {
      method: "POST",
      body: JSON.stringify({ name, description })
    });
  }

  async updateKnowledgeBase(id: string, name?: string, description?: string): Promise<KnowledgeBase> {
    return this.request<KnowledgeBase>(`/knowledge-bases/${id}`, {
      method: "PUT",
      body: JSON.stringify({ name, description })
    });
  }

  async deleteKnowledgeBase(id: string): Promise<void> {
    return this.request<void>(`/knowledge-bases/${id}`, {
      method: "DELETE"
    });
  }

  // --- Documents ---
  async getDocuments(kbId: string): Promise<DocumentItem[]> {
    return this.request<DocumentItem[]>(`/documents/?kb_id=${kbId}`);
  }

  async uploadDocument(kbId: string, file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append("kb_id", kbId);
    formData.append("file", file);

    return this.request<DocumentItem>("/documents/upload", {
      method: "POST",
      body: formData
    });
  }

  async getDocumentChunks(docId: string): Promise<DocumentChunk[]> {
    return this.request<DocumentChunk[]>(`/documents/${docId}/chunks`);
  }

  async deleteDocument(docId: string): Promise<void> {
    return this.request<void>(`/documents/${docId}`, {
      method: "DELETE"
    });
  }

  // --- RAG & Chat ---
  async queryRAG(
    kbId: string,
    query: string,
    options?: {
      documentIds?: string[];
      topK?: number;
      similarityThreshold?: number;
      rerank?: boolean;
    }
  ): Promise<RAGQueryResponse> {
    return this.request<RAGQueryResponse>("/rag/query", {
      method: "POST",
      body: JSON.stringify({
        kb_id: kbId,
        query,
        document_ids: options?.documentIds,
        top_k: options?.topK ?? 5,
        similarity_threshold: options?.similarityThreshold,
        rerank: options?.rerank ?? true
      })
    });
  }

  async chatRAG(
    kbId: string,
    query: string,
    conversationId?: string,
    options?: {
      documentIds?: string[];
      topK?: number;
      similarityThreshold?: number;
      rerank?: boolean;
    }
  ): Promise<RAGQueryResponse> {
    return this.request<RAGQueryResponse>("/rag/chat", {
      method: "POST",
      body: JSON.stringify({
        kb_id: kbId,
        query,
        conversation_id: conversationId,
        document_ids: options?.documentIds,
        top_k: options?.topK ?? 5,
        similarity_threshold: options?.similarityThreshold,
        rerank: options?.rerank ?? true
      })
    });
  }

  // --- Conversations ---
  async getConversations(kbId: string): Promise<ConversationItem[]> {
    return this.request<ConversationItem[]>(`/conversations/?kb_id=${kbId}`);
  }

  async getConversation(conversationId: string): Promise<ConversationItem> {
    return this.request<ConversationItem>(`/conversations/${conversationId}`);
  }

  async deleteConversation(conversationId: string): Promise<void> {
    return this.request<void>(`/conversations/${conversationId}`, {
      method: "DELETE"
    });
  }
}

export const api = new ApiClient();
