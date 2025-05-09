import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { fetchWithAuth } from '../utils/api';

interface User {
  sub: string;
  username?: string;
  grupos: string[];
  papel: string;
  exp: number;
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Função para decodificar o payload do JWT
function parseJwt(token: string): User | null {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return null;
  }
}

// Função para verificar se um token está expirado
function isTokenExpired(token: string): boolean {
  try {
    const decoded = parseJwt(token);
    if (!decoded || !decoded.exp) return true;
    
    // Adiciona margem de segurança (30 segundos) para evitar que o token expire durante a requisição
    return decoded.exp * 1000 < Date.now() + 30000;
  } catch {
    return true;
  }
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => {
    const storedToken = localStorage.getItem('mcp_token');
    if (storedToken && isTokenExpired(storedToken)) {
      localStorage.removeItem('mcp_token');
      return null;
    }
    return storedToken;
  });
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  // Computar isAuthenticated com base nos valores de token e user
  const isAuthenticated = Boolean(token && user);

  // Função para atualizar o token
  const refreshToken = useCallback(async (): Promise<boolean> => {
    if (!token) return false;
    
    try {
      setIsLoading(true);
      const response = await fetchWithAuth('/tools/refresh-token', token);
      
      if (!response.ok) {
        // Se token expirou, limpar sessão do usuário
        if (response.status === 401) {
          localStorage.removeItem('mcp_token');
          setToken(null);
          setUser(null);
        }
        console.error('Erro ao renovar token:', response.status);
        return false;
      }
      
      const data = await response.json();
      const newToken = data.access_token;
      
      const tokenValue = newToken.startsWith('Bearer ') 
        ? newToken.substring(7) 
        : newToken;
      
      localStorage.setItem('mcp_token', tokenValue);
      setToken(tokenValue);
      
      const userData = parseJwt(tokenValue);
      if (userData) {
        setUser(userData);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Erro inesperado ao renovar token:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    setIsLoading(true);
    
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const decodedUser = parseJwt(token);
      if (decodedUser) {
        if (decodedUser.exp * 1000 > Date.now()) {
          setUser(decodedUser);
        } else {
          console.warn('Token expirado. Limpando sessão.');
          localStorage.removeItem('mcp_token');
          setToken(null);
          setUser(null);
        }
      } else {
        console.warn('Token inválido. Limpando sessão.');
        localStorage.removeItem('mcp_token');
        setToken(null);
        setUser(null);
      }
    } catch (error) {
      console.error('Erro ao processar token:', error);
      localStorage.removeItem('mcp_token');
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  const login = (newToken: string) => {
    const tokenValue = newToken.startsWith('Bearer ') 
      ? newToken.substring(7) 
      : newToken;
    
    localStorage.setItem('mcp_token', tokenValue);
    setToken(tokenValue);
    
    const userData = parseJwt(tokenValue);
    if (userData) {
      setUser(userData);
    } else {
      console.error('Falha ao decodificar token durante login');
    }
  };

  const logout = () => {
    localStorage.removeItem('mcp_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      token, 
      user, 
      isAuthenticated,
      isLoading, 
      login, 
      logout,
      refreshToken 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
