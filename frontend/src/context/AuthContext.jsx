import { useQueryClient } from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { fetchMe, loginRequest, registerRequest } from "../api/auth";
import { clearToken, getToken, onUnauthorized, setToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState(null);
  // If a token is saved, we must ask the server who it belongs to before showing pages
  const [loading, setLoading] = useState(Boolean(getToken()));

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    queryClient.clear(); // forget every invoice the previous person loaded
  }, [queryClient]);

  useEffect(() => {
    if (!getToken()) return;
    fetchMe()
      .then(setUser)
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, [logout]);

  useEffect(() => onUnauthorized(logout), [logout]);

  const login = useCallback(
    async (email, password) => {
      clearToken(); // never send an old token along with a login attempt
      queryClient.clear();
      const token = await loginRequest(email, password);
      setToken(token);
      setUser(await fetchMe());
    },
    [queryClient],
  );

  const register = useCallback(
    async (email, password) => {
      await registerRequest(email, password);
      await login(email, password);
    },
    [login],
  );

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}
