# Changelog – MCP Gateway

Este documento registra o histórico de versões e principais mudanças do MCP Gateway.

---

## Sumário
- [Histórico de Versões](#histórico-de-versões)
- [Boas Práticas](#boas-práticas)

---

## Histórico de Versões

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
