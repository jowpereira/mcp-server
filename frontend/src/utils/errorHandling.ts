// Utilitário para integrar o ErrorContext com as chamadas de API
import { useError } from '../contexts/ErrorContext';

/**
 * Hook para lidar com erros de API utilizando o contexto global de erros
 * Retorna funções auxiliares para lidar com erros em respostas de fetch
 */
export function useApiError() {
  const { setError } = useError();

  /**
   * Processa uma resposta de API e mostra o erro se for o caso
   * @param response - A resposta da API
   * @param options - Opções adicionais
   * @returns true se a resposta foi processada e tem erro, false caso contrário
   */
  const processApiResponse = async (
    response: Response, 
    options: { 
      showError?: boolean,            // Se deve mostrar o erro automaticamente
      logResponse?: boolean           // Se deve logar a resposta no console
    } = {}
  ): Promise<boolean> => {
    const { 
      showError = true, 
      logResponse = false 
    } = options;

    if (logResponse) {
      console.log('API Response:', {
        url: response.url,
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      });
    }

    if (!response.ok) {
      let errorMessage;
      let errorCode: string | number = response.status;

      try {
        const contentType = response.headers.get('content-type');
        if (contentType?.includes('application/json')) {
          const errorData = await response.clone().json();
          // Formato de erro FastAPI
          errorMessage = errorData.detail || errorData.message || `Erro ${response.status}: ${response.statusText}`;
        } else {
          errorMessage = `Erro ${response.status}: ${response.statusText}`;
        }
      } catch (e) {
        errorMessage = `Erro ${response.status}: ${response.statusText}`;
      }

      if (showError) {
        setError({ message: errorMessage, code: errorCode });
      }

      return true; // Tem erro
    }

    return false; // Não tem erro
  };

  /**
   * Trata um erro de requisição (ex: erro de rede)
   * @param error - O erro capturado
   * @param options - Opções adicionais
   */
  const handleApiError = (
    error: any, 
    options: {
      showError?: boolean,
      ignoreCodes?: string[],
      specificHandlers?: { [key: string]: (message: string) => void }
    } = {}
  ): void => {
    const { showError = true, ignoreCodes, specificHandlers } = options;

    const errorMessage = error.response?.data?.message || error.message || 'Ocorreu um erro desconhecido';
    const errorCode = error.response?.data?.code || 'UNKNOWN_ERROR'; // Provide a default for errorCode

    if (ignoreCodes && ignoreCodes.includes(errorCode)) {
      return;
    }

    if (specificHandlers && specificHandlers[errorCode]) {
      specificHandlers[errorCode](errorMessage);
    } else {
      console.error('API Error:', error);

      if (showError) {
        setError({ message: errorMessage, code: errorCode });
      }
    }
  };

  return {
    processApiResponse,
    handleApiError
  };
}
