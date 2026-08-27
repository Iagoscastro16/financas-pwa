import { createContext, useContext, useEffect, useRef, useState } from "react";

import { setTokenGetter } from "../api/client";
import { login as loginRequest } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  // The interceptor in api/client.js reads through a ref instead of the
  // `token` state directly, so it always sees the latest value without
  // needing to be re-created on every render.
  const tokenRef = useRef(null);

  useEffect(() => {
    setTokenGetter(() => tokenRef.current);
  }, []);

  async function login(username, password) {
    const { access_token } = await loginRequest(username, password);
    tokenRef.current = access_token;
    setToken(access_token);
  }

  function logout() {
    tokenRef.current = null;
    setToken(null);
  }

  const value = {
    token,
    isAuthenticated: Boolean(token),
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
}
