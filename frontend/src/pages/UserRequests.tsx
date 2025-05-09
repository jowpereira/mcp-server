import React, { useEffect, useState } from 'react';
import '../App.css';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../utils/api';
import { useApiError } from '../utils/errorHandling';
import useLoading from '../hooks/useLoading';
import LoadingSpinner from '../components/LoadingSpinner';

// Interface para o formato de solicitação de acesso a grupo
interface AccessRequest {
  request_id: string;
  username: string;
  grupo: string;
  status: 'pending' | 'approved' | 'rejected';
  justificativa: string;
  created_at: string;
  updated_at: string | null;
  reviewed_by: string | null;
  review_comment: string | null;
}

// Interface para o formato do formulário de solicitação
interface RequestFormData {
  grupo: string;
  justificativa: string;
}

const UserRequests: React.FC = () => {
  const { token, user } = useAuth();
  const { isLoading, error, execute } = useLoading();
  const { processApiResponse, handleApiError } = useApiError();
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [availableGroups, setAvailableGroups] = useState<string[]>([]);
  const [formData, setFormData] = useState<RequestFormData>({
    grupo: '',
    justificativa: '',
  });
  const [showForm, setShowForm] = useState(false);

  // Busca as solicitações do usuário atual
  const fetchUserRequests = async () => {
    if (!token) return;

    try {
      const result = await execute(fetchWithAuth('/tools/requests/me', token));
      
      if (!result) return;
      
      const hasError = await processApiResponse(result);
      if (hasError) return;
      
      const data: AccessRequest[] = await result.json();
      setRequests(data);
    } catch (err: any) {
      handleApiError(err);
    }
  };

  // Busca grupos disponíveis para solicitar acesso
  const fetchAvailableGroups = async () => {
    if (!token) return;

    try {
      const result = await execute(fetchWithAuth('/tools/grupos/disponivel', token));
      
      if (!result) return;
      
      const hasError = await processApiResponse(result);
      if (hasError) return;
      
      const data = await result.json();
      setAvailableGroups(data.grupos || []);
    } catch (err: any) {
      handleApiError(err);
    }
  };

  // Enviar solicitação de acesso
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token) return;
    
    try {
      const result = await execute(fetchWithAuth('/tools/requests', token, {
        method: 'POST',
        body: JSON.stringify(formData),
        headers: {
          'Content-Type': 'application/json'
        }
      }));
      
      if (!result) return;
      
      const hasError = await processApiResponse(result);
      if (hasError) return;
      
      // Limpar formulário e recarregar solicitações
      setFormData({ grupo: '', justificativa: '' });
      setShowForm(false);
      fetchUserRequests();
    } catch (err: any) {
      handleApiError(err);
    }
  };

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  useEffect(() => {
    if (token && user) {
      fetchUserRequests();
      fetchAvailableGroups();
    }
  }, [token, user]);

  // Renderiza status com cores
  const renderStatus = (status: string) => {
    switch (status) {
      case 'approved':
        return <span className="status approved">Aprovado</span>;
      case 'rejected':
        return <span className="status rejected">Rejeitado</span>;
      default:
        return <span className="status pending">Pendente</span>;
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Carregando solicitações..." />;
  }

  return (
    <div className="card user-requests-page">
      <h2>Minhas Solicitações de Acesso</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="action-bar">
        <button 
          className="primary-button"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancelar' : 'Nova Solicitação'}
        </button>
      </div>
      
      {showForm && (
        <div className="request-form card">
          <h3>Solicitar Acesso a Grupo</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="grupo">Grupo</label>
              <select 
                id="grupo"
                name="grupo"
                value={formData.grupo}
                onChange={handleInputChange}
                required
              >
                <option value="">Selecione um grupo</option>
                {availableGroups.map(group => (
                  <option key={group} value={group}>{group}</option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="justificativa">Justificativa</label>
              <textarea 
                id="justificativa"
                name="justificativa"
                value={formData.justificativa}
                onChange={handleInputChange}
                placeholder="Explique por que você precisa de acesso a este grupo"
                required
                rows={4}
                minLength={5}
                maxLength={500}
              />
            </div>
            
            <div className="button-group">
              <button type="submit" className="primary-button">Enviar Solicitação</button>
            </div>
          </form>
        </div>
      )}
      
      {requests.length === 0 ? (
        <p className="info-message">Você não possui solicitações de acesso pendentes ou realizadas.</p>
      ) : (
        <div className="request-list">
          <h3>Suas Solicitações</h3>
          {requests.map((req) => (
            <div key={req.request_id} className="request-item card">
              <div className="request-header">
                <h4>Grupo: {req.grupo}</h4>
                {renderStatus(req.status)}
              </div>
              
              <div className="request-details">
                <p><strong>Solicitado em:</strong> {new Date(req.created_at).toLocaleString()}</p>
                <p><strong>Justificativa:</strong> {req.justificativa}</p>
                
                {req.status !== 'pending' && (
                  <>
                    <p><strong>Revisado por:</strong> {req.reviewed_by || 'N/A'}</p>
                    <p><strong>Revisado em:</strong> {req.updated_at ? new Date(req.updated_at).toLocaleString() : 'N/A'}</p>
                    {req.review_comment && (
                      <p><strong>Comentário:</strong> {req.review_comment}</p>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UserRequests;
