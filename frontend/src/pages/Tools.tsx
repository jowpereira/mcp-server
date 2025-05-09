import React, { useEffect, useState, useCallback } from 'react';
import '../App.css';
import { fetchWithAuth, getErrorBody } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';

// Group interface might be removed if not used elsewhere after this change
/*
interface Group {
  id: string;
  nome: string;
  usuarios: string[]; 
}
*/

interface Tool {
  id: string; 
  nome: string;
  url_base: string;
  descricao?: string;
}

const Tools: React.FC = () => {
  const { token, user } = useAuth(); // user can be used for UI elements if needed
  const [availableTools, setAvailableTools] = useState<Tool[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const fetchUserTools = useCallback(async () => {
    if (!token) { 
      setError("Usuário não autenticado.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError('');
    setAvailableTools([]);

    try {
      // Directly fetch tools available to the user using the new endpoint
      const response = await fetchWithAuth('/tools/user_tools', token);
      if (!response.ok) {
        const errorData = await getErrorBody(response);
        throw new Error(errorData.detail || 'Falha ao buscar ferramentas do usuário.');
      }
      const tools: Tool[] = await response.json();
      setAvailableTools(tools);

    } catch (err: any) {
      setError(err.message || 'Erro desconhecido ao buscar ferramentas.');
      setAvailableTools([]);
    } finally {
      setIsLoading(false);
    }
  // Removed user from dependencies as direct user details are not needed for this specific fetch call
  // The token itself implies the user context for the backend.
  }, [token]); 

  useEffect(() => {
    fetchUserTools();
  }, [fetchUserTools]);

  const handleAccessTool = (tool: Tool) => {
    if (tool.url_base) {
      // Assuming url_base is a full URL. 
      // If it's a relative path, it might need to be prefixed.
      // For security, ensure URLs are validated or handled appropriately if they are user-defined.
      window.open(tool.url_base, '_blank');
    } else {
      alert(`A ferramenta ${tool.nome} não possui uma URL configurada.`);
    }
  };

  return (
    <div className="card">
      <h2>Ferramentas Disponíveis</h2>
      {isLoading && <p>Carregando ferramentas...</p>}
      {error && <div className="error-message message-spacing">{error}</div>}
      {!isLoading && !error && availableTools.length === 0 && (
        <p>Nenhuma ferramenta disponível para você no momento. Verifique seus grupos ou contate um administrador.</p>
      )}
      {!isLoading && !error && availableTools.length > 0 && (
        <ul className="list-group">
          {availableTools.map(tool => (
            // Using tool.id as the key, which is guaranteed by ToolResponseSchema
            <li key={tool.id} className="list-group-item tool-item">
              <div>
                <strong>{tool.nome}</strong>
                {tool.descricao && <p>{tool.descricao}</p>}
              </div>
              {/* Ensure user is still checked if the button should only show for authenticated users,
                  though being on this page usually implies authentication via ProtectedRoute. */}
              {user && (
                <button onClick={() => handleAccessTool(tool)} className="button-small">
                  Acessar
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Tools;
