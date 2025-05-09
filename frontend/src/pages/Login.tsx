import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useApiError } from '../utils/errorHandling';
import useLoading from '../hooks/useLoading';
import LoadingSpinner from '../components/LoadingSpinner';
import '../App.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();
  const { processApiResponse, handleApiError } = useApiError();
  const { isLoading, execute } = useLoading();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    try {
      const result = await execute(
        fetch('/tools/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        })
      );
      
      if (!result) return; // Já tratado pelo execute
      
      const hasError = await processApiResponse(result);
      
      if (hasError) return;
      
      const data = await result.json();
      console.log('Login successful, token received');
      login(data.access_token);
      navigate('/dashboard');
    } catch (error) {
      handleApiError(error);
    }
  };

  return (
    <div className="card login-card">
      <form onSubmit={handleSubmit}>
        <h2>Login</h2>
        <div className="form-group">
          <label htmlFor="username">Usuário</label>
          <input
            id="username"
            type="text"
            placeholder="Seu usuário"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Senha</label>
          <input
            id="password"
            type="password"
            placeholder="Sua senha"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>
        <div className="button-group">
          {isLoading ? (
            <LoadingSpinner size="small" />
          ) : (
            <button type="submit">Entrar</button>
          )}
        </div>
      </form>
    </div>
  );
};

export default Login;
