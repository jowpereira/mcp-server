import { useEffect, useState } from 'react';
import '../App.css'; // Ensure App.css is imported

type ToolsProps = {
  token: string;
};

const Tools = ({ token }: ToolsProps) => {
  const [tools, setTools] = useState<string[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTools = async () => {
      setError('');
      try {
        // TODO: Replace with a generic endpoint to list all available tools for the user
        // For now, it attempts to access 'ferramenta_x' and infers availability.
        const res = await fetch('/tools/ferramenta_x', { // Example endpoint
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.status === 403) {
          setTools([]);
          setError('Você não tem permissão para acessar a ferramenta_x ou ela não existe.');
        } else if (res.ok) {
          // Assuming success means this specific tool is available
          // In a real scenario, the endpoint would return a list of tools.
          setTools(['ferramenta_x (Exemplo)']);
        } else {
          const errorData = await res.json().catch(() => null);
          setError(errorData?.detail || 'Erro ao buscar ferramentas.');
          setTools([]);
        }
      } catch (err: any) {
        setError('Erro de conexão ao buscar ferramentas.');
        setTools([]);
      }
    };
    fetchTools();
  }, [token]);

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
