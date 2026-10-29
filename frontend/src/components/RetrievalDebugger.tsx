import React, { useState } from "react";
import type { RetrievedChunkDebug, RAGMetrics } from "../types";
import { Activity, Clock, Layers, ShieldCheck, ChevronDown, ChevronUp } from "lucide-react";

interface RetrievalDebuggerProps {
  chunks: RetrievedChunkDebug[];
  metrics?: RAGMetrics;
  abstentionReason?: string;
}

export const RetrievalDebugger: React.FC<RetrievalDebuggerProps> = ({
  chunks,
  metrics,
  abstentionReason
}) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!chunks || chunks.length === 0) return null;

  return (
    <div className="mt-3 border border-slate-200 rounded-lg overflow-hidden bg-white text-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 transition-colors"
      >
        <div className="flex items-center gap-2 font-medium">
          <Activity className="w-4 h-4 text-indigo-600" />
          <span>RAG Retrieval Debugger & Telemetry</span>
          <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-[10px]">
            {chunks.length} candidate chunks
          </span>
          {metrics?.total_time_ms && (
            <span className="text-slate-500 font-mono text-[11px]">
              &bull; {metrics.total_time_ms} ms
            </span>
          )}
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>

      {isOpen && (
        <div className="p-4 space-y-4 border-t border-slate-200 bg-slate-50/50">
          {/* Latency & Metrics Cards */}
          {metrics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div className="p-2.5 rounded-md bg-white border border-slate-200">
                <div className="flex items-center gap-1.5 text-slate-500 mb-1">
                  <Clock className="w-3.5 h-3.5 text-blue-500" />
                  <span>Retrieval Time</span>
                </div>
                <p className="text-sm font-semibold font-mono text-slate-800">
                  {metrics.retrieval_time_ms ?? 0} ms
                </p>
              </div>

              <div className="p-2.5 rounded-md bg-white border border-slate-200">
                <div className="flex items-center gap-1.5 text-slate-500 mb-1">
                  <Clock className="w-3.5 h-3.5 text-purple-500" />
                  <span>Generation Time</span>
                </div>
                <p className="text-sm font-semibold font-mono text-slate-800">
                  {metrics.generation_time_ms ?? 0} ms
                </p>
              </div>

              <div className="p-2.5 rounded-md bg-white border border-slate-200">
                <div className="flex items-center gap-1.5 text-slate-500 mb-1">
                  <Layers className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Passed Threshold</span>
                </div>
                <p className="text-sm font-semibold font-mono text-slate-800">
                  {metrics.passed_threshold_count ?? 0} / {metrics.retrieved_count ?? chunks.length}
                </p>
              </div>

              <div className="p-2.5 rounded-md bg-white border border-slate-200">
                <div className="flex items-center gap-1.5 text-slate-500 mb-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Verified Citations</span>
                </div>
                <p className="text-sm font-semibold font-mono text-slate-800">
                  {metrics.valid_citations_count ?? 0}
                  {metrics.hallucinated_citations_stripped ? (
                    <span className="text-xs text-rose-600 ml-1">
                      ({metrics.hallucinated_citations_stripped} stripped)
                    </span>
                  ) : null}
                </p>
              </div>
            </div>
          )}

          {/* Abstention Reason banner if applicable */}
          {abstentionReason && (
            <div className="p-2.5 rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-xs">
              <strong>Abstention Trigger:</strong> {abstentionReason}
            </div>
          )}

          {/* Candidate Chunks Inspection Table */}
          <div className="space-y-2">
            <h4 className="font-semibold text-slate-700 text-xs uppercase tracking-wider">
              Retrieved Evidence Chunks (Ranked)
            </h4>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {chunks.map((chunk, idx) => (
                <div
                  key={chunk.chunk_id || idx}
                  className={`p-3 rounded-lg border transition-all ${
                    chunk.passed_threshold
                      ? "bg-white border-slate-200 shadow-xs"
                      : "bg-slate-100/70 border-dashed border-slate-300 opacity-60"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 flex items-center justify-center rounded-full bg-slate-100 text-slate-600 font-bold text-[10px]">
                        #{idx + 1}
                      </span>
                      <span className="font-medium text-slate-800">{chunk.document_name}</span>
                      <span className="text-slate-400">&bull;</span>
                      <span className="text-slate-500">Page {chunk.page_number}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                        Cosine Sim: {(chunk.similarity_score * 100).toFixed(1)}%
                      </span>
                      {chunk.rerank_score !== undefined && (
                        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">
                          Rerank: {(chunk.rerank_score * 100).toFixed(1)}%
                        </span>
                      )}
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                          chunk.passed_threshold
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-rose-100 text-rose-800"
                        }`}
                      >
                        {chunk.passed_threshold ? "Passed Threshold" : "Below Threshold"}
                      </span>
                    </div>
                  </div>

                  <p className="text-slate-600 text-[11px] font-mono leading-relaxed bg-slate-50 p-2 rounded border border-slate-200/70 max-h-24 overflow-y-auto whitespace-pre-wrap">
                    {chunk.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
