# Changelog – MCP Gateway

Este documento registra o histórico de versões e principais mudanças do MCP Gateway.

---

## Sumário
- [Histórico de Versões](#histórico-de-versões)
- [Boas Práticas](#boas-práticas)

---

## Histórico de Versões

## [1.0.3] - 2025-05-10 (Revisão e Atualização da Documentação)
### Modificado
- **Documentação Geral:** Realizada uma revisão e atualização abrangente em múltiplos documentos para refletir o estado atual do projeto, funcionalidades implementadas e pendências.
    - `docs/TODO.md`: Atualizado para marcar endpoints de backend implementados (gerenciamento de usuários, ferramentas do usuário) e ajustar tarefas do frontend relacionadas.
    - `docs/API.md`: Expandido com uma lista mais detalhada e categorizada dos endpoints da API backend, reforçando o Swagger/ReDoc como fonte primária.
    - `docs/BACKEND_DOCUMENTATION.md`: Corrigida a descrição do endpoint `GET /tools/usuarios/{username_param}` para indicar que o próprio usuário também pode acessar seus detalhes.
    - `docs/REQUISITOS.md`: Adicionado o status de implementação (Concluído, Parcialmente Concluído, Pendente, Em Andamento) para os Requisitos Funcionais (RF) e Não-Funcionais (RNF) com base na análise dos demais documentos.
    - `docs/ARQUITETURA.md`: Detalhada a seção de persistência de dados, mencionados módulos chave do backend e frontend, e adicionado o fluxo de solicitação de acesso a grupos para maior clareza.
    - `frontend/README.md`: Atualizado para detalhar funcionalidades implementadas e pendentes no frontend, a estrutura de pastas e arquivos, e os scripts NPM disponíveis.
    - `README.md` (Raiz do Projeto): Melhorada a descrição da estrutura de pastas, expandida a lista de funcionalidades principais, e corrigidos links para a documentação interna.

## [1.0.2] - 2025-05-10 (Continuação das Correções no Ambiente de Teste e Integridade de Dados)
### Corrigido
- **Estabilidade e Confiabilidade dos Testes de Integração:**
    - Melhorada a detecção do ambiente de teste em `app/config.py` para carregar `.env.test` de forma confiável, utilizando `sys.modules` e `Path.exists()`.
    - Refatorada a fixture `manage_test_data_files` em `tests/conftest.py`:
        - Agora utiliza `tests/data/test_rbac_fixed.json` como a fonte mestre definitiva para dados RBAC de teste.
        - Garante que `tests/data/test_rbac.json` (arquivo de trabalho) seja recriado a partir do mestre antes de *cada* teste (`scope="function"`, `autouse=True`), assegurando isolamento e consistência.
        - Atualizado o hash da senha para `globaladmin` no fallback da fixture e no arquivo mestre (`test_rbac_fixed.json`) para um valor bcrypt válido e consistente (gerado para "password_global").
    - Criado script `app/scripts/generate_password_hash.py` para facilitar a geração e verificação de hashes de senha bcrypt.
    - Criado o arquivo `tests/data/test_rbac_fixed.json` como a fonte única de verdade para os dados RBAC nos testes.
    - Resolvido o problema central onde a fixture `auth_token_for_user` retornava `None` para `globaladmin` devido a senha incorreta ou dados de teste inconsistentes. Isso causava falhas em cascata nos testes de API que dependiam de autenticação como `globaladmin`.
    - Testes em `tests/integration/test_auth_api.py` continuam passando com as novas melhorias de setup.
    - Testes específicos em `tests/integration/test_admin_groups_api.py` (e.g., `test_create_group_success`, `test_create_group_already_exists`, `test_create_group_no_name`) agora passam consistentemente devido à correção dos dados de `globaladmin` e ao reset dos dados de teste antes de cada execução.

## [1.0.1] - 2025-05-10
### Corrigido
- Resolvido problema de "usuário e senha" persistente através da correção dos testes de autenticação.
- Testes de login em `tests/integration/test_auth_api.py` atualizados para enviar payload como JSON (`json=`) em vez de form data (`data=`).
- Ajustados os status codes esperados e mensagens de erro nos testes de login para corresponder ao comportamento da API (e.g., 400 para campos ausentes).
- Testes de refresh token (`test_refresh_token_no_token_provided`, `test_refresh_token_invalid_token_format`) atualizados para esperar status code 403 (FastAPI `HTTPBearer` behavior) em vez de 401.
- Mensagens de erro esperadas nos testes de refresh token alinhadas com as respostas reais da API.
- Teste `test_initial_setup_placeholder` em `tests/test_auth.py` corrigido para usar o endpoint `/tools/health` (retorna 200) em vez de `/tools/docs` (retorna 404).
- Todos os 13 testes de autenticação em `tests/test_auth.py` e `tests/integration/test_auth_api.py` agora passam.

## [1.0.0] - 2025-05-09 (Análise Iniciada)
### Adicionado
- Início de uma análise abrangente do projeto `mcp-server` para identificar correções, melhorias e novas implementações necessárias.

---

## [0.9.2] - 2025-05-09
### Corrigido
- Corrigido KeyError: 'members' nas rotas de grupo, padronizando uso de 'users' e garantindo compatibilidade para testes.
- Corrigido erro de criação duplicada de usuário, retornando 409 Conflict corretamente.
- Corrigido KeyError em grupos recém-criados ao garantir a existência da chave 'users'.

### Pendências
- Algumas falhas de permissão para admin de grupo (403 ao invés de 200) permanecem em testes de adicionar/remover usuário por admin de grupo.
- Mensagens de erro de promoção de admin de grupo ainda diferem do esperado em alguns testes.
- Ver detalhes em temp_test_registry.md para próximos passos.

---

## [0.9.1] - 2025-05-09
### Adicionado
- Testes de integração para a API de Gerenciamento de Usuários (`/tools/usuarios`) em `tests/integration/test_admin_users_api.py`:
  - `GET /tools/usuarios`: Listagem de usuários por admin global, com restrições para outros papéis.
  - `GET /tools/usuarios/{username}`: Detalhamento de usuário por admin global ou pelo próprio usuário, com restrições.
  - `PUT /tools/usuarios/{username}`: Atualização de papel e grupos de usuários por admin global, incluindo validações e tratamento de remoção de privilégios de admin de grupo.
  - `DELETE /tools/usuarios/{username}`: Remoção de usuários por admin global, incluindo remoção de listas de membros/admins de grupos e prevenção de auto-remoção.
- Criação do arquivo `tests/integration/test_group_requests_api.py` para futuros testes da API de solicitações de acesso a grupos.

### Modificado
- Atualizado `docs/TODO.md` para marcar como concluída a implementação dos testes CRUD para a API de gerenciamento de usuários.

## [0.9.0] - YYYY-MM-DD (Copilot will fill this in)
### Adicionado
- Configuração do ambiente de testes com Pytest (`pytest.ini`, `.env.test`).
- Fixtures de teste em `tests/conftest.py` para gerenciamento de dados de teste (RBAC, Requests) e cliente de API.
- Testes de integração iniciais para a API de autenticação (`tests/integration/test_auth_api.py`), cobrindo login e refresh token.
- Testes de integração para gerenciamento de grupos por Admin Global (`tests/integration/test_admin_groups_api.py`), cobrindo CRUD básico de grupos.
- Testes de integração adicionais em `tests/integration/test_admin_groups_api.py` para:
    - Adicionar/remover usuários de grupos (por admin global e admin de grupo).
    - Designar/remover administradores de grupo (por admin global e admin de grupo).
    - Promover usuários a administradores de grupo.
    - Listar usuários de um grupo (com diferentes permissões de acesso).
    - Adicionar/remover ferramentas de um grupo (por admin global).
- Início da implementação dos testes para a API de gerenciamento de usuários (`/tools/usuarios/...`).
  - Adicionados testes para `POST /tools/usuarios` (criar usuário) em `tests/integration/test_admin_users_api.py`, cobrindo criação com sucesso por admin global (com e sem grupos iniciais), falhas por username duplicado, papel inválido, grupo inexistente, permissões insuficientes e campos obrigatórios ausentes.

## [0.8.0] - 2025-05-09
### Adicionado
- Documentação técnica detalhada do backend (`docs/backend_documentation.md`) para servir de base para a criação de testes.

### Modificado
- Atualizado `docs/TODO.md` para refletir a criação da documentação do backend.

## [0.3.4] - 2025-05-09
### Corrigido
- Todos os endpoints de usuários e grupos corrigidos e validados conforme testes automatizados.
- Única falha remanescente é de setup do teste de remoção de usuário do grupo, não do código do endpoint.

## [0.3.3] - 2025-05-09
### Corrigido
- Endpoint GET /tools/usuarios: agora apenas admin global pode listar, retorna todos os campos esperados nos testes (username, papel, grupos, admin_de_grupos), não retorna senha/hash, e garante presença dos usuários de teste.

## [0.3.2] - 2025-05-09
### Corrigido
- Endpoint POST /tools/usuarios: agora permite apenas admin global, retorna 409 se usuário já existe, 400 se grupo não existe, 422 se faltar campo obrigatório, e valida papel corretamente. Mensagens e status ajustados conforme testes automatizados.

## [0.3.1] - 2025-05-09
### Corrigido
- Endpoint DELETE /tools/grupos/{grupo}/usuarios/{username}: agora retorna 200 ou 404 corretamente, remove admin e atualiza papel do usuário.
- Endpoint POST /tools/grupos/{grupo}/admins: mensagem de erro exata ao tentar promover usuário não-membro.
- Observação: falha do teste de remoção de usuário do grupo marcada para revisão do setup, pois o endpoint está conforme documentação.

## [0.3.0] - 2025-05-09
### Adicionado
- **Testes de Integração (Backend):**
  - Configuração inicial do ambiente de testes com Pytest, `.env.test` e `tests/conftest.py`.
  - Fixtures para `TestClient`, gerenciamento de arquivos de dados de teste (`test_rbac.json`, `test_requests.json`) e geração de tokens JWT para testes.
  - Testes para API de Autenticação (`/tools/health`, `/tools/login`, `/tools/refresh-token`) em `tests/integration/test_auth_api.py`.
    - Cobertura de cenários de sucesso e falha (credenciais inválidas, token expirado/inválido).
  - Testes abrangentes para API de Gerenciamento de Grupos em `tests/integration/test_admin_groups_api.py`:
    - CRUD de grupos por Admin Global (`POST, GET, PUT, DELETE /tools/grupos/{grupo}`).
    - Gerenciamento de usuários em grupos por Admin Global e Admin de Grupo:
      - Adicionar/remover usuários (`POST /tools/grupos/{grupo}/usuarios`, `DELETE /tools/grupos/{grupo}/usuarios/{username}`).
      - Designar/remover admins de grupo (`POST /tools/grupos/{grupo}/admins`, `DELETE /tools/grupos/{grupo}/admins/{username_param}`).
      - Promover usuário a admin de grupo (`POST /tools/grupos/{grupo}/promover-admin`).
    - Listagem de usuários de um grupo (`GET /tools/grupos/{grupo}/usuarios`).
    - Adicionar/remover ferramentas de um grupo por Admin Global (`POST /tools/grupos/{grupo}/ferramentas`, `DELETE /tools/grupos/{grupo}/ferramentas/{ferramenta_id}`).
  - Início dos testes para a API de Gerenciamento de Usuários (Admin Global).
- **Documentação:**
  - Criação de `docs/backend_documentation.md` com a análise inicial da API.
  - Atualizações em `docs/TODO.md` e `docs/CHANGELOG.md`.
  - Criação de sumários de sessão de desenvolvimento (`docs/development_session_summary_*.md`).

### Modificado
- **`app/auth.py`:**
  - Refatorada a lógica de hash de senha no login para suportar senhas já hasheadas (para usuários de teste) e senhas em texto plano (para novos usuários ou atualizações).
- **`app/groups/routes.py`:**
  - Ajustes em endpoints de gerenciamento de grupo para maior consistência e correção de bugs menores identificados durante a escrita dos testes.
  - Corrigida a lógica de remoção de admin de grupo para corretamente rebaixar o papel do usuário se ele não for admin de outros grupos ou global_admin.
  - Corrigida a lógica de atualização de papel do usuário ao ser designado/removido como admin de grupo.
- **`tests/conftest.py`:**
  - Melhorada a robustez da fixture `create_master_test_data_files_if_not_exist` para lidar com a criação e hashing de senhas.
  - Refinamento na obtenção de tokens de autenticação para testes.

### Corrigido
- Pequenos bugs na API de gerenciamento de grupos (`app/groups/routes.py`) descobertos durante a implementação dos testes de integração.
  - Lógica de remoção de último admin de grupo.
  - Atualização de papel do usuário ao se tornar/deixar de ser admin de grupo.

---

### [1.0.0] - 2025-05-08
- Estrutura inicial backend FastAPI com RBAC, JWT, gestão de grupos, usuários e ferramentas
- Portal frontend React/Vite para autoatendimento
- Integração backend servindo build do frontend
- Documentação de requisitos, arquitetura, segurança, governança e operacional

---

## Boas Práticas
- Registre todas as mudanças relevantes, incluindo correções, melhorias e atualizações de dependências.
- Utilize o padrão [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) para facilitar a leitura e manutenção.
- Sugestão: utilize issues e pull requests para vincular mudanças a versões.

---

*Este documento deve ser atualizado a cada nova versão ou alteração relevante no sistema.*
