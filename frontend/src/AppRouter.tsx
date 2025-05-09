import React, { useState } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Tools from './pages/Tools';
import './App.css'; // Ensure App.css is imported for layout styles

const AppRouter: React.FC = () => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('mcp_token'));

  const handleLogin = (t: string) => {
    localStorage.setItem('mcp_token', t);
    setToken(t);
  };

  const handleLogout = () => {
    localStorage.removeItem('mcp_token');
    setToken(null);
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="app-container">
      <header className="header">
        <h1>MCP Gateway Portal</h1>
        <button onClick={handleLogout} className="secondary">Sair</button>
      </header>
      <main className="main-content">
        <Dashboard token={token} />
        <Tools token={token} />
      </main>
    </div>
  );
};

export default AppRouter;
