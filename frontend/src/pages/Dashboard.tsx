import { useEffect, useState } from 'react';
import '../App.css'; // Ensure App.css is imported

type DashboardProps = {
  token: string;
  user: any;
};

const Dashboard = ({ token, user }: DashboardProps) => {
  const [allGroups, setAllGroups] = useState<string[]>([]);
  const [myGroups, setMyGroups] = useState<string[]>(user?.grupos || []);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [pendingRequests, setPendingRequests] = useState<{ [group: string]: string[] }>({});
  const [adminGroups, setAdminGroups] = useState<string[]>([]);

  useEffect(() => {
    console.log("[Dashboard] Token received:", token ? "Exists" : "Missing");
    const fetchGroups = async () => {
      setError('');
      try {
        const res = await fetch('/tools/grupos', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          console.log("[Dashboard] All groups fetched:", data.grupos);
          setAllGroups(data.grupos || []);
        } else {
          console.error("[Dashboard] Failed to fetch all groups, status:", res.status);
          setAllGroups([]);
        }
      } catch (err) {
        console.error("[Dashboard] Error fetching all groups:", err);
        setAllGroups([]);
      }
    };
    const fetchMyGroups = async () => {
      try {
        setMyGroups(user?.grupos || []);
        const userIsAdmin = user?.papel === 'global_admin' || user?.papel === 'admin';
        setIsAdmin(userIsAdmin);
        console.log("[Dashboard] isAdmin state set to:", userIsAdmin, "(based on papel:", user?.papel, ")");
      } catch (err) {
        console.error("[Dashboard] Error setting admin status:", err);
        setMyGroups([]);
        setIsAdmin(false);
      }
    };
    if (token) { // Only fetch if token exists
        fetchGroups();
        fetchMyGroups();
    } else {
        setAllGroups([]);
        setMyGroups([]);
        setIsAdmin(false);
    }
  }, [token, user]);

  useEffect(() => {
    console.log("[Dashboard] Admin groups effect triggered. isAdmin:", isAdmin, "Current allGroups:", allGroups);
    if (!isAdmin || !token) { // Also check for token
      setAdminGroups([]);
      return;
    }
    const fetchAdminGroups = () => {
      try {
        console.log("[Dashboard] Setting admin groups. User papel:", user?.papel);
        if (user?.papel === 'global_admin') {
          console.log("[Dashboard] User is global_admin. Setting adminGroups to allGroups:", allGroups);
          setAdminGroups(allGroups);
        } else if (user?.papel === 'admin') {
          console.log("[Dashboard] User is admin. Setting adminGroups to myGroups:", myGroups);
          setAdminGroups(myGroups);
        } else {
          setAdminGroups([]);
        }
      } catch (err) {
        console.error("[Dashboard] Error in fetchAdminGroups:", err);
        setAdminGroups([]);
      }
    };
    fetchAdminGroups();
  }, [isAdmin, allGroups, myGroups, token, user]);

  useEffect(() => {
    console.log("[Dashboard] Pending requests effect triggered. isAdmin:", isAdmin, "Admin groups:", adminGroups);
    if (!isAdmin || adminGroups.length === 0 || !token) { // Also check for token
      setPendingRequests({});
      return;
    }
    const fetchRequests = async () => {
      const reqs: { [group: string]: string[] } = {};
      console.log("[Dashboard] Fetching pending requests for adminGroups:", adminGroups);
      for (const g of adminGroups) {
        try {
          const res = await fetch(`/tools/grupos/${g}/solicitacoes`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            console.log(`[Dashboard] Pending requests for group ${g}:`, data.solicitacoes);
            reqs[g] = data.solicitacoes || [];
          } else {
            console.error(`[Dashboard] Failed to fetch requests for group ${g}, status:`, res.status);
            reqs[g] = []; // Ensure group key exists even if fetch fails
          }
        } catch (err) {
          console.error(`[Dashboard] Error fetching requests for group ${g}:`, err);
          reqs[g] = []; // Ensure group key exists on error
        }
      }
      setPendingRequests(reqs);
      console.log("[Dashboard] All pending requests set:", reqs);
    };
    fetchRequests();
  }, [isAdmin, adminGroups, token, message]);

  const handleJoin = async (grupo: string) => {
    setMessage('');
    setError('');
    try {
      const res = await fetch(`/tools/grupos/${grupo}/solicitar-entrada`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setMessage(data.message);
      } else {
        setError(data.detail || 'Erro ao solicitar entrada');
      }
    } catch (err) {
      console.error("[Dashboard] Error in handleJoin:", err);
      setError('Erro ao conectar para solicitar entrada');
    }
  };

  const handleApprove = async (grupo: string, username: string) => {
    setMessage('');
    setError('');
    try {
      const res = await fetch(`/tools/grupos/${grupo}/solicitacoes/${username}/aprovar`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setMessage(data.message);
      } else {
        setError(data.detail || 'Erro ao aprovar solicitação');
      }
    } catch (err) {
      console.error("[Dashboard] Error in handleApprove:", err);
      setError('Erro ao conectar para aprovar solicitação');
    }
  };

  const handleReject = async (grupo: string, username: string) => {
    setMessage('');
    setError('');
    try {
      const res = await fetch(`/tools/grupos/${grupo}/solicitacoes/${username}/rejeitar`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) {
        setMessage(data.message);
      } else {
        setError(data.detail || 'Erro ao rejeitar solicitação');
      }
    } catch (err) {
      console.error("[Dashboard] Error in handleReject:", err);
      setError('Erro ao conectar para rejeitar solicitação');
    }
  };

  const availableGroups = allGroups.filter(g => !myGroups.includes(g));

  return (
    <>
      <div className="card">
        <h2>Bem-vindo, {user?.sub || 'usuário'}!</h2>
        <p>Papel: <b>{user?.papel}</b></p>
        <p>Aqui você pode visualizar seus grupos, solicitar acesso a novos grupos e, se for admin, gerenciar solicitações.</p>
      </div>

      <div className="card">
        <h3>Seus grupos</h3>
        {myGroups.length > 0 ? (
          <ul className="list-group">
            {myGroups.map(g => <li key={g} className="list-group-item">{g}</li>)}
          </ul>
        ) : (
          <p>Você ainda não faz parte de nenhum grupo.</p>
        )}
      </div>

      <div className="card">
        <h3>Solicitar entrada em grupo</h3>
        {availableGroups.length > 0 ? (
          <ul className="list-group">
            {availableGroups.map(g => (
              <li key={g} className="list-group-item">
                {g} <button onClick={() => handleJoin(g)} className="secondary">Solicitar entrada</button>
              </li>
            ))}
          </ul>
        ) : (
          <p>Nenhum grupo disponível para solicitação no momento.</p>
        )}
      </div>

      {isAdmin && (
        <div className="card">
          <h3>Solicitações pendentes para seus grupos</h3>
          {Object.keys(pendingRequests).length === 0 ? <p>Nenhuma solicitação pendente.</p> :
            Object.entries(pendingRequests).map(([g, users]) => (
              users.length > 0 && (
              <div key={g} className="dashboard-section-spacing">
                <h4>{g}</h4>
                <ul className="list-group">
                  {users.map((u: string) => (
                    <li key={u} className="list-group-item">
                      {u}
                      <span className="list-item-actions">
                        <button onClick={() => handleApprove(g, u)} className="action-button-spacing">Aprovar</button>
                        <button onClick={() => handleReject(g, u)} className="secondary">Rejeitar</button>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              )
            ))}
        </div>
      )}
      {message && <div className="success-message message-spacing">{message}</div>}
      {error && <div className="error-message message-spacing">{error}</div>}
    </>
  );
};

export default Dashboard;
