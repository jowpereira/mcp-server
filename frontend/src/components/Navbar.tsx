import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../App.css'; // Reutilizando o CSS existente

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">MCP Gateway</Link>
      </div>
      {user && (        <div className="navbar-links">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/tools">Ferramentas</Link>
          
          {/* Links para usuários comuns */}
          <Link to="/requests">Minhas Solicitações</Link>
          
          {/* Links dinâmicos por papel */}
          {(user.papel === 'global_admin' || user.papel === 'admin') && (
            <>
              <Link to="/groupadmin">Gerenciar Grupos</Link>
              <Link to="/admin/requests">Revisar Solicitações</Link>
            </>
          )}
          
          {/* Links apenas para admin global */}
          {user.papel === 'global_admin' && (
            <Link to="/admin/users">Gerenciar Usuários</Link>
          )}
        </div>
      )}
      <div className="navbar-user">
        {user ? (
          <>
            <span>Olá, {user.username || user.sub || 'Usuário'}</span>
            <button onClick={handleLogout} className="button-logout">Sair</button>
          </>
        ) : (
          <Link to="/login">Login</Link>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
