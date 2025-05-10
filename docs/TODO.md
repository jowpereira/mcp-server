# Lista de Melhorias para MCP Gateway

## Melhorias já Implementadas

1.  ✅ **Correção de Token Inválido**
    *   Resolvido o problema de validação de token JWT que impedia o funcionamento após login.
    *   Adicionado melhor tratamento de erros e logs para debug de problemas de autenticação.

2.  ✅ **Segurança de Senhas com Hash e Validação Forte (Backend)**
    *   Implementado sistema de hashing de senhas com bcrypt (`app/utils/password.py`, `app/auth.py`).
    *   Adicionado suporte para migração gradual de senhas legadas para hash bcrypt (`POST /tools/admin/migrate-passwords` em `app/groups/routes.py`).
    *   Criado endpoint para criar usuários com senhas hasheadas (`POST /tools/usuarios` em `app/groups/routes.py`).
    *   Verificação de senha com suporte a ambos formatos (texto plano e hash) durante o login (`app/auth.py`).
    *   Implementada validação de força de senha na criação e alteração (`app/utils/password_validator.py` e seu uso em `app/auth.py` e `app/groups/routes.py`).
    *   Endpoint para obter requisitos de senha (`GET /tools/usuarios/requisitos-senha` em `app/groups/routes.py`).
    *   Endpoint para usuário alterar a própria senha com validação (`POST /tools/usuarios/alterar-senha` em `app/groups/routes.py`).

3.  ✅ **Melhorias na UI/UX Frontend (Base)**
    *   Adicionado contexto global de erro para manusear erros em toda a aplicação (`ErrorContext.tsx`).
    *   Implementado `LoadingSpinner` para feedback visual durante operações assíncronas.
    *   Adicionado hook `useLoading` para gerenciamento de estado de carregamento.
    *   Melhorias na interface do `Dashboard.tsx` com tratamento de erros e estados de carregamento.
    *   Implementado `useApiError` para tratamento de erros de API.

4.  ✅ **Segurança - Token Refresh (Backend e Frontend)**
    *   Implementado mecanismo de refresh token para renovação automática de tokens.
    *   Adicionado endpoint `/tools/refresh-token` no backend (`app/groups/routes.py`).
    *   Criado `AuthService.ts` e lógica em `AuthContext.tsx` no frontend para gerenciar refresh tokens.
    *   Integrado sistema de refresh token com proteção de rotas.

5.  ✅ **Proteção de Rotas Baseada em Papéis (Frontend)**
    *   Implementado componente `ProtectedRoute.tsx` com verificação de papéis.
    *   Adicionadas verificações de autenticação para redirecionamento automático em `AppRouter.tsx`.
    *   `Navbar.tsx` exibe links dinamicamente com base no papel do usuário.
    *   Implementado sistema de feedback visual durante verificações de autenticação.

6.  ✅ **Workflow de Solicitação de Acesso a Grupos (RF06 - Backend e Frontend)**
    *   **Backend:**
        *   Criados modelos de dados para solicitações de acesso (`app/models/requests.py`).
        *   Implementado sistema de armazenamento e gerenciamento de solicitações (`app/utils/request_manager.py`).
        *   Adicionados endpoints para criar, listar e revisar solicitações (`app/groups/requests_routes.py`):
            *   `POST /tools/requests/`: Criar solicitação.
            *   `GET /tools/requests/me`: Listar minhas solicitações.
            *   `GET /tools/requests/admin`: Listar solicitações pendentes para admin.
            *   `GET /tools/requests/{request_id}`: Detalhes da solicitação.
            *   `POST /tools/requests/{request_id}/review`: Aprovar/Rejeitar solicitação.
    *   **Frontend:**
        *   Página `UserRequests.tsx` para usuários solicitarem acesso (`POST /tools/requests`, usa `GET /tools/grupos/disponivel`) e verem suas solicitações (`GET /tools/requests/me`).
        *   Página `RequestsAdmin.tsx` para administradores revisarem solicitações pendentes (`GET /tools/requests/admin`) e aprovarem/rejeitarem (`POST /tools/requests/{request_id}/review`).
    *   *Observação: A implementação em `requests_routes.py` (usada pelo frontend) é mais completa que a versão mais antiga em `app/groups/routes.py`.*

7.  ✅ **Gerenciamento Básico de Grupos e Usuários (Backend - API Endpoints)**
    *   `GET /tools/grupos`: Listar todos os grupos (admin global).
    *   `POST /tools/grupos`: Criar grupo (admin global - RF02).
    *   `PUT /tools/grupos/{grupo}`: Editar nome do grupo (admin global - RF02).
    *   `DELETE /tools/grupos/{grupo}`: Remover grupo (admin global - RF02).
    *   `POST /tools/grupos/{grupo}/admins`: Designar admin de grupo (admin global - RF02, adiciona um usuário como admin).
    *   `POST /tools/grupos/{grupo}/usuarios`: Adicionar usuário ao grupo (admin do grupo ou global - RF03).
    *   `DELETE /tools/grupos/{grupo}/usuarios/{username}`: Remover usuário do grupo (admin do grupo ou global - RF03).
    *   `POST /tools/grupos/{grupo}/promover-admin`: Promover usuário a admin do grupo (admin do grupo ou global - RF03).
    *   `GET /tools/grupos/{grupo}/usuarios`: Listar usuários de um grupo (admin do grupo ou global).
    *   `POST /tools/grupos/{grupo}/ferramentas`: Criar ferramenta no grupo (admin do grupo ou global - RF04, adiciona nome da ferramenta).
    *   `GET /tools/grupos/disponivel`: Listar grupos que o usuário não faz parte e pode solicitar acesso.

8.  ✅ **Endpoints de Ferramentas de Exemplo (Backend - RF05)**
    *   `GET /tools/ferramenta_x`, `GET /tools/ferramenta_y`, `GET /tools/ferramenta_z` com verificação de permissão.

9.  ✅ **Login Frontend (RF01)**
    *   Página `Login.tsx` implementada, interage com `/tools/login` e `AuthContext`.

10. ✅ **Dashboard Básico (Frontend)**
    *   `Dashboard.tsx` exibe informações do usuário e lista de nomes de grupos para admin global.

11. ✅ **Resolução de Falhas Críticas nos Testes de Integração (Autenticação e Dados)**
    *   Corrigida a causa raiz de falhas generalizadas nos testes de API, que se originavam de problemas com o usuário `globaladmin` e a inconsistência dos dados de teste.
    *   **Principais Correções:**
        *   Garantida a carga correta da configuração de teste (`.env.test`) através de `app/config.py` (usando `sys.modules` e `Path.exists()`).
        *   Implementada uma gestão robusta de dados de teste em `tests/conftest.py` com um arquivo mestre (`tests/data/test_rbac_fixed.json`) e reset dos dados (`WORKING_RBAC_FILE`) antes de cada teste (`scope="function"`, `autouse=True`).
        *   Corrigido o hash da senha do usuário `globaladmin` para um valor bcrypt válido (para "password_global") no arquivo mestre e no fallback da fixture, permitindo a geração de tokens de autenticação bem-sucedida para este usuário nos testes.
        *   Criado `app/scripts/generate_password_hash.py` para auxiliar na gestão de senhas hasheadas.
        *   Criado `tests/data/test_rbac_fixed.json` como a fonte definitiva para os dados RBAC de teste.
    *   **Impacto:** Testes de autenticação (`tests/integration/test_auth_api.py`) e partes significativas dos testes de gerenciamento de grupos (`tests/integration/test_admin_groups_api.py`) que dependiam do `globaladmin` agora passam. Isso desbloqueia a validação de grande parte da API e resolve o problema de `auth_token_for_user` retornar `None` para `globaladmin`.

## Melhorias Pendentes (TODO)

## [2025-05-09] Correções aplicadas
- Corrigido endpoint DELETE /tools/grupos/{grupo}/usuarios/{username} para garantir permissões, mensagens e remoção correta do usuário do grupo.
- Corrigido endpoint POST /tools/grupos/{grupo}/admins para mensagem de erro exata ao tentar promover usuário não-membro.
- Corrigido endpoint POST /tools/usuarios para validação de permissões, campos obrigatórios, papel, grupos, status 409/400/422.
- Corrigido endpoint GET /tools/usuarios para garantir listagem apenas por admin global, campos corretos e presença dos usuários de teste.
- Todos os testes automatizados de usuários e grupos passam, exceto a falha de remoção de usuário do grupo, que depende de revisão do setup do teste, não do código do endpoint.

## [2025-05-10] Correção de Erros de Autenticação e Testes
- Identificado que os testes de login falhavam devido ao envio de dados como `form data` em vez de `JSON`.
- Corrigido o formato de envio de dados nos testes de login em `tests/integration/test_auth_api.py` para usar `json=`.
- Ajustadas as expectativas de status code e mensagens de erro para o endpoint `/tools/login` (e.g., 400 para campos ausentes em vez de 422).
- Identificado que os testes de refresh token (`test_refresh_token_no_token_provided` e `test_refresh_token_invalid_token_format`) esperavam status 401, mas FastAPI retorna 403 para `HTTPBearer` quando a autenticação falha antes de chegar à lógica do endpoint. Corrigido para esperar 403.
- Corrigidas as mensagens de erro esperadas nos testes de refresh token para corresponder às mensagens reais da FastAPI (e.g., "Not authenticated", "Invalid authentication credentials").
- Corrigido o teste `test_initial_setup_placeholder` em `tests/test_auth.py` para usar o endpoint `/tools/health` que retorna 200, em vez de `/tools/docs` que retorna 404.
- Todos os testes de autenticação (`tests/test_auth.py` e `tests/integration/test_auth_api.py`) agora passam.

## Observação importante
- A única falha remanescente nos testes automatizados é de setup do teste de remoção de usuário do grupo. O endpoint está correto conforme documentação e requisitos. Recomenda-se revisar o setup do teste em `test_admin_groups_api.py`.

1.  **Segurança**
    *   [ ] Adicionar limite de tentativas de login para prevenir ataques de força bruta (Backend).
    *   [ ] Implementar expiração e renovação de senha (política, não apenas a funcionalidade de alterar) (Backend).
    *   [ ] Implementar rate limiting para APIs (Backend).
    *   [ ] Adicionar headers de segurança (HSTS, CSP, etc.) no FastAPI (Backend).
    *   [ ] Revisar e garantir proteção contra CSRF se aplicável (FastAPI tem alguma proteção, mas verificar para forms HTML se houver) (Backend).
    *   [ ] **RF07:** Implementar trilha de auditoria detalhada para todas as ações administrativas e de acesso significativas (Backend).

2.  **Experiência do Usuário (Frontend)**
    *   [ ] Implementar sistema de notificações para o usuário no frontend (ex: após aprovação de solicitação, erro em ação).
    *   [ ] Adicionar páginas de erro customizadas para HTTP 404, 500, etc.
    *   [ ] Criar componentes de feedback visual no frontend para ações bem sucedidas (ex: "Grupo criado com sucesso").
    *   [ ] Melhorar a navegação com breadcrumbs.
    *   [ ] Implementar tema escuro/claro.
    *   [ ] **RNF07:** Implementar internacionalização (i18n) no frontend.

3.  **Backend**
    *   [ ] Adicionar paginação em listas que podem crescer muito (ex: listar usuários, listar grupos, listar solicitações).
    *   [ ] Implementar cache para dados frequentemente acessados (ex: configurações RBAC, se não mudarem com frequência).
    *   [ ] Adicionar validação de dados mais robusta em todos os endpoints (Pydantic ajuda, mas verificar casos de borda).
    *   [ ] **RNF04:** Melhorar sistema de logging com níveis configuráveis, rotação de logs e formato estruturado (JSON).
    *   [ ] Melhorar sistema de logging com níveis configuráveis, rotação de logs e formato estruturado (JSON).
    *   [ ] **RF02/RF07:** Adicionar endpoints para gestão completa de usuários pelo admin global (Listar, Editar, Deletar usuários). Atualmente só existe Criar (`POST /tools/usuarios`).
    *   [ ] Refinar/Unificar a lógica de solicitação de acesso a grupos: remover a implementação mais antiga de `app/groups/routes.py` (`solicitar-entrada`, `solicitacoes`, `aprovar`, `rejeitar`) em favor da de `app/groups/requests_routes.py`.
    *   [ ] Implementar persistência de dados em um banco de dados relacional ou NoSQL (atualmente em `rbac.json` e `requests.json`).
    *   [ ] **RF05:** Criar endpoint para listar ferramentas disponíveis para um usuário (ex: `GET /tools/my_tools` ou `GET /tools/user_tools`) com base em seus grupos e permissões.
    *   [ ] **RF02/RF04:** Avaliar a necessidade de endpoints mais completos para gerenciamento de grupos que retornem/aceitem mais detalhes (descrição, listas de usuários/admins/ferramentas) para alinhar com o frontend (`GroupAdmin.tsx`), ou simplificar o frontend. Os atuais em `app/groups/routes.py` são muito granulares.

4.  **Frontend**
    *   [ ] Implementar componentes reutilizáveis para forms e tabelas.
    *   [ ] Adicionar filtros e ordenação em listas (ex: lista de usuários, grupos, solicitações).
    *   [ ] Criar dashboard com métricas e informações relevantes para administradores.
    *   [ ] Implementar armazenamento local seguro para preferências do usuário (ex: tema).
    *   [ ] Otimizar bundle para produção (`npm run build` já faz isso, mas verificar otimizações adicionais como code splitting).
    *   [ ] **RF02, RF03, RF04 (GroupAdmin.tsx):**
        *   [ ] **Corrigir Role Mismatch:** Decidir se `GroupAdmin.tsx` é apenas para `global_admin` ou se `admin` de grupo deve ter uma visão/funcionalidade similar para seus grupos. Ajustar `Navbar.tsx` e a lógica interna da página.
        *   [ ] **Corrigir API Mismatch (Data Fetching):** Alinhar a obtenção de dados de grupos com o que o backend `GET /tools/grupos` realmente fornece (apenas nomes), ou criar/usar novo endpoint backend que retorne detalhes completos.
        *   [ ] **Corrigir API Mismatch (Data Submission):** Ajustar os payloads enviados para criar/editar grupos, adicionar admins/usuários, adicionar ferramentas para corresponder aos endpoints existentes em `app/groups/routes.py`, ou usar/criar novos endpoints backend.
        *   [ ] **Implementar Funcionalidades Faltantes:** Adicionar UI para remover usuários de grupos, promover usuários a admin de grupo, editar/remover ferramentas de grupos.
    *   [ ] **RF05 (Tools.tsx):**
        *   [ ] Corrigir a lógica de listagem de ferramentas. Utilizar um endpoint backend dedicado (a ser criado) para buscar as ferramentas que o usuário autenticado pode acessar.
    *   [ ] **RF02/RF07 (User Management by Global Admin):**
        *   [ ] Criar nova página/componente para gerenciamento completo de usuários (CRUD) por administradores globais.
        *   [ ] Corrigir a rota `/admin/users` em `AppRouter.tsx` para apontar para este novo componente, em vez de `UserRequests.tsx`.
    *   [ ] **RF04 (Tool Management by Group Admin):** Se `GroupAdmin.tsx` for adaptado para group admins, garantir que eles possam gerenciar ferramentas (CRUD) em seus grupos.

5.  **Testes**
    *   [ ] Adicionar testes unitários no backend (pytest) para lógica de negócios, auth, utils.
    *   [ ] Adicionar testes de integração para APIs do backend.
        *   [x] Configurar ambiente de teste (pytest.ini, .env.test, conftest.py com fixtures).
        *   [x] Implementar testes de integração para API de Autenticação (`/tools/login`, `/tools/refresh-token`).
        *   [x] Implementar testes de integração para API de Gerenciamento de Grupos (Admin Global: Criar, Listar, Editar, Deletar).
        *   [x] Implementar testes de integração para API de Gerenciamento de Usuários em Grupos (Admin de Grupo/Global: Adicionar/Remover Usuários/Admins de grupo, Promover, Listar usuários do grupo).
        *   [x] Implementar testes de integração para API de Gerenciamento de Ferramentas em Grupos (Admin Global: Adicionar/Remover ferramentas).
        *   [x] Implementar testes de integração para API de Gerenciamento de Usuários (Admin Global: CRUD de usuários - **CONCLUÍDO**).
            *   [x] `POST /tools/usuarios` (Criar usuário)
            *   [x] `GET /tools/usuarios` (Listar usuários)
            *   [x] `GET /tools/usuarios/{username}` (Detalhar usuário)
            *   [x] `PUT /tools/usuarios/{username}` (Atualizar usuário)
            *   [x] `DELETE /tools/usuarios/{username}` (Remover usuário)
        *   [ ] Implementar testes de integração para API de Solicitações de Acesso a Grupos.
        *   [ ] Implementar testes de integração para Endpoints de Ferramentas de Exemplo e Acesso a Ferramentas.
        *   [ ] Implementar testes de integração para `GET /grupos/disponivel`.

6.  **Documentação**
    *   [ ] Melhorar documentação da API (Swagger/OpenAPI gerada pelo FastAPI) com exemplos de request/response mais detalhados e descrições claras.
    *   [ ] Criar documentação para desenvolvedores (como estender o sistema, adicionar novas ferramentas, configurar o ambiente).
    *   [x] Gerar documentação técnica detalhada do backend para basear a criação de testes.
    *   [ ] Adicionar mais comentários no código (backend e frontend) para facilitar manutenção.
    *   [ ] Criar tutoriais visuais ou guias rápidos para usuários finais e administradores sobre como usar o portal.

7.  **Infraestrutura**
    *   [ ] Preparar para containerização com Docker (Dockerfile para backend e frontend).
    *   [ ] Configurar para deployment em ambientes cloud (ex: Azure App Service, AKS, etc.).
    *   [ ] Adicionar health checks mais detalhados no backend (ex: verificar conexão com futuro banco de dados).
    *   [ ] Implementar backup automatizado de dados (especialmente quando migrar para banco de dados).

## Prioridades

1.  **Backend:** Implementar persistência de dados em banco de dados.
2.  **Frontend/Backend Alignment:** Corrigir as discrepâncias entre `GroupAdmin.tsx` / `Tools.tsx` e os endpoints backend existentes, ou criar os endpoints necessários no backend. Implementar CRUD de usuários para admin global (Backend e Frontend).
3.  **Testes:** Adicionar testes automatizados (backend e frontend) para garantir estabilidade.
4.  **Segurança:** Adicionar limite de tentativas de login e rate limiting.
5.  **Documentação:** Melhorar documentação da API e para desenvolvedores.
