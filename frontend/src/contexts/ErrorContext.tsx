import React, { createContext, useContext, useState, useCallback } from 'react';
import type { ReactNode } from 'react'; // Changed to type-only import

// Tipos para o context de erros
interface ErrorContent {
  message: string;
  code?: string | number;
  timestamp?: Date;
}

interface ErrorContextType {
  error: ErrorContent | null;
  setError: (error: ErrorContent | null) => void;
  clearError: () => void;
}

// Criar o context
const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

// Componente Provider
export const ErrorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [error, setErrorState] = useState<ErrorContent | null>(null);

  const setError = useCallback((error: ErrorContent | null) => {
    if (error) {
      setErrorState({
        ...error,
        timestamp: new Date(),
      });
    } else {
      setErrorState(null);
    }
  }, []);

  const clearError = useCallback(() => {
    setErrorState(null);
  }, []);

  return (
    <ErrorContext.Provider value={{ error, setError, clearError }}>
      {children}
    </ErrorContext.Provider>
  );
};

// Hook para usar o ErrorContext
export const useError = () => {
  const context = useContext(ErrorContext);
  if (context === undefined) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

// Componente ErrorBoundary
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: React.ReactNode;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Você pode registrar o erro em um serviço de relatórios de erro
    console.error("Erro capturado pelo ErrorBoundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // Renderizar fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      return (
        <div className="error-boundary card">
          <h3>Algo deu errado</h3>
          <p>{this.state.error?.message || 'Um erro inesperado ocorreu.'}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            Tentar novamente
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Componente de toast de erro
export const ErrorToast: React.FC = () => {
  const { error, clearError } = useError();
  
  if (!error) return null;
  
  // Auto-dismiss after 5 seconds
  React.useEffect(() => {
    if (error) {
      const timer = setTimeout(() => clearError(), 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);
  
  return (
    <div className="error-toast">
      <div className="error-toast-content">
        <span className="error-toast-message">{error.message}</span>
        {error.code && <span className="error-toast-code">Code: {error.code}</span>}
        <button className="error-toast-close" onClick={clearError}>×</button>
      </div>
    </div>
  );
};
