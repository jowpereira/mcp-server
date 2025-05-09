import React, { useEffect, useState } from 'react';
import '../App.css';

interface GroupAdminProps {
  token: string;
  user: any;
}

const GroupAdmin: React.FC<GroupAdminProps> = ({ token, user }) => {
  const [groups, setGroups] = useState<any[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchGroups = async () => {
      setError('');
      try {
        const res = await fetch('/tools/grupos', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setGroups(data.grupos || []);
        } else {
          setError('Erro ao buscar grupos.');
        }
      } catch {
        setError('Erro de conexão ao buscar grupos.');
      }
    };
    fetchGroups();
  }, [token]);

  return (
    <div className="card">
      <h2>Gestão de Grupos</h2>
      {error && <div className="error-message">{error}</div>}
      <ul className="list-group">
        {groups.map((g: any) => (
          <li key={g} className="list-group-item">{g}</li>
        ))}
      </ul>
      {/* Adicione aqui botões para criar/editar/remover grupos, promover admins, etc. */}
    </div>
  );
};

export default GroupAdmin;
