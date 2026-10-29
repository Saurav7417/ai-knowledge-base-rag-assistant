import React from "react";
import type { CitationItem } from "../types";
import { X, FileText, CheckCircle2 } from "lucide-react";

interface CitationModalProps {
  citation: CitationItem | null;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="relative w-full max-w-xl rounded-xl bg-white p-6 shadow-2xl border border-slate-200">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors"
          title="Close citation preview"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 border-b border-slate-100 pb-4 mb-4">
          <div className="p-2.5 rounded-lg bg-indigo-50 text-indigo-600">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-slate-800">{citation.document_name}</h3>
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" /> Verified Grounded
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Page {citation.page_number} &bull; Similarity: {(citation.similarity_score * 100).toFixed(1)}% &bull; Chunk: <span className="font-mono text-slate-400">{citation.chunk_id.slice(0, 8)}</span>
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Extracted Supporting Passage
          </label>
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 text-sm leading-relaxed font-sans max-h-64 overflow-y-auto whitespace-pre-wrap">
            "{citation.excerpt}"
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            Close Source Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
