import React, { useState, useEffect } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Tools from './pages/Tools';
import GroupAdmin from './pages/GroupAdmin';
import UserRequests from './pages/UserRequests';
import './App.css';

// Utilitário para decodificar o payload do JWT
function parseJwt(token: string) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return null;
  }
}

const AppRouter: React.FC = () => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('mcp_token'));
  const [user, setUser] = useState<any>(null);
  const [isValid, setIsValid] = useState<boolean>(false);
  const [checking, setChecking] = useState<boolean>(true);
  const [view, setView] = useState<'dashboard'|'tools'|'groupadmin'|'requests'>('dashboard');

  useEffect(() => {
    const validateToken = async () => {
      setChecking(true);
      setIsValid(false);
      setUser(null);
      if (!token) {
        setChecking(false);
        return;
      }
      try {
        const res = await fetch('/tools/health', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          setIsValid(true);
          setUser(parseJwt(token));
        } else {
          setIsValid(false);
        }
      } catch {
        setIsValid(false);
      } finally {
        setChecking(false);
      }
    };
    validateToken();
  }, [token]);

  const handleLogin = (t: string) => {
    localStorage.setItem('mcp_token', t);
    setToken(t);
  };

  const handleLogout = () => {
    localStorage.removeItem('mcp_token');
    setToken(null);
    setIsValid(false);
    setUser(null);
  };

  if (checking) {
    return <div className="card">Verificando sessão...</div>;
  }

  if (!token || !isValid || !user) {
    return <Login onLogin={handleLogin} />;
  }

  // Barra de navegação dinâmica
  return (
    <div className="app-container">
      <header className="header">
        <h1>MCP Gateway Portal</h1>
        <nav>
          <button onClick={() => setView('dashboard')}>Dashboard</button>
          <button onClick={() => setView('tools')}>Ferramentas</button>
          {(user.papel === 'global_admin' || user.papel === 'admin') && (
            <button onClick={() => setView('groupadmin')}>Gestão de Grupos</button>
          )}
          <button onClick={() => setView('requests')}>Solicitações</button>
          <button onClick={handleLogout} className="secondary">Sair</button>
        </nav>
      </header>
      <main className="main-content">
        {view === 'dashboard' && <Dashboard token={token} user={user} />}
        {view === 'tools' && <Tools token={token} user={user} />}
        {view === 'groupadmin' && (user.papel === 'global_admin' || user.papel === 'admin') && (
          <GroupAdmin token={token} user={user} />
        )}
        {view === 'requests' && <UserRequests token={token} user={user} />}
      </main>
    </div>
  );
};

export default AppRouter;
