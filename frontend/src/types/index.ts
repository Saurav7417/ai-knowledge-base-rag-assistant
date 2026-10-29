export interface User {
  id: string;
  email: string;
  full_name?: string;
  created_at: string;
}

export interface KnowledgeBase {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  document_count: number;
}

export type DocumentStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface DocumentItem {
  id: string;
  kb_id: string;
  user_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  processing_status: DocumentStatus;
  error_message?: string;
  total_pages: number;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  page_number: number;
  char_start: number;
  char_end: number;
  metadata_json: Record<string, any>;
}

export interface CitationItem {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  excerpt: string;
  similarity_score: number;
}

export interface RetrievedChunkDebug {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  content: string;
  similarity_score: number;
  rerank_score?: number;
  passed_threshold: boolean;
}

export interface RAGMetrics {
  retrieval_time_ms?: number;
  generation_time_ms?: number;
  total_time_ms?: number;
  retrieved_count?: number;
  passed_threshold_count?: number;
  valid_citations_count?: number;
  hallucinated_citations_stripped?: number;
}

export interface RAGQueryResponse {
  answer: string;
  is_abstained: boolean;
  abstention_reason?: string;
  citations: CitationItem[];
  retrieved_chunks: RetrievedChunkDebug[];
  conversation_id?: string;
  message_id?: string;
  metrics: RAGMetrics;
}

export interface MessageItem {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  is_abstained: boolean;
  citations?: CitationItem[];
  retrieval_debug_info?: {
    retrieved_chunks?: RetrievedChunkDebug[];
    metrics?: RAGMetrics;
    abstention_reason?: string;
  };
  created_at: string;
}

export interface ConversationItem {
  id: string;
  user_id: string;
  kb_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: MessageItem[];
}
