import React, { useState, useRef, useEffect } from "react";
import type { KnowledgeBase, MessageItem, CitationItem, RAGQueryResponse } from "../types";
import { api } from "../api/client";
import { RetrievalDebugger } from "./RetrievalDebugger";
import {
  Send,
  Bot,
  User as UserIcon,
  Sparkles,
  AlertTriangle,
  RotateCcw,
  BookOpen,
  Filter,
  CheckCircle2
} from "lucide-react";

interface ChatPanelProps {
  currentKb: KnowledgeBase | null;
  selectedDocIds: string[];
  conversationId: string | null;
  onSelectCitation: (citation: CitationItem) => void;
  onClearChat: () => void;
  ragSettings: {
    topK: number;
    similarityThreshold: number;
    rerank: boolean;
  };
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  currentKb,
  selectedDocIds,
  conversationId,
  onSelectCitation,
  onClearChat,
  ragSettings
}) => {
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load existing conversation messages if conversationId changes
  useEffect(() => {
    if (conversationId) {
      api.getConversation(conversationId).then(conv => {
        if (conv?.messages) {
          setMessages(conv.messages);
        }
      }).catch(console.error);
    } else {
      setMessages([]);
    }
  }, [conversationId]);

  if (!currentKb) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400 bg-slate-50">
        <Sparkles className="w-12 h-12 text-slate-300 mb-3" />
        <h3 className="text-base font-medium text-slate-600">Grounded Research Assistant</h3>
        <p className="text-xs text-slate-400 max-w-sm mt-1">
          Select a knowledge base to begin asking questions with verified citations and source grounding.
        </p>
      </div>
    );
  }

  const handleSend = async (queryText?: string) => {
    const q = (queryText || inputQuery).trim();
    if (!q || loading) return;

    const userMessage: MessageItem = {
      id: "temp-user-" + Date.now(),
      conversation_id: conversationId || "",
      role: "user",
      content: q,
      is_abstained: false,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputQuery("");
    setLoading(true);

    try {
      const resp: RAGQueryResponse = await api.chatRAG(
        currentKb.id,
        q,
        conversationId || undefined,
        {
          documentIds: selectedDocIds.length > 0 ? selectedDocIds : undefined,
          topK: ragSettings.topK,
          similarityThreshold: ragSettings.similarityThreshold,
          rerank: ragSettings.rerank
        }
      );

      const assistantMessage: MessageItem = {
        id: resp.message_id || "temp-asst-" + Date.now(),
        conversation_id: resp.conversation_id || conversationId || "",
        role: "assistant",
        content: resp.answer,
        is_abstained: resp.is_abstained,
        citations: resp.citations,
        retrieval_debug_info: {
          retrieved_chunks: resp.retrieved_chunks,
          metrics: resp.metrics,
          abstention_reason: resp.abstention_reason
        },
        created_at: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: MessageItem = {
        id: "error-" + Date.now(),
        conversation_id: conversationId || "",
        role: "assistant",
        content: `Error generating research answer: ${err.message || "Failed to query RAG pipeline."}`,
        is_abstained: true,
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderFormattedAnswer = (text: string, citations?: CitationItem[]) => {
    // Regex matches inline citation badges **[DocumentName, p.X]**
    const parts = text.split(/(\*\*\[[^\]]+\]\*\*)/g);

    return parts.map((part, i) => {
      const match = part.match(/\*\*\[(.*?), p\.(\d+)\]\*\*/);
      if (match) {
        const docName = match[1];
        const pageNum = parseInt(match[2], 10);
        const matchingCit = citations?.find(
          c => c.document_name === docName && c.page_number === pageNum
        );

        return (
          <button
            key={i}
            onClick={() => matchingCit && onSelectCitation(matchingCit)}
            className="inline-flex items-center gap-1 mx-1 px-1.5 py-0.5 rounded bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-medium cursor-pointer transition-colors"
            title="Click to view verified source excerpt"
          >
            <BookOpen className="w-3 h-3 text-indigo-500" />
            <span>{docName}, p.{pageNum}</span>
          </button>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Header Bar */}
      <div className="px-6 py-3 bg-white border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs">
          <span className="font-semibold text-slate-800">Research Session:</span>
          <span className="text-slate-600 font-medium truncate max-w-xs">{currentKb.name}</span>
          {selectedDocIds.length > 0 ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[10px] font-medium border border-indigo-200">
              <Filter className="w-3 h-3" /> Scoped to {selectedDocIds.length} doc(s)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px] font-medium">
              Scoped to entire knowledge base
            </span>
          )}
        </div>

        {messages.length > 0 && (
          <button
            onClick={() => {
              if (window.confirm("Clear research chat history?")) {
                setMessages([]);
                onClearChat();
              }
            }}
            className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 px-2.5 py-1 rounded-md hover:bg-slate-100 transition-colors"
            title="Clear Chat"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="max-w-xl mx-auto py-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600 text-white flex items-center justify-center mx-auto mb-4 shadow-lg shadow-indigo-500/20">
              <Bot className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-800">
              Ask questions about your uploaded documents
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto leading-relaxed">
              Every substantive answer is strictly grounded in the retrieved passages with direct inline citations.
              If the documents do not contain evidence, the assistant will abstain.
            </p>

            {/* Example Queries */}
            <div className="mt-8 space-y-2 text-left">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 text-center">
                Try asking:
              </p>
              <div className="grid grid-cols-1 gap-2 max-w-md mx-auto">
                {[
                  "What is the acceptable Recovery Time Objective (RTO)?",
                  "How long must audit logs be retained according to our documentation?",
                  "What is the password hashing requirement and work factor?",
                  "Which consensus protocol is employed for coordination?"
                ].map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(prompt)}
                    className="p-3 text-left rounded-lg bg-white border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/20 text-xs text-slate-700 transition-colors shadow-2xs"
                  >
                    &ldquo;{prompt}&rdquo;
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((m) => {
            const isUser = m.role === "user";

            return (
              <div
                key={m.id}
                className={`flex gap-3 max-w-3xl ${isUser ? "ml-auto" : "mr-auto"}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`space-y-2 ${isUser ? "items-end" : "items-start"} max-w-2xl`}>
                  <div
                    className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed shadow-xs ${
                      isUser
                        ? "bg-indigo-600 text-white rounded-br-xs"
                        : "bg-white text-slate-800 border border-slate-200 rounded-tl-xs"
                    }`}
                  >
                    {isUser ? (
                      <p className="whitespace-pre-wrap">{m.content}</p>
                    ) : (
                      <>
                        {/* Abstention Banner */}
                        {m.is_abstained && (
                          <div className="mb-3 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
                            <span>
                              <strong>Abstention Notice:</strong> Insufficient evidence in uploaded documents.
                            </span>
                          </div>
                        )}

                        <div className="whitespace-pre-wrap text-slate-800">
                          {renderFormattedAnswer(m.content, m.citations)}
                        </div>

                        {/* Verified Citations List */}
                        {m.citations && m.citations.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-slate-100">
                            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Verified Citations ({m.citations.length})
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {m.citations.map((c, i) => (
                                <button
                                  key={c.chunk_id || i}
                                  onClick={() => onSelectCitation(c)}
                                  className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-[11px] text-slate-700 border border-slate-200 transition-colors"
                                  title="View source passage"
                                >
                                  <BookOpen className="w-3 h-3 text-slate-400" />
                                  <span>{c.document_name} &bull; Page {c.page_number}</span>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* RAG Telemetry & Debugger Accordion */}
                        {m.retrieval_debug_info?.retrieved_chunks && (
                          <RetrievalDebugger
                            chunks={m.retrieval_debug_info.retrieved_chunks}
                            metrics={m.retrieval_debug_info.metrics}
                            abstentionReason={m.retrieval_debug_info.abstention_reason}
                          />
                        )}
                      </>
                    )}
                  </div>
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-lg bg-slate-800 text-white flex items-center justify-center shrink-0 shadow-xs">
                    <UserIcon className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {loading && (
          <div className="flex items-center gap-3 mr-auto max-w-xl">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-xs text-xs text-slate-500 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
              <span>Retrieving candidate passages & verifying citations...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-4 bg-white border-t border-slate-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative max-w-3xl mx-auto"
        >
          <textarea
            rows={2}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder="Ask a question grounded in your documents... (Press Enter to send)"
            className="w-full pl-4 pr-12 py-3 bg-slate-50 border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-hidden focus:border-indigo-500 focus:bg-white resize-none shadow-xs"
          />
          <button
            type="submit"
            disabled={loading || !inputQuery.trim()}
            className={`absolute right-3 bottom-5 p-2 rounded-lg transition-colors ${
              !inputQuery.trim() || loading
                ? "text-slate-300 bg-slate-100 cursor-not-allowed"
                : "text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-500/20"
            }`}
            title="Send query"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="text-[11px] text-center text-slate-400 mt-2">
          Responses are strictly grounded in retrieved evidence passages with deterministic citation validation.
        </p>
      </div>
    </div>
  );
};
