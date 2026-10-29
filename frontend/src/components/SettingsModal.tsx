import React from "react";
import { X, Sliders, Shield, Zap } from "lucide-react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: {
    topK: number;
    similarityThreshold: number;
    rerank: boolean;
  };
  onSave: (newSettings: { topK: number; similarityThreshold: number; rerank: boolean }) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSave
}) => {
  const [topK, setTopK] = React.useState(settings.topK);
  const [threshold, setThreshold] = React.useState(settings.similarityThreshold);
  const [rerank, setRerank] = React.useState(settings.rerank);

  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ topK, similarityThreshold: threshold, rerank });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
      <div className="w-full max-w-md rounded-xl bg-white border border-slate-200 p-6 shadow-2xl text-slate-800">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-semibold text-slate-800">RAG Pipeline Hyperparameters</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-5 text-xs">
          {/* Top K */}
          <div>
            <div className="flex justify-between mb-1.5 font-medium">
              <label className="text-slate-700">Top-K Candidate Chunks</label>
              <span className="font-mono text-indigo-600 font-bold">{topK}</span>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value, 10))}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Number of closest vector passages sent to the LLM context window.
            </p>
          </div>

          {/* Similarity Threshold */}
          <div>
            <div className="flex justify-between mb-1.5 font-medium">
              <label className="text-slate-700">Cosine Similarity Threshold</label>
              <span className="font-mono text-indigo-600 font-bold">{(threshold * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={threshold * 100}
              onChange={(e) => setThreshold(parseFloat(e.target.value) / 100)}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Minimum cosine similarity score required for chunks to pass the abstention gate.
            </p>
          </div>

          {/* Reranker Toggle */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
            <div className="mr-3">
              <div className="flex items-center gap-1.5 font-medium text-slate-800">
                <Zap className="w-3.5 h-3.5 text-amber-500" />
                <span>Reciprocal Rank Reranker</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Combines semantic vectors with BM25 keyword matching for higher precision.
              </p>
            </div>
            <input
              type="checkbox"
              checked={rerank}
              onChange={(e) => setRerank(e.target.checked)}
              className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500 cursor-pointer"
            />
          </div>

          {/* Grounding & Security Note */}
          <div className="p-3 rounded-lg bg-indigo-50/50 border border-indigo-100 flex items-start gap-2 text-indigo-900">
            <Shield className="w-4 h-4 shrink-0 text-indigo-600 mt-0.5" />
            <p className="text-[11px] leading-relaxed">
              XML boundary isolation and citation validation are continuously active to prevent indirect prompt injection and citation fabrication.
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 text-xs font-medium text-slate-500 hover:text-slate-800 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors shadow-xs"
            >
              Apply Settings
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
