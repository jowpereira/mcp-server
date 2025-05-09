import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Tools from './pages/Tools';
import GroupAdmin from './pages/GroupAdmin';
import UserRequests from './pages/UserRequests';
import RequestsAdmin from './pages/RequestsAdmin';
import ProtectedRoute from './components/ProtectedRoute';
import { useAuth } from './contexts/AuthContext';
import LoadingSpinner from './components/LoadingSpinner';
import './App.css';

const AppRouter: React.FC = () => {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="loading-container">
        <LoadingSpinner message="Carregando aplicação..." />
      </div>
    );
  }

  return (
    <Routes>
      {/* Se estiver logado e tentar acessar /login, redireciona para /dashboard */}
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} 
      />
      
      {/* Rotas Protegidas básicas - qualquer usuário autenticado */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/tools" element={<Tools />} />
        {/* Rota padrão para usuários logados */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Route>      {/* Rotas para administradores de grupo */}
      <Route element={<ProtectedRoute requiredRoles={['admin', 'global_admin']} />}>
        <Route path="/groupadmin" element={<GroupAdmin />} />
        <Route path="/admin/requests" element={<RequestsAdmin />} />
      </Route>

      {/* Rotas exclusivas para administradores globais */}
      <Route element={<ProtectedRoute requiredRoles={['global_admin']} />}>
        <Route path="/admin/users" element={<UserRequests />} /> {/* Pode ser reutilizado ou novo componente */}
      </Route>
      
      {/* Rotas para usuários comuns */}
      <Route element={<ProtectedRoute />}>
        <Route path="/requests" element={<UserRequests />} />
      </Route>

      {/* Rota de fallback para qualquer caminho não correspondido */}
      <Route path="*" element={
        <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
      } />
    </Routes>
  );
};

export default AppRouter;
