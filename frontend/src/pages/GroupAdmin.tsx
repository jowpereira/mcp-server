import React, { useEffect, useState, useCallback } from 'react';
import '../App.css';
import { fetchWithAuth, getErrorBody } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface Tool {
  id: string; // Corresponds to the key in rbac.json ferramentas definition
  nome: string;
  url_base: string;
  descricao?: string;
}

interface Group {
  id: string; // group name, used as key
  nome: string;
  descricao: string;
  administradores: string[];
  usuarios: string[]; // Changed from 'utilizadores' to 'usuarios' to match backend
  ferramentas_disponiveis: Tool[]; // Tools available to this specific group
}

interface ActionMessage {
  type: 'success' | 'error';
  text: string;
}

const GroupAdmin: React.FC = () => {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [groups, setGroups] = useState<Group[]>([]);
  const [isLoadingGroups, setIsLoadingGroups] = useState<boolean>(false);
  const [fetchGroupsError, setFetchGroupsError] = useState<string>('');
  
  const [showCreateGroupModal, setShowCreateGroupModal] = useState<boolean>(false);
  const [newGroupName, setNewGroupName] = useState<string>('');
  const [newGroupDescription, setNewGroupDescription] = useState<string>('');
  const [isCreatingGroup, setIsCreatingGroup] = useState<boolean>(false);
  const [createGroupError, setCreateGroupError] = useState<string>('');

  const [actionMessage, setActionMessage] = useState<ActionMessage | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);

  const [showEditGroupModal, setShowEditGroupModal] = useState<boolean>(false);
  const [editingGroup, setEditingGroup] = useState<Group | null>(null);
  const [editGroupName, setEditGroupName] = useState<string>('');
  const [editGroupDescription, setEditGroupDescription] = useState<string>('');
  const [isUpdatingGroup, setIsUpdatingGroup] = useState<boolean>(false);
  const [editGroupError, setEditGroupError] = useState<string>('');

  const [showManageUserModal, setShowManageUserModal] = useState<boolean>(false);
  const [userToManage, setUserToManage] = useState<string>('');
  const [isManagingUser, setIsManagingUser] = useState<boolean>(false);
  const [manageUserError, setManageUserError] = useState<string>('');

  const [showManageToolModal, setShowManageToolModal] = useState<boolean>(false);
  const [toolToManage, setToolToManage] = useState<string>(''); // tool ID
  const [isManagingTool, setIsManagingTool] = useState<boolean>(false);
  const [manageToolError, setManageToolError] = useState<string>('');

  const [allGlobalTools, setAllGlobalTools] = useState<Tool[]>([]); // For Add Tool Modal
  const [isLoadingGlobalTools, setIsLoadingGlobalTools] = useState<boolean>(false);

  const [isPerformingGroupAction, setIsPerformingGroupAction] = useState<boolean>(false);

  const clearActionMessage = useCallback(() => {
    setTimeout(() => setActionMessage(null), 5000);
  }, []);

  const fetchAllGlobalTools = useCallback(async () => {
    if (!token) return;
    setIsLoadingGlobalTools(true);
    try {
      const response = await fetchWithAuth('/ferramentas', token);
      if (!response.ok) {
        const errorData = await getErrorBody(response);
        throw new Error(errorData.detail || 'Falha ao buscar ferramentas globais.');
      }
      const data: Tool[] = await response.json();
      setAllGlobalTools(data);
    } catch (err: any) {
      setActionMessage({ type: 'error', text: `Erro ao buscar ferramentas globais: ${err.message}` });
      setAllGlobalTools([]);
      clearActionMessage();
    } finally {
      setIsLoadingGlobalTools(false);
    }
  }, [token, clearActionMessage]);

  const fetchGroups = useCallback(async (selectGroupId?: string) => {
    if (!token) return;
    setIsLoadingGroups(true);
    setFetchGroupsError('');
    try {
      // Endpoint changed to /grupos which returns more details including tools with full definitions
      const response = await fetchWithAuth('/grupos', token);
      if (!response.ok) {
        const errorData = await getErrorBody(response);
        throw new Error(errorData.detail || 'Falha ao buscar grupos.');
      }
      const data: Group[] = await response.json();
      setGroups(data);
      if (selectGroupId) {
        const groupToSelect = data.find(g => g.id === selectGroupId);
        setSelectedGroup(groupToSelect || null);
      } else if (selectedGroup) {
        const refreshedSelectedGroup = data.find(g => g.id === selectedGroup.id);
        setSelectedGroup(refreshedSelectedGroup || null);
      }
    } catch (err: any) {
      setFetchGroupsError(err.message || 'Erro desconhecido ao buscar grupos.');
      setGroups([]);
      setSelectedGroup(null);
      setActionMessage({ type: 'error', text: `Erro ao buscar grupos: ${err.message}` });
      clearActionMessage();
    } finally {
      setIsLoadingGroups(false);
    }
  }, [token, selectedGroup, clearActionMessage]); // Added selectedGroup and clearActionMessage

  useEffect(() => {
    if (user && (user.papel === 'global_admin' || user.papel === 'admin')) {
      fetchGroups();
      fetchAllGlobalTools();
    } else {
      navigate('/dashboard');
    }
  }, [token, user, navigate, fetchGroups, fetchAllGlobalTools]);

  // Simplified authorization check
  if (!user || (user.papel !== 'global_admin' && user.papel !== 'admin')) {
    return <p>Acesso não autorizado. Você precisa ser um administrador de grupo ou administrador global.</p>;
  }

  const handleOpenCreateGroupModal = () => {
    if (user?.papel !== 'global_admin') {
        setActionMessage({ type: 'error', text: 'Apenas administradores globais podem criar grupos.' });
        clearActionMessage();
        return;
    }
    setNewGroupName('');
    setNewGroupDescription('');
    setCreateGroupError('');
    setShowCreateGroupModal(true);
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (user?.papel !== 'global_admin') {
      setCreateGroupError('Ação não permitida.');
      return;
    }
    if (!newGroupName.trim()) {
      setCreateGroupError('Nome do grupo é obrigatório.');
      return;
    }
    setIsCreatingGroup(true);
    setCreateGroupError('');
    setActionMessage(null);
    setIsPerformingGroupAction(true);

    try {
      const response = await fetchWithAuth('/grupos', token, {
        method: 'POST',
        body: JSON.stringify({ nome: newGroupName, descricao: newGroupDescription || '' }),
      });
      const responseData = await response.json();

      if (!response.ok) {
        const errorDetail = responseData.detail || 'Falha ao criar grupo.';
        throw new Error(errorDetail);
      }
      setActionMessage({ type: 'success', text: responseData.message || 'Grupo criado com sucesso!' });
      setShowCreateGroupModal(false);
      fetchGroups(); 
    } catch (err: any) {
      setCreateGroupError(err.message || 'Erro desconhecido ao criar grupo.');
      setActionMessage({ type: 'error', text: err.message || 'Erro desconhecido ao criar grupo.' });
    } finally {
      setIsCreatingGroup(false);
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleOpenEditGroupModal = (group: Group) => {
    if (user?.papel !== 'global_admin') {
        setActionMessage({ type: 'error', text: 'Apenas administradores globais podem editar grupos.' });
        clearActionMessage();
        return;
    }
    setEditingGroup(group);
    setEditGroupName(group.nome);
    setEditGroupDescription(group.descricao);
    setEditGroupError('');
    setShowEditGroupModal(true);
  };

  const handleUpdateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (user?.papel !== 'global_admin') {
        setEditGroupError('Ação não permitida.');
        return;
    }
    if (!editingGroup || !editGroupName.trim()) {
      setEditGroupError('Nome do grupo é obrigatório.');
      return;
    }
    setIsUpdatingGroup(true);
    setEditGroupError('');
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/grupos/${editingGroup.id}`, token, {
        method: 'PUT',
        body: JSON.stringify({ nome: editGroupName, descricao: editGroupDescription || '' }),
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao atualizar grupo.');
      setActionMessage({ type: 'success', text: responseData.message || 'Grupo atualizado com sucesso!' });
      setShowEditGroupModal(false);
      fetchGroups(editingGroup.id); 
    } catch (err: any) {
      setEditGroupError(err.message);
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsUpdatingGroup(false);
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleDeleteGroup = async (groupId: string) => {
    if (user?.papel !== 'global_admin') {
      setActionMessage({ type: 'error', text: 'Apenas administradores globais podem excluir grupos.' });
      clearActionMessage();
      return;
    }
    if (!window.confirm('Tem certeza que deseja excluir este grupo? Esta ação não pode ser desfeita.')) return;
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/grupos/${groupId}`, token, { method: 'DELETE' });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao excluir grupo.');
      setActionMessage({ type: 'success', text: responseData.message || 'Grupo excluído com sucesso!' });
      setSelectedGroup(null); 
      fetchGroups();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleOpenManageUserModal = (username: string = '') => {
    setUserToManage(username);
    setManageUserError('');
    setShowManageUserModal(true);
  };

  const handleAddUserToGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGroup || !userToManage.trim()) {
      setManageUserError('Nome de usuário é obrigatório.');
      return;
    }
    setIsManagingUser(true);
    setManageUserError('');
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/grupos/${selectedGroup.id}/usuarios`, token, {
        method: 'POST',
        body: JSON.stringify({ username: userToManage.trim() }),
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao adicionar usuário ao grupo.');
      setActionMessage({ type: 'success', text: responseData.message || 'Usuário adicionado ao grupo!' });
      setShowManageUserModal(false);
      fetchGroups(selectedGroup.id);
    } catch (err: any) {
      setManageUserError(err.message);
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsManagingUser(false);
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleRemoveUserFromGroup = async (usernameToRemove: string) => {
    if (!selectedGroup) return;
    if (!window.confirm(`Tem certeza que deseja remover ${usernameToRemove} do grupo ${selectedGroup.nome}?`)) return;
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/grupos/${selectedGroup.id}/usuarios/${usernameToRemove}`, token, { 
        method: 'DELETE',
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao remover usuário do grupo.');
      setActionMessage({ type: 'success', text: responseData.message || 'Usuário removido do grupo!' });
      fetchGroups(selectedGroup.id);
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handlePromoteToAdmin = async (usernameToPromote: string) => {
    if (!selectedGroup) return;
    if (user?.papel !== 'global_admin') {
        setActionMessage({ type: 'error', text: 'Apenas administradores globais podem promover usuários a administradores de grupo.' });
        clearActionMessage();
        return;
    }
    if (!window.confirm(`Tem certeza que deseja promover ${usernameToPromote} a administrador do grupo ${selectedGroup.nome}?`)) return;
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/grupos/${selectedGroup.id}/admins`, token, {
        method: 'POST',
        body: JSON.stringify({ username: usernameToPromote }),
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao promover usuário a admin.');
      setActionMessage({ type: 'success', text: responseData.message || 'Usuário promovido a admin!' });
      fetchGroups(selectedGroup.id);
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleDemoteAdmin = async (adminUsernameToDemote: string) => {
    if (!selectedGroup) return;
    if (user?.papel !== 'global_admin') {
        setActionMessage({ type: 'error', text: 'Apenas administradores globais podem remover administradores de grupo.' });
        clearActionMessage();
        return;
    }
    if (selectedGroup.administradores.length <= 1 && adminUsernameToDemote === selectedGroup.administradores[0]) {
        setActionMessage({ type: 'error', text: 'Não é possível remover o último administrador do grupo.' });
        clearActionMessage();
        return;
    }
    if (!window.confirm(`Tem certeza que deseja remover ${adminUsernameToDemote} como administrador do grupo ${selectedGroup.nome}?`)) return;
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/grupos/${selectedGroup.id}/admins/${adminUsernameToDemote}`, token, {
        method: 'DELETE',
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao remover admin do grupo.');
      setActionMessage({ type: 'success', text: responseData.message || 'Admin removido do grupo!' });
      fetchGroups(selectedGroup.id);
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleOpenManageToolModal = (toolId: string = '') => {
    setToolToManage(toolId);
    setManageToolError('');
    setShowManageToolModal(true);
  };

  const handleAddToolToGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGroup || !toolToManage) {
      setManageToolError('ID da ferramenta é obrigatório.');
      return;
    }
    setIsManagingTool(true);
    setManageToolError('');
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/grupos/${selectedGroup.id}/ferramentas`, token, {
        method: 'POST',
        body: JSON.stringify({ tool_id: toolToManage }),
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao adicionar ferramenta ao grupo.');
      setActionMessage({ type: 'success', text: responseData.message || 'Ferramenta adicionada ao grupo!' });
      setShowManageToolModal(false);
      fetchGroups(selectedGroup.id);
    } catch (err: any) {
      setManageToolError(err.message);
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsManagingTool(false);
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleRemoveToolFromGroup = async (toolIdToRemove: string) => {
    if (!selectedGroup) return;
    if (!window.confirm(`Tem certeza que deseja remover a ferramenta ${allGlobalTools.find(t=>t.id === toolIdToRemove)?.nome || toolIdToRemove} do grupo ${selectedGroup.nome}?`)) return;
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/grupos/${selectedGroup.id}/ferramentas/${toolIdToRemove}`, token, {
        method: 'DELETE',
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao remover ferramenta do grupo.');
      setActionMessage({ type: 'success', text: responseData.message || 'Ferramenta removida do grupo!' });
      fetchGroups(selectedGroup.id);
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const getAvailableToolsForGroup = () => {
    if (!selectedGroup) return [];
    const groupToolIds = selectedGroup.ferramentas_disponiveis.map(t => t.id);
    return allGlobalTools.filter(tool => !groupToolIds.includes(tool.id));
  };

  return (
    <div className="container">
      <h2>Gerenciamento de Grupos</h2>
      {actionMessage && (
        <div className={`action-message ${actionMessage.type}`}>
          {actionMessage.text}
        </div>
      )}

      {user?.papel === 'global_admin' && (
        <button onClick={handleOpenCreateGroupModal} className="button-primary" disabled={isPerformingGroupAction}>
          Criar Novo Grupo
        </button>
      )}

      {isLoadingGroups && <p>Carregando grupos...</p>}
      {fetchGroupsError && <p className="error-message">{fetchGroupsError}</p>}

      {!isLoadingGroups && groups.length === 0 && !fetchGroupsError && (
        <p>Nenhum grupo encontrado.</p>
      )}

      {groups.length > 0 && (
        <div className="groups-list">
          <h3>Grupos Existentes:</h3>
          <ul>
            {groups.map((group) => (
              <li key={group.id} onClick={() => setSelectedGroup(group)} className={selectedGroup?.id === group.id ? 'selected' : ''}>
                {group.nome} ({group.id})
                {user?.papel === 'global_admin' && (
                    <>
                        <button onClick={(e) => { e.stopPropagation(); handleOpenEditGroupModal(group); }} className="button-secondary button-small" disabled={isPerformingGroupAction}>Editar</button>
                        <button onClick={(e) => { e.stopPropagation(); handleDeleteGroup(group.id); }} className="button-danger button-small" disabled={isPerformingGroupAction}>Excluir</button>
                    </>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {selectedGroup && (
        <div className="group-details-card">
          <h3>Detalhes do Grupo: {selectedGroup.nome}</h3>
          <p><strong>ID:</strong> {selectedGroup.id}</p>
          <p><strong>Descrição:</strong> {selectedGroup.descricao || 'N/A'}</p>
          
          {/* Gerenciamento de Administradores */}
          <h4>Administradores:</h4>
          {selectedGroup.administradores.length > 0 ? (
            <ul>
              {selectedGroup.administradores.map(admin => (
                <li key={admin}>{admin}
                  {user?.papel === 'global_admin' && (
                    <button onClick={() => handleDemoteAdmin(admin)} className="button-danger button-small" disabled={isPerformingGroupAction || selectedGroup.administradores.length <= 1 && admin === selectedGroup.administradores[0]}>
                      Remover Admin
                    </button>
                  )}
                </li>
              ))}
            </ul>
          ) : <p>Nenhum administrador neste grupo.</p>}
          {/* Botão para promover usuário a admin (global admin only) - aparece se houver usuários para promover */}
          {user?.papel === 'global_admin' && selectedGroup.usuarios.filter(u => !selectedGroup.administradores.includes(u)).length > 0 && (
            <div>
              <label htmlFor="promoteAdminSelect">Promover Usuário a Admin: </label>
              <select 
                id="promoteAdminSelect"
                onChange={(e) => handlePromoteToAdmin(e.target.value)} 
                value="" 
                disabled={isPerformingGroupAction}
              >
                <option value="" disabled>Selecione um usuário...</option>
                {selectedGroup.usuarios
                  .filter(u => !selectedGroup.administradores.includes(u))
                  .map(u => <option key={u} value={u}>{u}</option>)
                }
              </select>
            </div>
          )}

          {/* Gerenciamento de Usuários */}
          <h4>Usuários:</h4>
          {selectedGroup.usuarios.length > 0 ? (
            <ul>
              {selectedGroup.usuarios.map(username => (
                <li key={username}>{username}
                  {(user?.papel === 'global_admin' || (user?.papel === 'admin' && selectedGroup.administradores.includes(user.username || ''))) && (
                    <button onClick={() => handleRemoveUserFromGroup(username)} className="button-danger button-small" disabled={isPerformingGroupAction || selectedGroup.administradores.includes(username)}>
                      Remover Usuário
                    </button>
                  )}
                </li>
              ))}
            </ul>
          ) : <p>Nenhum usuário neste grupo.</p>}
          {(user?.papel === 'global_admin' || (user?.papel === 'admin' && selectedGroup.administradores.includes(user.username || ''))) && (
            <button onClick={() => handleOpenManageUserModal()} className="button-secondary" disabled={isPerformingGroupAction}>Adicionar Usuário ao Grupo</button>
          )}

          {/* Gerenciamento de Ferramentas */}
          <h4>Ferramentas Disponíveis:</h4>
          {selectedGroup.ferramentas_disponiveis.length > 0 ? (
            <ul>
              {selectedGroup.ferramentas_disponiveis.map(tool => (
                <li key={tool.id}>{tool.nome} ({tool.id}) - {tool.descricao || 'Sem descrição'}
                  {(user?.papel === 'global_admin' || (user?.papel === 'admin' && selectedGroup.administradores.includes(user.username || ''))) && (
                    <button onClick={() => handleRemoveToolFromGroup(tool.id)} className="button-danger button-small" disabled={isPerformingGroupAction}>
                      Remover Ferramenta
                    </button>
                  )}
                </li>
              ))}
            </ul>
          ) : <p>Nenhuma ferramenta atribuída a este grupo.</p>}
          {(user?.papel === 'global_admin' || (user?.papel === 'admin' && selectedGroup.administradores.includes(user.username || ''))) && getAvailableToolsForGroup().length > 0 && (
            <button onClick={() => handleOpenManageToolModal()} className="button-secondary" disabled={isPerformingGroupAction || isLoadingGlobalTools}>
              Adicionar Ferramenta ao Grupo
            </button>
          )}
          {isLoadingGlobalTools && <p>Carregando ferramentas globais...</p>}
        </div>
      )}

      {/* Modal de Criação de Grupo */}
      {showCreateGroupModal && (
        <div className="modal">
          <div className="modal-content">
            <span className="close-button" onClick={() => setShowCreateGroupModal(false)}>&times;</span>
            <h3>Criar Novo Grupo</h3>
            <form onSubmit={handleCreateGroup}>
              <div>
                <label htmlFor="newGroupName">Nome do Grupo:</label>
                <input 
                  type="text" 
                  id="newGroupName" 
                  value={newGroupName} 
                  onChange={(e) => setNewGroupName(e.target.value)} 
                  required 
                />
              </div>
              <div>
                <label htmlFor="newGroupDescription">Descrição:</label>
                <textarea 
                  id="newGroupDescription" 
                  value={newGroupDescription} 
                  onChange={(e) => setNewGroupDescription(e.target.value)} 
                />
              </div>
              {createGroupError && <p className="error-message">{createGroupError}</p>}
              <button type="submit" className="button-primary" disabled={isCreatingGroup || isPerformingGroupAction}>
                {isCreatingGroup ? 'Criando...' : 'Criar Grupo'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Edição de Grupo */}
      {showEditGroupModal && editingGroup && (
        <div className="modal">
          <div className="modal-content">
            <span className="close-button" onClick={() => setShowEditGroupModal(false)}>&times;</span>
            <h3>Editar Grupo: {editingGroup.nome}</h3>
            <form onSubmit={handleUpdateGroup}>
              <div>
                <label htmlFor="editGroupName">Novo Nome do Grupo:</label>
                <input 
                  type="text" 
                  id="editGroupName" 
                  value={editGroupName} 
                  onChange={(e) => setEditGroupName(e.target.value)} 
                  required 
                />
              </div>
              <div>
                <label htmlFor="editGroupDescription">Nova Descrição:</label>
                <textarea 
                  id="editGroupDescription" 
                  value={editGroupDescription} 
                  onChange={(e) => setEditGroupDescription(e.target.value)} 
                />
              </div>
              {editGroupError && <p className="error-message">{editGroupError}</p>}
              <button type="submit" className="button-primary" disabled={isUpdatingGroup || isPerformingGroupAction}>
                {isUpdatingGroup ? 'Atualizando...' : 'Atualizar Grupo'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Gerenciamento de Usuário (Adicionar) */}
      {showManageUserModal && selectedGroup && (
        <div className="modal">
          <div className="modal-content">
            <span className="close-button" onClick={() => setShowManageUserModal(false)}>&times;</span>
            <h3>Adicionar Usuário ao Grupo: {selectedGroup.nome}</h3>
            <form onSubmit={handleAddUserToGroup}>
              <div>
                <label htmlFor="userToManage">Nome do Usuário:</label>
                <input 
                  type="text" 
                  id="userToManage" 
                  value={userToManage} 
                  onChange={(e) => setUserToManage(e.target.value)} 
                  required 
                  placeholder="Digite o username"
                />
              </div>
              {manageUserError && <p className="error-message">{manageUserError}</p>}
              <button type="submit" className="button-primary" disabled={isManagingUser || isPerformingGroupAction}>
                {isManagingUser ? 'Adicionando...' : 'Adicionar Usuário'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Gerenciamento de Ferramenta (Adicionar) */}
      {showManageToolModal && selectedGroup && (
        <div className="modal">
          <div className="modal-content">
            <span className="close-button" onClick={() => setShowManageToolModal(false)}>&times;</span>
            <h3>Adicionar Ferramenta ao Grupo: {selectedGroup.nome}</h3>
            {isLoadingGlobalTools ? <p>Carregando ferramentas...</p> : (
              <form onSubmit={handleAddToolToGroup}>
                <div>
                  <label htmlFor="toolToManage">Selecione a Ferramenta:</label>
                  <select 
                    id="toolToManage" 
                    value={toolToManage} 
                    onChange={(e) => setToolToManage(e.target.value)} 
                    required
                  >
                    <option value="" disabled>Selecione uma ferramenta...</option>
                    {getAvailableToolsForGroup().map(tool => (
                      <option key={tool.id} value={tool.id}>{tool.nome} ({tool.id})</option>
                    ))}
                  </select>
                </div>
                {getAvailableToolsForGroup().length === 0 && <p>Nenhuma ferramenta nova para adicionar ou todas já foram adicionadas.</p>}
                {manageToolError && <p className="error-message">{manageToolError}</p>}
                <button type="submit" className="button-primary" disabled={isManagingTool || isPerformingGroupAction || getAvailableToolsForGroup().length === 0}>
                  {isManagingTool ? 'Adicionando...' : 'Adicionar Ferramenta'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default GroupAdmin;
