import React, { useState, useRef } from "react";
import type { DocumentItem, DocumentChunk, KnowledgeBase } from "../types";
import { api } from "../api/client";
import {
  UploadCloud,
  FileText,
  Trash2,
  Eye,
  CheckCircle,
  Clock,
  AlertCircle,
  X,
  Filter
} from "lucide-react";

interface DocumentManagerProps {
  currentKb: KnowledgeBase | null;
  documents: DocumentItem[];
  selectedDocIds: string[];
  onToggleSelectDoc: (docId: string) => void;
  onSelectAllDocs: (docIds: string[]) => void;
  onRefreshDocs: () => void;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({
  currentKb,
  documents,
  selectedDocIds,
  onToggleSelectDoc,
  onSelectAllDocs,
  onRefreshDocs
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [inspectingDoc, setInspectingDoc] = useState<DocumentItem | null>(null);
  const [docChunks, setDocChunks] = useState<DocumentChunk[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!currentKb) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center text-slate-400">
        <FileText className="w-12 h-12 mb-3 stroke-1" />
        <h3 className="text-base font-medium text-slate-600">No Knowledge Base Selected</h3>
        <p className="text-xs text-slate-400 max-w-sm mt-1">
          Select or create a knowledge base from the sidebar to manage documents and research papers.
        </p>
      </div>
    );
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);

    try {
      await api.uploadDocument(currentKb.id, file);
      onRefreshDocs();
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? All vectors and indexed chunks will be permanently removed.`)) {
      return;
    }
    try {
      await api.deleteDocument(docId);
      onRefreshDocs();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleInspectChunks = async (doc: DocumentItem) => {
    setInspectingDoc(doc);
    setLoadingChunks(true);
    try {
      const chunks = await api.getDocumentChunks(doc.id);
      setDocChunks(chunks);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingChunks(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="flex flex-col h-full bg-white border-r border-slate-200 overflow-hidden">
      {/* KB Header */}
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-800">{currentKb.name}</h2>
            <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">
              {currentKb.description || "Private research corpus"}
            </p>
          </div>
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
            {documents.length} {documents.length === 1 ? "document" : "documents"}
          </span>
        </div>
      </div>

      {/* Upload Dropzone */}
      <div className="p-4 border-b border-slate-200 bg-slate-50/50">
        <div
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
            uploading
              ? "border-indigo-400 bg-indigo-50/30 cursor-not-allowed"
              : "border-slate-300 hover:border-indigo-400 hover:bg-white"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md,.markdown"
            onChange={handleFileUpload}
            disabled={uploading}
            className="hidden"
          />
          <UploadCloud className={`w-8 h-8 mx-auto mb-2 ${uploading ? "animate-bounce text-indigo-600" : "text-slate-400"}`} />
          <p className="text-xs font-semibold text-slate-700">
            {uploading ? "Ingesting & indexing vectors..." : "Click or drag documents to upload"}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            PDF, TXT, or Markdown (Max 15MB)
          </p>
        </div>

        {uploadError && (
          <div className="mt-2 p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Selective Search Controls */}
      <div className="px-4 py-2 bg-slate-100/70 border-b border-slate-200 flex items-center justify-between text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <span>
            {selectedDocIds.length === 0
              ? "Scope: All documents"
              : `Scope: ${selectedDocIds.length} selected`}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {selectedDocIds.length > 0 && (
            <button
              onClick={() => onSelectAllDocs([])}
              className="text-xs text-slate-500 hover:text-slate-800 underline"
            >
              Reset to all
            </button>
          )}
          <button
            onClick={() => onSelectAllDocs(documents.map(d => d.id))}
            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
          >
            Select all
          </button>
        </div>
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
        {documents.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No documents uploaded yet. Upload a PDF or markdown document above to start indexing.
          </div>
        ) : (
          documents.map(doc => {
            const isSelected = selectedDocIds.includes(doc.id);

            return (
              <div
                key={doc.id}
                className={`p-3.5 flex items-start gap-3 transition-colors hover:bg-slate-50 ${
                  isSelected ? "bg-indigo-50/40" : ""
                }`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => onToggleSelectDoc(doc.id)}
                  className="mt-1 rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                  title="Filter search to this document"
                />

                <div className="p-2 rounded-lg bg-slate-100 text-slate-600 mt-0.5 shrink-0">
                  <FileText className="w-4 h-4" />
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-slate-800 truncate" title={doc.filename}>
                    {doc.filename}
                  </p>
                  <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
                    <span>{formatBytes(doc.file_size_bytes)}</span>
                    <span>&bull;</span>
                    <span>{doc.total_pages} {doc.total_pages === 1 ? "page" : "pages"}</span>
                    <span>&bull;</span>
                    <span className="font-mono">{doc.chunk_count} chunks</span>
                  </div>

                  {/* Status Indicator */}
                  <div className="mt-1.5 flex items-center gap-1.5">
                    {doc.processing_status === "COMPLETED" && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                        <CheckCircle className="w-3 h-3" /> Indexed
                      </span>
                    )}
                    {doc.processing_status === "PROCESSING" && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full animate-pulse">
                        <Clock className="w-3 h-3" /> Indexing
                      </span>
                    )}
                    {doc.processing_status === "PENDING" && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                        <Clock className="w-3 h-3" /> Pending
                      </span>
                    )}
                    {doc.processing_status === "FAILED" && (
                      <span
                        className="inline-flex items-center gap-1 text-[10px] font-medium text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full"
                        title={doc.error_message || "Processing failed"}
                      >
                        <AlertCircle className="w-3 h-3" /> Failed
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => handleInspectChunks(doc)}
                    className="p-1.5 text-slate-400 hover:text-indigo-600 rounded-md hover:bg-slate-100 transition-colors"
                    title="Inspect Chunks & Offsets"
                  >
                    <Eye className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id, doc.filename)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md hover:bg-slate-100 transition-colors"
                    title="Delete document & vectors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Chunks Inspector Drawer / Modal */}
      {inspectingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="relative w-full max-w-3xl rounded-xl bg-white p-6 shadow-2xl border border-slate-200 max-h-[85vh] flex flex-col">
            <button
              onClick={() => setInspectingDoc(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="border-b border-slate-200 pb-3 mb-4">
              <h3 className="text-base font-semibold text-slate-800">
                Chunk Inspector: {inspectingDoc.filename}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Total Chunks: {inspectingDoc.chunk_count} &bull; Pages: {inspectingDoc.total_pages} &bull; Total Size: {formatBytes(inspectingDoc.file_size_bytes)}
              </p>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
              {loadingChunks ? (
                <div className="p-8 text-center text-slate-400 text-xs">Loading chunks...</div>
              ) : docChunks.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs">No chunks found.</div>
              ) : (
                docChunks.map((c, i) => (
                  <div key={c.id || i} className="p-3.5 rounded-lg border border-slate-200 bg-slate-50">
                    <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
                      <span className="font-semibold text-indigo-700">
                        Chunk #{c.chunk_index} (Page {c.page_number})
                      </span>
                      <span className="font-mono text-[11px] text-slate-400">
                        Char Offsets: [{c.char_start} - {c.char_end}] ({c.content.length} chars)
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 font-mono leading-relaxed whitespace-pre-wrap bg-white p-3 rounded border border-slate-200">
                      {c.content}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
