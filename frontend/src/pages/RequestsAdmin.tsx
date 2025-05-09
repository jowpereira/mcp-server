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

// Interface para o formulário de revisão
interface ReviewFormData {
  status: 'approved' | 'rejected';
  comment: string;
}

const RequestsAdmin: React.FC = () => {
  const { token, user } = useAuth();
  const { isLoading, error, execute } = useLoading();
  const { processApiResponse, handleApiError } = useApiError();
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<AccessRequest | null>(null);
  const [formData, setFormData] = useState<ReviewFormData>({
    status: 'approved',
    comment: ''
  });

  // Busca as solicitações pendentes para review
  const fetchPendingRequests = async () => {
    if (!token) return;

    try {
      const result = await execute(fetchWithAuth('/tools/requests/admin', token));
      
      if (!result) return;
      
      const hasError = await processApiResponse(result);
      if (hasError) return;
      
      const data: AccessRequest[] = await result.json();
      setRequests(data);
    } catch (err: any) {
      handleApiError(err);
    }
  };

  // Enviar revisão de solicitação
  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token || !selectedRequest) return;
    
    try {
      const result = await execute(fetchWithAuth(`/tools/requests/${selectedRequest.request_id}/review`, token, {
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
      setFormData({ status: 'approved', comment: '' });
      setSelectedRequest(null);
      fetchPendingRequests();
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
      fetchPendingRequests();
    }
  }, [token, user]);

  if (isLoading) {
    return <LoadingSpinner message="Carregando solicitações pendentes..." />;
  }

  return (
    <div className="card requests-admin-page">
      <h2>Solicitações de Acesso Pendentes</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      {requests.length === 0 ? (
        <p className="info-message">Não há solicitações de acesso pendentes para revisão.</p>
      ) : (
        <div className="request-list">
          {requests.map((req) => (
            <div key={req.request_id} className="request-item card">
              <div className="request-header">
                <h4>Grupo: {req.grupo}</h4>
                <span className="status pending">Pendente</span>
              </div>
              
              <div className="request-details">
                <p><strong>Usuário:</strong> {req.username}</p>
                <p><strong>Solicitado em:</strong> {new Date(req.created_at).toLocaleString()}</p>
                <p><strong>Justificativa:</strong> {req.justificativa}</p>
              </div>
              
              <div className="request-actions">
                <button 
                  className="button secondary-button"
                  onClick={() => setSelectedRequest(req)}
                >
                  Analisar Solicitação
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {selectedRequest && (
        <div className="modal-overlay">
          <div className="modal-content review-modal">
            <div className="modal-header">
              <h3>Revisar Solicitação</h3>
              <button className="close-button" onClick={() => setSelectedRequest(null)}>×</button>
            </div>
            
            <div className="modal-body">
              <div className="request-summary">
                <p><strong>Usuário:</strong> {selectedRequest.username}</p>
                <p><strong>Grupo:</strong> {selectedRequest.grupo}</p>
                <p><strong>Data:</strong> {new Date(selectedRequest.created_at).toLocaleString()}</p>
                <p><strong>Justificativa:</strong> {selectedRequest.justificativa}</p>
              </div>
              
              <form onSubmit={handleSubmitReview}>
                <div className="form-group">
                  <label htmlFor="status">Decisão</label>
                  <select 
                    id="status"
                    name="status"
                    value={formData.status}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="approved">Aprovar</option>
                    <option value="rejected">Rejeitar</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label htmlFor="comment">Comentário (opcional)</label>
                  <textarea 
                    id="comment"
                    name="comment"
                    value={formData.comment}
                    onChange={handleInputChange}
                    placeholder="Explique a razão da sua decisão (opcional)"
                    rows={3}
                    maxLength={500}
                  />
                </div>
                
                <div className="button-group">
                  <button type="button" className="secondary-button" onClick={() => setSelectedRequest(null)}>Cancelar</button>
                  <button type="submit" className={formData.status === 'approved' ? 'approve-button' : 'reject-button'}>
                    {formData.status === 'approved' ? 'Aprovar' : 'Rejeitar'} Solicitação
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RequestsAdmin;
