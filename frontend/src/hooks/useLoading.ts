import { useState, useCallback } from 'react';

interface UseLoadingResult<T> {
  isLoading: boolean;
  error: string | null;
  execute: (promise: Promise<T>) => Promise<T | null>;
  setIsLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

/**
 * Hook para gerenciar estado de carregamento e erros em operações assíncronas
 * 
 * @returns Objeto com estado de carregamento, erro e função para executar promises
 */
export default function useLoading<T = any>(): UseLoadingResult<T> {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  /**
   * Executa uma promise gerenciando automaticamente os estados de loading e erro
   * 
   * @param promise A promise a ser executada
   * @returns O resultado da promise ou null em caso de erro
   */
  const execute = useCallback(async (promise: Promise<T>): Promise<T | null> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await promise;
      return result;
    } catch (err: any) {
      const errorMessage = err?.message || 'Ocorreu um erro inesperado';
      console.error('useLoading error:', errorMessage, err);
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isLoading,
    error,
    execute,
    setIsLoading,
    setError,
    clearError
  };
}
