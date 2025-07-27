import React, { createContext, useContext, useState } from "react";

const AuthContext = createContext<any>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<string | null>(localStorage.getItem("user_id"));

  const login = (user_id: string) => {
    setUser(user_id);
    localStorage.setItem("user_id", user_id);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("user_id");
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}