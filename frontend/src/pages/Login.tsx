import { useState } from 'react';
import type { FormEvent } from 'react';
import '../App.css';

type LoginProps = {
  onLogin: (token: string) => void;
};

const Login = ({ onLogin }: LoginProps) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const res = await fetch('/tools/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Usuário ou senha inválidos' }));
        throw new Error(errorData.detail || 'Usuário ou senha inválidos');
      }
      const data = await res.json();
      onLogin(data.access_token);
    } catch (error: unknown) {
      if (error instanceof Error) {
        setError(error.message || 'Erro ao autenticar. Tente novamente.');
      } else {
        setError('Erro ao autenticar. Tente novamente.');
      }
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
          />
        </div>
        <div className="button-group">
          <button type="submit">Entrar</button>
        </div>
        {error && <div className="error-message">{error}</div>}
      </form>
    </div>
  );
};

export default Login;
