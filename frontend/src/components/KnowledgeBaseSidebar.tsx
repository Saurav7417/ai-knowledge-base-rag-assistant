import React, { useState } from "react";
import type { KnowledgeBase } from "../types";
import { useAuth } from "../context/AuthContext";
import {
  Plus,
  Trash2,
  Edit2,
  LogOut,
  Folder,
  Sliders,
  Sparkles,
  Check,
  X
} from "lucide-react";

interface KnowledgeBaseSidebarProps {
  knowledgeBases: KnowledgeBase[];
  currentKb: KnowledgeBase | null;
  onSelectKb: (kb: KnowledgeBase) => void;
  onCreateKb: (name: string, desc?: string) => Promise<void>;
  onUpdateKb: (id: string, name: string, desc?: string) => Promise<void>;
  onDeleteKb: (id: string) => Promise<void>;
  onOpenSettings: () => void;
}

export const KnowledgeBaseSidebar: React.FC<KnowledgeBaseSidebarProps> = ({
  knowledgeBases,
  currentKb,
  onSelectKb,
  onCreateKb,
  onUpdateKb,
  onDeleteKb,
  onOpenSettings
}) => {
  const { user, logout } = useAuth();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKbName, setNewKbName] = useState("");
  const [newKbDesc, setNewKbDesc] = useState("");
  const [editingKbId, setEditingKbId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKbName.trim()) return;
    await onCreateKb(newKbName.trim(), newKbDesc.trim() || undefined);
    setNewKbName("");
    setNewKbDesc("");
    setShowCreateModal(false);
  };

  const handleStartEdit = (kb: KnowledgeBase, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingKbId(kb.id);
    setEditName(kb.name);
  };

  const handleSaveEdit = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (editName.trim()) {
      await onUpdateKb(id, editName.trim());
    }
    setEditingKbId(null);
  };

  const handleDelete = async (id: string, name: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm(`Delete knowledge base "${name}"? All associated documents and chats will be deleted.`)) {
      await onDeleteKb(id);
    }
  };

  return (
    <div className="w-72 bg-slate-900 text-slate-200 flex flex-col h-full border-r border-slate-800 shrink-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800 flex items-center gap-3">
        <div className="p-2 rounded-lg bg-indigo-600 text-white shadow-md shadow-indigo-500/20">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-white tracking-tight">AI Knowledge Base</h1>
          <p className="text-[11px] text-slate-400 font-medium">Research Assistant & RAG</p>
        </div>
      </div>

      {/* Action Header */}
      <div className="px-4 py-3 flex items-center justify-between text-xs font-semibold text-slate-400 tracking-wider uppercase">
        <span>Knowledge Bases</span>
        <button
          onClick={() => setShowCreateModal(true)}
          className="p-1 text-indigo-400 hover:text-white rounded-md hover:bg-slate-800 transition-colors"
          title="Create Knowledge Base"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* KB List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-1">
        {knowledgeBases.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-500">
            No knowledge bases yet. Click + to create one.
          </div>
        ) : (
          knowledgeBases.map((kb) => {
            const isSelected = currentKb?.id === kb.id;
            const isEditing = editingKbId === kb.id;

            return (
              <div
                key={kb.id}
                onClick={() => onSelectKb(kb)}
                className={`group px-3 py-2.5 rounded-lg cursor-pointer text-xs flex items-center justify-between transition-colors ${
                  isSelected
                    ? "bg-indigo-600/20 text-white border border-indigo-500/30 font-medium"
                    : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                  <Folder className={`w-4 h-4 shrink-0 ${isSelected ? "text-indigo-400" : "text-slate-400"}`} />
                  {isEditing ? (
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="bg-slate-800 text-white px-2 py-0.5 rounded text-xs w-full focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
                      autoFocus
                    />
                  ) : (
                    <span className="truncate">{kb.name}</span>
                  )}
                </div>

                <div className="flex items-center gap-1.5 shrink-0 ml-2">
                  {isEditing ? (
                    <>
                      <button
                        onClick={(e) => handleSaveEdit(kb.id, e)}
                        className="text-emerald-400 hover:text-emerald-300 p-0.5"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingKbId(null);
                        }}
                        className="text-slate-400 hover:text-slate-300 p-0.5"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </>
                  ) : (
                    <>
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
                        {kb.document_count}
                      </span>
                      <div className="hidden group-hover:flex items-center gap-1">
                        <button
                          onClick={(e) => handleStartEdit(kb, e)}
                          className="text-slate-400 hover:text-slate-200 p-0.5"
                          title="Rename"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => handleDelete(kb.id, kb.name, e)}
                          className="text-slate-400 hover:text-rose-400 p-0.5"
                          title="Delete KB"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Profile & Settings */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40">
        <div className="flex items-center justify-between text-xs">
          <div className="min-w-0 flex-1 mr-2">
            <p className="font-medium text-white truncate">{user?.full_name || "AI Researcher"}</p>
            <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={onOpenSettings}
              className="p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-800 transition-colors"
              title="RAG Parameters & Settings"
            >
              <Sliders className="w-4 h-4" />
            </button>
            <button
              onClick={logout}
              className="p-1.5 text-slate-400 hover:text-rose-400 rounded-md hover:bg-slate-800 transition-colors"
              title="Log out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Create KB Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-sm rounded-xl bg-slate-900 border border-slate-800 p-6 shadow-2xl text-slate-200">
            <h3 className="text-base font-semibold text-white mb-4">Create Knowledge Base</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Cloud Security Architecture"
                  value={newKbName}
                  onChange={(e) => setNewKbName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-hidden focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Description (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Technical handbooks, SOC2 policies, and RFCs"
                  value={newKbDesc}
                  onChange={(e) => setNewKbDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-hidden focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors"
                >
                  Create Knowledge Base
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
