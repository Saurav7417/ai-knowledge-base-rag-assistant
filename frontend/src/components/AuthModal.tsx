import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Sparkles, Lock, Mail, User, AlertCircle, ArrowRight } from "lucide-react";

interface AuthModalProps {
  isOpen: boolean;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen }) => {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        await register(email, password, fullName || undefined);
      } else {
        await login(email, password);
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      // Try login first, if user doesn't exist, register
      try {
        await login("demo.researcher@antigravity.ai", "DemoPassword123!");
      } catch (_) {
        await register("demo.researcher@antigravity.ai", "DemoPassword123!", "Demo AI Researcher");
      }
    } catch (err: any) {
      setError(err.message || "Demo login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl bg-white border border-slate-200 p-8 shadow-2xl">
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 text-white flex items-center justify-center mx-auto mb-3 shadow-lg shadow-indigo-500/25">
            <Sparkles className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-slate-800">
            {isRegister ? "Create Research Account" : "Welcome Back"}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {isRegister
              ? "Start indexing documents with isolated tenant security"
              : "Access your private knowledge bases and research history"}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="e.g. Marie Curie"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-hidden focus:border-indigo-500 focus:bg-white"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="email"
                required
                placeholder="researcher@institute.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-hidden focus:border-indigo-500 focus:bg-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                minLength={6}
                placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-hidden focus:border-indigo-500 focus:bg-white"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-md shadow-indigo-500/20 transition-colors flex items-center justify-center gap-1.5"
          >
            <span>{loading ? "Authenticating..." : isRegister ? "Create Account" : "Sign In"}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-col gap-2">
          {/* Quick Demo Access Button */}
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={loading}
            className="w-full py-2 px-3 border border-indigo-200 hover:bg-indigo-50/50 text-indigo-700 text-xs font-medium rounded-lg transition-colors flex items-center justify-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            <span>1-Click Demo Login (Pre-configured)</span>
          </button>

          <p className="text-center text-xs text-slate-500 mt-2">
            {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
            <button
              onClick={() => {
                setIsRegister(!isRegister);
                setError(null);
              }}
              className="text-indigo-600 hover:text-indigo-800 font-semibold underline ml-1"
            >
              {isRegister ? "Sign In" : "Sign Up"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};
