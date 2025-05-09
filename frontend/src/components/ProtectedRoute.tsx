import React, { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import AuthService from '../utils/authService';

interface ProtectedRouteProps {
  requiredRoles?: string[];  // Papéis exigidos para acessar esta rota
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ requiredRoles = [] }) => {
  const { token, user, isLoading, refreshToken } = useAuth();
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const location = useLocation();

  // Verifica e atualiza autenticação quando o componente é montado
  useEffect(() => {
    const checkAndRefreshAuth = async () => {
      setIsCheckingAuth(true);
      
      if (token) {
        // Se estamos carregando, espera terminar
        if (isLoading) {
          setIsCheckingAuth(false);
          return;
        }
        
        try {
          // Verifica se o token está próximo de expirar e renova se necessário
          const needsRefresh = await AuthService.isAuthenticated();
          if (!needsRefresh) {
            await refreshToken();
          }
        } catch (error) {
          console.error('Erro ao verificar autenticação:', error);
        }
      }
      
      setIsCheckingAuth(false);
    };
    
    checkAndRefreshAuth();
  }, [token, isLoading, refreshToken]);
  
  // Se estamos carregando ou verificando autenticação, mostra spinner
  if (isLoading || isCheckingAuth) {
    return (
      <div className="protected-route-loading">
        <LoadingSpinner message="Verificando autenticação..." />
      </div>
    );
  }
  
  // Verifica se o usuário está autenticado
  if (!token || !user) {
    // Redireciona para login, preservando a rota que o usuário tentou acessar
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  
  // Verificação de papel (role) se especificado
  if (requiredRoles.length > 0) {
    const userRole = user.papel;
    
    // Se o papel do usuário não estiver na lista de papéis requeridos
    if (!requiredRoles.includes(userRole)) {
      return (
        <div className="error-message card">
          <h3>Acesso Negado</h3>
          <p>Você não tem permissão para acessar esta página.</p>
          <p>Seu papel atual: <strong>{userRole}</strong></p>
          <p>Papéis necessários: <strong>{requiredRoles.join(', ')}</strong></p>
          <button onClick={() => window.history.back()}>Voltar</button>
        </div>
      );
    }
  }
  
  // Usuário autenticado com o papel correto
  return <Outlet />;
};

export default ProtectedRoute;
