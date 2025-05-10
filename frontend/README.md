# MCP Gateway Portal (Frontend)

Este projeto é o portal de autoatendimento para o MCP Gateway, desenvolvido utilizando React, Vite e TypeScript. Ele interage com a API backend do MCP Gateway para fornecer funcionalidades de gerenciamento e acesso a ferramentas.

*(Atualizado em 2025-05-10 para refletir o estado atual e funcionalidades implementadas)*

## Funcionalidades Implementadas (Visão Geral)

- **Autenticação e Sessão:**
    - Login de usuário com JWT (`Login.tsx`, `AuthContext.tsx`).
    - Renovação automática de token (Refresh Token) integrada ao `AuthContext.tsx` e `AuthService.ts`.
    - Logout.
- **Proteção de Rotas:**
    - Rotas protegidas baseadas em autenticação e papéis de usuário (`ProtectedRoute.tsx`, `AppRouter.tsx`).
- **Dashboard:**
    - Exibição de informações básicas do usuário (`Dashboard.tsx`).
    - Listagem de nomes de grupos para `global_admin` (funcionalidade básica).
- **Gerenciamento de Solicitações de Acesso a Grupos (RF06):**
    - **Usuário:**
        - Solicitar acesso a grupos disponíveis (`UserRequests.tsx`, interage com `GET /tools/grupos/disponivel` e `POST /tools/requests/`).
        - Visualizar o status de suas próprias solicitações (`UserRequests.tsx`, interage com `GET /tools/requests/me`).
    - **Administrador (de Grupo ou Global):**
        - Visualizar solicitações pendentes para os grupos que administra (ou todos para `global_admin`) (`RequestsAdmin.tsx`, interage com `GET /tools/requests/admin`).
        - Aprovar ou rejeitar solicitações (`RequestsAdmin.tsx`, interage com `POST /tools/requests/{request_id}/review`).
- **Visualização de Ferramentas (Base para RF05):**
    - Página `Tools.tsx` para listar ferramentas (atualmente precisa ser atualizada para usar `GET /user_tools`).
- **Gerenciamento de Erros e Carregamento:**
    - Contexto global de erro (`ErrorContext.tsx`) para feedback ao usuário.
    - Indicador visual de carregamento (`LoadingSpinner.tsx`, `useLoading.ts`).
    - Hook `useApiError.ts` para tratamento padronizado de erros da API.
- **Navegação:**
    - Barra de navegação (`Navbar.tsx`) com links dinâmicos baseados no papel do usuário.

## Funcionalidades Pendentes ou em Desenvolvimento (Principais)
Conforme `docs/TODO.md`:

- **Gerenciamento Completo de Grupos (RF02, RF03, RF04 - `GroupAdmin.tsx`):**
    - Alinhar a página `GroupAdmin.tsx` com os papéis corretos (global_admin vs admin de grupo).
    - Corrigir a obtenção e submissão de dados para corresponder aos endpoints backend existentes ou criar/usar novos.
    - Implementar UI para todas as funcionalidades de gerenciamento de grupos, seus usuários e ferramentas.
- **Gerenciamento Completo de Usuários (RF02/RF07 - Admin Global):**
    - Criar nova página/componente para CRUD de usuários por `global_admin`.
- **Melhorias na UI/UX:**
    - Notificações para o usuário.
    - Páginas de erro customizadas.
    - Feedback visual para ações bem-sucedidas.
    - Internacionalização (i18n).
- **Consumo Efetivo de Ferramentas (RF05 - `Tools.tsx`):**
    - Atualizar `Tools.tsx` para usar o endpoint `GET /user_tools` e permitir a "execução" ou acesso às ferramentas listadas.

## Estrutura do Projeto (`frontend/src/`)

- **`main.tsx`**: Ponto de entrada da aplicação React.
- **`App.tsx`**: Componente raiz da aplicação.
- **`AppRouter.tsx`**: Define as rotas da aplicação e utiliza `ProtectedRoute`.
- **`assets/`**: Arquivos estáticos como imagens (ex: `react.svg`).
- **`components/`**: Componentes React reutilizáveis:
    - `LoadingSpinner.tsx`: Indicador de carregamento.
    - `Navbar.tsx`: Barra de navegação superior.
    - `ProtectedRoute.tsx`: Componente de ordem superior para proteger rotas.
- **`contexts/`**: Contextos React para gerenciamento de estado global:
    - `AuthContext.tsx`: Gerencia o estado de autenticação, informações do usuário e tokens.
    - `ErrorContext.tsx`: Fornece uma forma de exibir mensagens de erro globalmente.
- **`hooks/`**: Hooks customizados:
    - `useLoading.ts`: Hook para gerenciar estados de carregamento.
    - `useApiError.ts`: Hook para tratamento padronizado de erros de API.
- **`pages/`**: Componentes que representam as diferentes páginas da aplicação:
    - `Dashboard.tsx`: Painel principal após o login.
    - `Login.tsx`: Página de login.
    - `GroupAdmin.tsx`: (Em desenvolvimento) Página para administração de grupos.
    - `RequestsAdmin.tsx`: Página para administradores gerenciarem solicitações de acesso a grupos.
    - `Tools.tsx`: Página para usuários visualizarem/acessarem ferramentas.
    - `UserManagement.tsx`: (Placeholder ou a ser criado) Página para gerenciamento de usuários pelo admin global.
    - `UserRequests.tsx`: Página para usuários criarem e visualizarem suas solicitações de acesso.
- **`services/`**: Módulos para interagir com a API backend:
    - `AuthService.ts`: Funções relacionadas à autenticação (login, refresh token).
    - `api.ts`: Configuração da instância Axios e interceptors para requisições API, incluindo a lógica de refresh token.
- **`utils/`**: Utilitários gerais.
- **Estilização:**
    - `index.css`, `App.css`: Arquivos CSS globais e por componente.

## Scripts Disponíveis

No diretório do projeto, você pode executar:

- **`npm run dev`**: Inicia a aplicação em modo de desenvolvimento.
  Abra [http://localhost:5173](http://localhost:5173) (ou a porta indicada) para visualizar no navegador.
A página recarrega automaticamente ao fazer edições.

- **`npm run build`**: Compila a aplicação para produção na pasta `dist/`.
  Otimiza a build para melhor performance.

- **`npm run lint`**: Executa o ESLint para verificar problemas de linting no código.

- **`npm run preview`**: Serve localmente os arquivos da build de produção (da pasta `dist/`) para pré-visualização.

## Integração com o Backend

- O frontend espera que o backend FastAPI esteja rodando (por padrão em `http://localhost:8000`).
- As requisições API são feitas para `/tools/...`.
- O backend FastAPI é configurado para servir os arquivos estáticos do frontend (da pasta `frontend/dist/`) quando em modo de produção, permitindo que ambos rodem na mesma origem.
- Para desenvolvimento, o CORS é habilitado no backend para permitir requisições do servidor de desenvolvimento Vite (ex: `localhost:5173`).

---

Consulte a documentação principal do projeto (`README.md` na raiz e `docs/`) para mais informações sobre o sistema completo e a API backend.
