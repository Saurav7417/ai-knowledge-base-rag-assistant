import React, { useState, useEffect } from "react";
import type { KnowledgeBase, DocumentItem, CitationItem } from "./types";
import { api } from "./api/client";
import { useAuth } from "./context/AuthContext";
import { KnowledgeBaseSidebar } from "./components/KnowledgeBaseSidebar";
import { DocumentManager } from "./components/DocumentManager";
import { ChatPanel } from "./components/ChatPanel";
import { CitationModal } from "./components/CitationModal";
import { SettingsModal } from "./components/SettingsModal";
import { AuthModal } from "./components/AuthModal";

export const AppContent: React.FC = () => {
  const { user, loading: authLoading } = useAuth();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [currentKb, setCurrentKb] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<CitationItem | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // RAG Hyperparameters
  const [ragSettings, setRagSettings] = useState({
    topK: 5,
    similarityThreshold: 0.10,
    rerank: true
  });

  // Fetch Knowledge Bases on user login
  const fetchKnowledgeBases = async () => {
    try {
      const kbs = await api.getKnowledgeBases();
      setKnowledgeBases(kbs);
      if (kbs.length > 0 && !currentKb) {
        setCurrentKb(kbs[0]);
      } else if (currentKb) {
        // Refresh current KB
        const updated = kbs.find(k => k.id === currentKb.id);
        if (updated) setCurrentKb(updated);
      }
    } catch (err) {
      console.error("Failed to load knowledge bases:", err);
    }
  };

  // Fetch documents for the active KB
  const fetchDocuments = async (kbId: string) => {
    try {
      const docs = await api.getDocuments(kbId);
      setDocuments(docs);
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
  };

  useEffect(() => {
    if (user) {
      fetchKnowledgeBases();
    } else {
      setKnowledgeBases([]);
      setCurrentKb(null);
      setDocuments([]);
      setSelectedDocIds([]);
      setConversationId(null);
    }
  }, [user]);

  useEffect(() => {
    if (currentKb) {
      fetchDocuments(currentKb.id);
      setSelectedDocIds([]);
      setConversationId(null);
    } else {
      setDocuments([]);
    }
  }, [currentKb?.id]);

  const handleCreateKb = async (name: string, desc?: string) => {
    const created = await api.createKnowledgeBase(name, desc);
    await fetchKnowledgeBases();
    setCurrentKb(created);
  };

  const handleUpdateKb = async (id: string, name: string, desc?: string) => {
    await api.updateKnowledgeBase(id, name, desc);
    await fetchKnowledgeBases();
  };

  const handleDeleteKb = async (id: string) => {
    await api.deleteKnowledgeBase(id);
    const remaining = knowledgeBases.filter(k => k.id !== id);
    setKnowledgeBases(remaining);
    setCurrentKb(remaining.length > 0 ? remaining[0] : null);
  };

  const handleToggleSelectDoc = (docId: string) => {
    setSelectedDocIds(prev =>
      prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]
    );
  };

  if (authLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-900 text-white">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400 font-mono">Initializing research environment...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-slate-50 font-sans">
      {/* Auth Screen Modal if user not logged in */}
      <AuthModal isOpen={!user} />

      {/* 1. Left Sidebar: Knowledge Bases */}
      <KnowledgeBaseSidebar
        knowledgeBases={knowledgeBases}
        currentKb={currentKb}
        onSelectKb={(kb) => setCurrentKb(kb)}
        onCreateKb={handleCreateKb}
        onUpdateKb={handleUpdateKb}
        onDeleteKb={handleDeleteKb}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* 2. Middle Panel: Document Ingestion & Status Manager */}
      <div className="w-80 sm:w-96 shrink-0 h-full">
        <DocumentManager
          currentKb={currentKb}
          documents={documents}
          selectedDocIds={selectedDocIds}
          onToggleSelectDoc={handleToggleSelectDoc}
          onSelectAllDocs={(ids) => setSelectedDocIds(ids)}
          onRefreshDocs={() => {
            if (currentKb) {
              fetchDocuments(currentKb.id);
              fetchKnowledgeBases();
            }
          }}
        />
      </div>

      {/* 3. Right Panel: Grounded Chat & Research Q&A */}
      <ChatPanel
        currentKb={currentKb}
        selectedDocIds={selectedDocIds}
        conversationId={conversationId}
        onSelectCitation={(cit) => setActiveCitation(cit)}
        onClearChat={() => setConversationId(null)}
        ragSettings={ragSettings}
      />

      {/* Citation Inspector Side-Modal */}
      <CitationModal
        citation={activeCitation}
        onClose={() => setActiveCitation(null)}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={ragSettings}
        onSave={(newSet) => setRagSettings(newSet)}
      />
    </div>
  );
};

export default function App() {
  return <AppContent />;
}
