import React, { useEffect, useState } from 'react';
import '../App.css';
import { fetchWithAuth } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';
import { useError } from '../contexts/ErrorContext';
import useLoading from '../hooks/useLoading';
import LoadingSpinner from '../components/LoadingSpinner';

// Interface simplificada para o grupo
interface GroupItem {
  id: string;
  nome: string;
}

const Dashboard: React.FC = () => {
  const { token, user } = useAuth();
  const { setError } = useError();
  const { isLoading, error, execute } = useLoading();
  const [groups, setGroups] = useState<GroupItem[]>([]);

  useEffect(() => {
    const fetchGroups = async () => {
      if (!token) return;

      const result = await execute(
        fetchWithAuth('/tools/grupos', token)
          .then(async (response) => {
            if (!response.ok) {
              const errorText = await response.text();
              let errorDetail = 'Falha ao buscar grupos';
              
              try {
                const errorData = JSON.parse(errorText);
                errorDetail = errorData.detail || errorDetail;
              } catch (e) {
                errorDetail = errorText || errorDetail;
              }
              
              throw new Error(errorDetail);
            }
            
            const data = await response.json();
            // Tratar corretamente a resposta
            if (data && data.grupos && Array.isArray(data.grupos)) {
              return data.grupos.map((groupName: string) => ({ 
                id: groupName, 
                nome: groupName
              }));
            } else if (Array.isArray(data)) {
              return data;
            }
            return [];
          })
      );

      if (result) {
        setGroups(result);
      }
    };

    fetchGroups();
  }, [token, execute]);

  // Mostrar erro usando o context de erro global
  useEffect(() => {
    if (error) {
      setError({ message: error });
    }
  }, [error, setError]);

  return (
    <div className="dashboard-page card">
      <h1>Dashboard</h1>
      <p>Bem-vindo, {user?.username || user?.sub || 'usuário'}!</p>

      <div className="user-info card">
        <h3>Suas informações:</h3>
        <p><strong>Usuário:</strong> {user?.username || user?.sub || 'N/A'}</p>
        <p><strong>Papel:</strong> {user?.papel || 'N/A'}</p>
        <p><strong>Grupos:</strong> {user?.grupos?.join(', ') || 'Nenhum grupo'}</p>
      </div>

      {/* Ações dinâmicas por papel */}
      {user?.papel === 'global_admin' && (
        <div className="card success-message">Você é administrador global. Acesse a gestão completa de grupos e usuários pelo menu.</div>
      )}
      {user?.papel === 'admin' && (
        <div className="card success-message">Você é admin de grupo. Gerencie seu(s) grupo(s) pelo menu.</div>
      )}
      {user?.papel === 'user' && (
        <div className="card">Você pode visualizar e acessar ferramentas dos seus grupos.</div>
      )}

      {/* Lista de grupos (admin global) */}
      {user?.papel === 'global_admin' && (
        <div className="groups-section card">
          <h3>Grupos no Sistema</h3>
          
          {isLoading ? (
            <LoadingSpinner message="Carregando grupos..." />
          ) : groups.length > 0 ? (
            <ul className="group-list">
              {groups.map(group => (
                <li key={group.id} className="group-item">
                  {group.nome}
                </li>
              ))}
            </ul>
          ) : (
            <p>Nenhum grupo encontrado.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
