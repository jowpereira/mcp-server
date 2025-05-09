import React, { useEffect, useState, useCallback } from 'react';
import '../App.css';
import { fetchWithAuth, getErrorBody } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface Tool {
  id: string;
  nome: string;
  url_base: string;
  descricao?: string;
}

interface Group {
  id: string;
  nome: string;
  descricao: string;
  administradores: string[];
  usuarios: string[];
  ferramentas_disponiveis: Tool[];
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

  // Selected group for detailed management
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);

  // State for Edit Group Modal
  const [showEditGroupModal, setShowEditGroupModal] = useState<boolean>(false);
  const [editingGroup, setEditingGroup] = useState<Group | null>(null);
  const [editGroupName, setEditGroupName] = useState<string>('');
  const [editGroupDescription, setEditGroupDescription] = useState<string>('');
  const [isUpdatingGroup, setIsUpdatingGroup] = useState<boolean>(false);
  const [editGroupError, setEditGroupError] = useState<string>('');

  // State for Add Admin Modal
  const [showAddAdminModal, setShowAddAdminModal] = useState<boolean>(false);
  const [newAdminUsername, setNewAdminUsername] = useState<string>('');
  const [isAddingAdmin, setIsAddingAdmin] = useState<boolean>(false);
  const [addAdminError, setAddAdminError] = useState<string>('');

  // State for Add User Modal
  const [showAddUserModal, setShowAddUserModal] = useState<boolean>(false);
  const [newUserUsername, setNewUserUsername] = useState<string>('');
  const [isAddingUser, setIsAddingUser] = useState<boolean>(false);
  const [addUserError, setAddUserError] = useState<string>('');

  // State for Add Tool Modal
  const [showAddToolModal, setShowAddToolModal] = useState<boolean>(false);
  const [newToolName, setNewToolName] = useState<string>('');
  const [isAddingTool, setIsAddingTool] = useState<boolean>(false);
  const [addToolError, setAddToolError] = useState<string>('');

  const [isPerformingGroupAction, setIsPerformingGroupAction] = useState<boolean>(false);

  const clearActionMessage = useCallback(() => {
    setTimeout(() => setActionMessage(null), 3000);
  }, []);

  const fetchGroups = useCallback(async (selectGroupId?: string) => {
    if (!token) return;
    setIsLoadingGroups(true);
    setFetchGroupsError('');
    try {
      const response = await fetchWithAuth('/tools/grupos', token);
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
        // Se um grupo estava selecionado, atualize seus detalhes
        const refreshedSelectedGroup = data.find(g => g.id === selectedGroup.id);
        setSelectedGroup(refreshedSelectedGroup || null);
      }
    } catch (err: any) {
      setFetchGroupsError(err.message || 'Erro desconhecido ao buscar grupos.');
      setGroups([]);
      setSelectedGroup(null);
    } finally {
      setIsLoadingGroups(false);
    }
  }, [token]); // Removido selectedGroup das dependências

  useEffect(() => {
    fetchGroups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]); // Só depende do token, executa ao montar ou trocar de usuário

  useEffect(() => {
    if (user && user.papel !== 'global_admin') {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  if (!user || user.papel !== 'global_admin') {
    return <p>Acesso não autorizado.</p>;
  }

  const handleOpenCreateGroupModal = () => {
    setNewGroupName('');
    setNewGroupDescription('');
    setCreateGroupError('');
    setShowCreateGroupModal(true);
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || user.papel !== 'global_admin') {
      setCreateGroupError('Ação não permitida.');
      return;
    }
    if (!newGroupName.trim() || !newGroupDescription.trim()) {
      setCreateGroupError('Nome e descrição são obrigatórios.');
      return;
    }
    setIsCreatingGroup(true);
    setCreateGroupError('');
    setActionMessage(null);
    setIsPerformingGroupAction(true);

    try {
      const response = await fetchWithAuth('/tools/grupos', token, {
        method: 'POST',
        body: JSON.stringify({ nome: newGroupName, descricao: newGroupDescription }),
      });
      const responseData = await response.json();

      if (!response.ok) {
        const errorDetail = responseData.detail || 'Falha ao criar grupo.';
        throw new Error(errorDetail);
      }
      setActionMessage({ type: 'success', text: responseData.mensagem || 'Grupo criado com sucesso!' });
      setShowCreateGroupModal(false);
      fetchGroups(); // Refresh the list of groups
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
    setEditingGroup(group);
    setEditGroupName(group.nome);
    setEditGroupDescription(group.descricao);
    setEditGroupError('');
    setShowEditGroupModal(true);
  };

  const handleUpdateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGroup || !editGroupName.trim() || !editGroupDescription.trim()) {
      setEditGroupError('Nome e descrição são obrigatórios.');
      return;
    }
    setIsUpdatingGroup(true);
    setEditGroupError('');
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/tools/grupos/${editingGroup.id}`, token, {
        method: 'PUT',
        body: JSON.stringify({ nome: editGroupName, descricao: editGroupDescription }),
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao atualizar grupo.');
      setActionMessage({ type: 'success', text: responseData.mensagem || 'Grupo atualizado com sucesso!' });
      setShowEditGroupModal(false);
      fetchGroups(editingGroup.id); // Re-fetch and keep selected group updated
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
    if (!user || user.papel !== 'global_admin') {
      setActionMessage({ type: 'error', text: 'Ação não permitida.' });
      return;
    }
    if (!window.confirm('Tem certeza que deseja excluir este grupo? Esta ação não pode ser desfeita.')) return;
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/tools/grupos/${groupId}`, token, { method: 'DELETE' });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao excluir grupo.');
      setActionMessage({ type: 'success', text: responseData.mensagem || 'Grupo excluído com sucesso!' });
      setSelectedGroup(null); // Clear selection as group is gone
      fetchGroups();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleOpenAddAdminModal = () => {
    setNewAdminUsername('');
    setAddAdminError('');
    setShowAddAdminModal(true);
  };

  const handleAddAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || user.papel !== 'global_admin') {
      setAddAdminError('Ação não permitida.');
      return;
    }
    if (!selectedGroup || !newAdminUsername.trim()) {
      setAddAdminError('Nome de usuário do admin é obrigatório.');
      return;
    }
    setIsAddingAdmin(true);
    setAddAdminError('');
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/tools/grupos/${selectedGroup.id}/admins`, token, {
        method: 'POST',
        body: JSON.stringify({ username: newAdminUsername.trim() }),
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao adicionar administrador.');
      setActionMessage({ type: 'success', text: responseData.mensagem || 'Administrador adicionado!' });
      setShowAddAdminModal(false);
      fetchGroups(selectedGroup.id);
    } catch (err: any) {
      setAddAdminError(err.message);
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsAddingAdmin(false);
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleOpenAddUserModal = () => {
    setNewUserUsername('');
    setAddUserError('');
    setShowAddUserModal(true);
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || user.papel !== 'global_admin') {
      setAddUserError('Ação não permitida.');
      return;
    }
    if (!selectedGroup || !newUserUsername.trim()) {
      setAddUserError('Nome de usuário é obrigatório.');
      return;
    }
    setIsAddingUser(true);
    setAddUserError('');
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/tools/grupos/${selectedGroup.id}/usuarios`, token, {
        method: 'POST',
        body: JSON.stringify({ username: newUserUsername.trim() }),
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao adicionar usuário.');
      setActionMessage({ type: 'success', text: responseData.mensagem || 'Usuário adicionado!' });
      setShowAddUserModal(false);
      fetchGroups(selectedGroup.id);
    } catch (err: any) {
      setAddUserError(err.message);
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsAddingUser(false);
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleOpenAddToolModal = () => {
    setNewToolName('');
    setAddToolError('');
    setShowAddToolModal(true);
  };

  const handleAddTool = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || user.papel !== 'global_admin') {
      setAddToolError('Ação não permitida.');
      return;
    }
    if (!selectedGroup || !newToolName.trim()) {
      setAddToolError('Nome da ferramenta é obrigatório.');
      return;
    }
    setIsAddingTool(true);
    setAddToolError('');
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/tools/grupos/${selectedGroup.id}/ferramentas`, token, {
        method: 'POST',
        body: JSON.stringify({ nome: newToolName }),
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || 'Falha ao adicionar ferramenta.');
      setActionMessage({ type: 'success', text: responseData.mensagem || 'Ferramenta adicionada!' });
      setShowAddToolModal(false);
      fetchGroups(selectedGroup.id);
    } catch (err: any) {
      setAddToolError(err.message);
      setActionMessage({ type: 'error', text: err.message });
    } finally {
      setIsAddingTool(false);
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  const handleRemoveUserFromGroup = async (groupId: string, usernameToRemove: string) => {
    if (!user || user.papel !== 'global_admin') {
      setActionMessage({ type: 'error', text: 'Ação não permitida.' });
      clearActionMessage();
      return;
    }
    if (!window.confirm(`Tem certeza que deseja remover o usuário ${usernameToRemove} do grupo ${groupId}?`)) return;
    
    setActionMessage(null);
    setIsPerformingGroupAction(true);
    try {
      const response = await fetchWithAuth(`/tools/grupos/${groupId}/usuarios/${usernameToRemove}`, token, { 
        method: 'DELETE',
      });
      const responseData = await response.json();
      if (!response.ok) {
        throw new Error(responseData.detail || 'Falha ao remover usuário do grupo.');
      }
      setActionMessage({ type: 'success', text: responseData.mensagem || 'Usuário removido com sucesso!' });
      fetchGroups(groupId); // Refresh the current group details
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message || 'Erro desconhecido ao remover usuário.' });
    } finally {
      setIsPerformingGroupAction(false);
      clearActionMessage();
    }
  };

  return (
    <div className="group-admin-container">
      <h2>Gestão de Grupos</h2>

      {actionMessage && (
        <div className={`action-message ${actionMessage.type}`}>
          {actionMessage.text}
        </div>
      )}

      {!selectedGroup ? (
        <>
          <button onClick={handleOpenCreateGroupModal} className="button-primary margin-bottom-20" disabled={isPerformingGroupAction}>
            Criar Novo Grupo
          </button>
          <div className="card">
            <h3>Grupos Existentes</h3>
            {isLoadingGroups && <p>Carregando grupos...</p>}
            {fetchGroupsError && <div className="error-message">{fetchGroupsError}</div>}
            {!isLoadingGroups && !fetchGroupsError && groups.length === 0 && <p>Nenhum grupo cadastrado.</p>}
            <ul className="list-group">
              {groups.map((group) => (
                <li key={group.id} className="list-group-item group-item">
                  <div>
                    <strong>{group.nome}</strong>
                    <p>{group.descricao}</p>
                    <p><small>Admins: {group.administradores.join(', ') || 'Nenhum'}</small></p>
                    <p><small>Usuários: {group.usuarios.length}</small></p>
                    <p><small>Ferramentas: {group.ferramentas_disponiveis.length}</small></p>
                  </div>
                  <button 
                    onClick={() => setSelectedGroup(group)} 
                    className="button-small"
                    disabled={isPerformingGroupAction}
                  >
                    Gerenciar
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </>
      ) : (
        <div className="card margin-top-20">
          <h3>Gerenciando Grupo: {selectedGroup.nome}</h3>
          <p><strong>ID:</strong> {selectedGroup.id}</p>
          <p><strong>Descrição:</strong> {selectedGroup.descricao}</p>
          
          <div className="group-actions margin-top-20 margin-bottom-20">
            <button onClick={() => handleOpenEditGroupModal(selectedGroup)} className="button-secondary" disabled={isPerformingGroupAction}>Editar Grupo</button>
            <button onClick={() => handleDeleteGroup(selectedGroup.id)} className="button-danger" disabled={isPerformingGroupAction}>Excluir Grupo</button>
          </div>

          <div className="management-section card margin-top-20">
            <h4>Administradores ({selectedGroup.administradores.length})</h4>
            <ul className="list-group-condensed">
              {selectedGroup.administradores.map(admin => <li key={admin}>{admin}</li>)}
            </ul>
            {selectedGroup.administradores.length === 0 && <p>Nenhum administrador.</p>}
            <button onClick={handleOpenAddAdminModal} className="button-small margin-top-10" disabled={isPerformingGroupAction}>Adicionar Admin</button>
          </div>

          <div className="management-section card margin-top-20">
            <h4>Usuários ({selectedGroup.usuarios.length})</h4>
            <ul className="list-group-condensed">
              {selectedGroup.usuarios.map(usr => (
                <li key={usr} className="list-group-item-condensed">
                  {usr}
                  <button 
                    onClick={() => handleRemoveUserFromGroup(selectedGroup.id, usr)} 
                    className="button-danger-small margin-left-10"
                    disabled={isPerformingGroupAction} 
                  >
                    Remover
                  </button>
                </li>
              ))}
            </ul>
            {selectedGroup.usuarios.length === 0 && <p>Nenhum usuário.</p>}
            <button onClick={handleOpenAddUserModal} className="button-small margin-top-10" disabled={isPerformingGroupAction}>Adicionar Usuário</button>
          </div>

          <div className="management-section card margin-top-20">
            <h4>Ferramentas ({selectedGroup.ferramentas_disponiveis.length})</h4>
            <ul className="list-group-condensed">
              {selectedGroup.ferramentas_disponiveis.map(tool => (
                <li key={tool.id || tool.nome}>{tool.nome} ({tool.url_base})</li>
              ))}
            </ul>
            {selectedGroup.ferramentas_disponiveis.length === 0 && <p>Nenhuma ferramenta.</p>}
            <button onClick={handleOpenAddToolModal} className="button-small margin-top-10" disabled={isPerformingGroupAction}>Adicionar Ferramenta</button>
          </div>
          
          <button onClick={() => setSelectedGroup(null)} className="button-primary margin-top-20" disabled={isPerformingGroupAction}>
            Voltar para Lista de Grupos
          </button>
        </div>
      )}

      {showCreateGroupModal && (
        <div className="modal">
          <div className="modal-content card">
            <span className="close-button" onClick={() => setShowCreateGroupModal(false)}>&times;</span>
            <h3>Criar Novo Grupo</h3>
            <form onSubmit={handleCreateGroup}>
              <div className="form-group">
                <label htmlFor="newGroupName">Nome do Grupo:</label>
                <input
                  id="newGroupName"
                  type="text"
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="newGroupDescription">Descrição:</label>
                <textarea
                  id="newGroupDescription"
                  value={newGroupDescription}
                  onChange={(e) => setNewGroupDescription(e.target.value)}
                  required
                />
              </div>
              {createGroupError && <div className="error-message">{createGroupError}</div>}
              <button type="submit" className="button-primary" disabled={isCreatingGroup}>
                {isCreatingGroup ? 'Criando...' : 'Criar Grupo'}
              </button>
            </form>
          </div>
        </div>
      )}

      {showEditGroupModal && editingGroup && (
        <div className="modal">
          <div className="modal-content card">
            <span className="close-button" onClick={() => setShowEditGroupModal(false)}>&times;</span>
            <h3>Editar Grupo: {editingGroup.nome}</h3>
            <form onSubmit={handleUpdateGroup}>
              <div className="form-group">
                <label htmlFor="editGroupName">Nome do Grupo:</label>
                <input id="editGroupName" type="text" value={editGroupName} onChange={(e) => setEditGroupName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label htmlFor="editGroupDescription">Descrição:</label>
                <textarea id="editGroupDescription" value={editGroupDescription} onChange={(e) => setEditGroupDescription(e.target.value)} required />
              </div>
              {editGroupError && <div className="error-message">{editGroupError}</div>}
              <button type="submit" className="button-primary" disabled={isUpdatingGroup}>{isUpdatingGroup ? 'Atualizando...' : 'Salvar Alterações'}</button>
            </form>
          </div>
        </div>
      )}

      {showAddAdminModal && selectedGroup && (
        <div className="modal">
          <div className="modal-content card">
            <span className="close-button" onClick={() => setShowAddAdminModal(false)}>&times;</span>
            <h3>Adicionar Admin ao Grupo: {selectedGroup.nome}</h3>
            <form onSubmit={handleAddAdmin}>
              <div className="form-group">
                <label htmlFor="newAdminUsername">Nome do Usuário Admin:</label>
                <input id="newAdminUsername" type="text" value={newAdminUsername} onChange={(e) => setNewAdminUsername(e.target.value)} required />
              </div>
              {addAdminError && <div className="error-message">{addAdminError}</div>}
              <button type="submit" className="button-primary" disabled={isAddingAdmin}>{isAddingAdmin ? 'Adicionando...' : 'Adicionar Admin'}</button>
            </form>
          </div>
        </div>
      )}

      {showAddUserModal && selectedGroup && (
        <div className="modal">
          <div className="modal-content card">
            <span className="close-button" onClick={() => setShowAddUserModal(false)}>&times;</span>
            <h3>Adicionar Usuário ao Grupo: {selectedGroup.nome}</h3>
            <form onSubmit={handleAddUser}>
              <div className="form-group">
                <label htmlFor="newUserUsername">Nome do Usuário:</label>
                <input id="newUserUsername" type="text" value={newUserUsername} onChange={(e) => setNewUserUsername(e.target.value)} required />
              </div>
              {addUserError && <div className="error-message">{addUserError}</div>}
              <button type="submit" className="button-primary" disabled={isAddingUser}>{isAddingUser ? 'Adicionando...' : 'Adicionar Usuário'}</button>
            </form>
          </div>
        </div>
      )}

      {showAddToolModal && selectedGroup && (
        <div className="modal">
          <div className="modal-content card">
            <span className="close-button" onClick={() => setShowAddToolModal(false)}>&times;</span>
            <h3>Adicionar Ferramenta ao Grupo: {selectedGroup.nome}</h3>
            <form onSubmit={handleAddTool}>
              <div className="form-group">
                <label htmlFor="newToolName">Nome da Ferramenta (deve existir globalmente):</label>
                <input id="newToolName" type="text" value={newToolName} onChange={(e) => setNewToolName(e.target.value)} required />
              </div>
              {addToolError && <div className="error-message">{addToolError}</div>}
              <button type="submit" className="button-primary" disabled={isAddingTool}>{isAddingTool ? 'Adicionando...' : 'Adicionar Ferramenta'}</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupAdmin;
