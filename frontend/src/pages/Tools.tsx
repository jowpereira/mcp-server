import { useEffect, useState } from 'react';
import '../App.css';

type ToolsProps = {
  token: string;
  user: any;
};

const Tools = ({ token, user }: ToolsProps) => {
  const [tools, setTools] = useState<string[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTools = async () => {
      setError('');
      try {
        // Exemplo: buscar ferramentas do grupo do usuário
        // Aqui, só um placeholder para /tools/ferramenta_x
        const res = await fetch('/tools/ferramenta_x', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          setTools(['ferramenta_x']);
        } else {
          setTools([]);
          setError('Você não tem permissão para acessar ferramentas ou nenhuma disponível.');
        }
      } catch {
        setError('Erro de conexão ao buscar ferramentas.');
        setTools([]);
      }
    };
    fetchTools();
  }, [token, user]);

  return (
    <div className="card">
      <h2>Ferramentas Disponíveis</h2>
      {error && <div className="error-message message-spacing">{error}</div>}
      {tools.length > 0 ? (
        <ul className="list-group">
          {tools.map(tool => (
            <li key={tool} className="list-group-item">{tool}</li>
          ))}
        </ul>
      ) : (
        !error && <p>Nenhuma ferramenta disponível ou configurada para você no momento.</p>
      )}
    </div>
  );
};

export default Tools;
