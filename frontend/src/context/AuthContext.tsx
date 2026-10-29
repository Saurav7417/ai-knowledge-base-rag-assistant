import React, { createContext, useContext, useState, useEffect } from "react";
import type { User } from "../types";
import { api } from "../api/client";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  register: (email: string, pass: string, name?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchProfile = async () => {
    if (!api.getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const u = await api.getMe();
      setUser(u);
    } catch (_) {
      setUser(null);
      api.setToken(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();

    const handleUnauthorized = () => {
      setUser(null);
    };

    window.addEventListener("auth-unauthorized", handleUnauthorized);
    return () => window.removeEventListener("auth-unauthorized", handleUnauthorized);
  }, []);

  const login = async (email: string, pass: string) => {
    await api.login(email, pass);
    await fetchProfile();
  };

  const register = async (email: string, pass: string, name?: string) => {
    await api.register(email, pass, name);
    await fetchProfile();
  };

  const logout = () => {
    api.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
