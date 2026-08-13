import { createContext, useContext, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type CurrentSubject } from "../api/client";

interface AuthContextValue {
  subject: CurrentSubject | undefined;
  isLoading: boolean;
  isAuthenticated: boolean;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [enabled, setEnabled] = useState(true);

  const query = useQuery({
    queryKey: ["auth", "me"],
    queryFn: api.me,
    enabled,
    retry: false,
    staleTime: 60_000,
  });

  const refresh = async () => {
    setEnabled(true);
    await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
  };

  const value: AuthContextValue = {
    subject: query.data,
    isLoading: query.isLoading,
    isAuthenticated: Boolean(query.data),
    refresh,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
