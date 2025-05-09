// filepath: frontend/src/utils/api.ts
export interface ApiErrorDetail {
  detail: string;
  // Adicione outros campos se a sua API retornar erros mais estruturados
}

/**
 * Realiza uma requisição fetch com o token de autorização e Content-Type padrão.
 * @param url A URL da API.
 * @param token O token JWT.
 * @param options Opções adicionais para a requisição fetch.
 * @returns A promessa da resposta da requisição.
 */
export async function fetchWithAuth(
  url: string,
  token: string | null, // Permitir token nulo para maior flexibilidade
  options: RequestInit = {}
): Promise<Response> {
  // Verificar se temos um token passado como parâmetro ou pegar o mais recente do localStorage
  const tokenToUse = token || localStorage.getItem('mcp_token');
  
  // Initialize headers as Record<string, string> for proper typing
  const newHeaders: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (tokenToUse) {
    // Assegure-se que o formato do token seja Bearer + token sem espaços extras
    // e sem 'Bearer' duplicado se o token já começar com essa string
    const tokenValue = tokenToUse.startsWith('Bearer ') ? tokenToUse : `Bearer ${tokenToUse}`;
    newHeaders['Authorization'] = tokenValue;
  }

  // Conditionally add Content-Type only if there is a body and method is not GET/HEAD
  if (options.body && options.method && !['GET', 'HEAD'].includes(options.method.toUpperCase())) {
    newHeaders['Content-Type'] = 'application/json';
  }

  console.log('fetchWithAuth: Requesting URL:', url);
  console.log('fetchWithAuth: Full Token Sent:', tokenToUse ? `Bearer ${tokenToUse}` : 'No token'); 
  console.log('fetchWithAuth: Options:', options);
  console.log('fetchWithAuth: Final Headers:', newHeaders);

  const response = await fetch(url, {
    ...options,
    headers: newHeaders,
  });

  console.log('fetchWithAuth: Response Status:', response.status, 'for URL:', url);

  // If response is not ok, and it's a 401, log a specific message
  if (!response.ok && response.status === 401) {
    console.error('fetchWithAuth: 401 Unauthorized error for URL:', url, 'Full Token used:', tokenToUse ? `Bearer ${tokenToUse}` : 'No token'); 
    try {
      const errorBodyText = await response.clone().text(); // Use clone to be able to read it again later
      console.error('fetchWithAuth: 401 Response body (text):', errorBodyText);
      // Try to parse as JSON if it looks like it might be
      if (errorBodyText.trim().startsWith('{')) {
        try {
          const parsedError = JSON.parse(errorBodyText);
          console.error('fetchWithAuth: 401 Response body (parsed JSON):', parsedError);
        } catch (parseError) {
          console.error('fetchWithAuth: Failed to parse 401 response body as JSON:', parseError);
        }
      }
    } catch (e) {
      console.error('fetchWithAuth: Could not read 401 response body:', e);
    }
  }

  return response;
}

/**
 * Tenta extrair o corpo da mensagem de erro de uma resposta.
 * @param response A resposta da API.
 * @returns Um objeto com o detalhe do erro ou uma mensagem de erro genérica.
 */
export async function getErrorBody(response: Response): Promise<ApiErrorDetail> {
  try {
    // Tenta parsear como JSON primeiro, que é o esperado para erros FastAPI
    const errorData = await response.json();
    if (errorData && typeof errorData.detail === 'string') {
      return errorData as ApiErrorDetail;
    }
    // Fallback se não for JSON ou não tiver 'detail'
    return { detail: response.statusText || `Erro ${response.status} ao processar a resposta.` };
  } catch (e) {
    // Se o corpo não for JSON válido, retorna o statusText
    return { detail: response.statusText || `Erro ${response.status} e resposta não pôde ser lida.` };
  }
}
