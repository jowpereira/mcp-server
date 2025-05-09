import React, { useEffect, useState } from 'react';
import '../App.css';

interface UserRequestsProps {
  token: string;
  user: any;
}

const UserRequests: React.FC<UserRequestsProps> = ({ token, user }) => {
  const [requests, setRequests] = useState<any[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    // Exemplo: buscar solicitações de acesso do usuário
    // Endpoint real pode variar conforme backend
    setError('');
    const fetchRequests = async () => {
      try {
        // Exemplo: /tools/grupos/{grupo}/solicitacoes
        // Aqui, só um placeholder
        setRequests([]);
      } catch {
        setError('Erro ao buscar solicitações.');
      }
    };
    fetchRequests();
  }, [token]);

  return (
    <div className="card">
      <h2>Solicitações de Acesso</h2>
      {error && <div className="error-message">{error}</div>}
      {requests.length === 0 ? (
        <p>Nenhuma solicitação pendente.</p>
      ) : (
        <ul className="list-group">
          {requests.map((req: any, idx) => (
            <li key={idx} className="list-group-item">{JSON.stringify(req)}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default UserRequests;
