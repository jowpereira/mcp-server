# API MCP Gateway

Esta documentação apresenta os principais endpoints e exemplos de uso da API do MCP Gateway. A documentação OpenAPI/Swagger é gerada automaticamente pelo FastAPI em `/docs` e a documentação ReDoc em `/redoc`.

---

## Sumário
- [Endpoints Principais](#endpoints-principais)
  - [Autenticação e Sessão](#autenticação-e-sessão)
  - [Gerenciamento de Grupos (Admin Global)](#gerenciamento-de-grupos-admin-global)
  - [Gerenciamento de Usuários em Grupos (Admin Global / Admin de Grupo)](#gerenciamento-de-usuários-em-grupos-admin-global--admin-de-grupo)
  - [Gerenciamento de Ferramentas em Grupos (Admin Global / Admin de Grupo)](#gerenciamento-de-ferramentas-em-grupos-admin-global--admin-de-grupo)
  - [Gerenciamento de Usuários (Admin Global)](#gerenciamento-de-usuários-admin-global)
  - [Funcionalidades do Usuário](#funcionalidades-do-usuário)
  - [Descoberta de Grupos e Ferramentas](#descoberta-de-grupos-e-ferramentas)
  - [Solicitações de Acesso a Grupos](#solicitações-de-acesso-a-grupos)
  - [Infraestrutura e Exemplos](#infraestrutura-e-exemplos)
- [Exemplos de Uso](#exemplos-de-uso)
- [Observações e Boas Práticas](#observações-e-boas-práticas)

---

## Endpoints Principais

A seguir, uma lista mais detalhada dos endpoints. Para payloads, respostas e todos os detalhes, consulte `/docs` ou `/redoc`.

### Autenticação e Sessão
- `POST /tools/login` — Login de usuário, retorna JWT.
- `POST /tools/refresh-token` — Renova um token JWT para o usuário autenticado.

### Gerenciamento de Grupos (Admin Global)
- `GET /tools/grupos` — Lista todos os grupos com detalhes.
- `POST /tools/grupos` — Cria um novo grupo.
- `PUT /tools/grupos/{grupo}` — Edita nome e/ou descrição de um grupo.
- `DELETE /tools/grupos/{grupo}` — Remove um grupo.

### Gerenciamento de Usuários em Grupos (Admin Global / Admin de Grupo)
- `POST /tools/grupos/{grupo}/admins` — Designa um usuário como administrador de um grupo (Admin Global).
- `DELETE /tools/grupos/{grupo}/admins/{username_param}` — Remove um administrador de um grupo.
- `POST /tools/grupos/{grupo}/usuarios` — Adiciona um usuário a um grupo.
- `DELETE /tools/grupos/{grupo}/usuarios/{username}` — Remove um usuário de um grupo.
- `POST /tools/grupos/{grupo}/promover-admin` — Promove um membro do grupo a administrador do grupo.
- `GET /tools/grupos/{grupo}/usuarios` — Lista administradores e usuários de um grupo.

### Gerenciamento de Ferramentas em Grupos (Admin Global / Admin de Grupo)
- `POST /tools/grupos/{grupo}/ferramentas` — Adiciona uma ferramenta existente (global) a um grupo.
- `DELETE /tools/grupos/{grupo}/ferramentas/{tool_id}` — Remove uma ferramenta de um grupo.

### Gerenciamento de Usuários (Admin Global)
- `POST /tools/usuarios` — Cria um novo usuário.
- `GET /tools/usuarios` — Lista todos os usuários.
- `GET /tools/usuarios/{username_param}` — Obtém detalhes de um usuário específico.
- `PUT /tools/usuarios/{username_param}` — Atualiza o papel e/ou grupos de um usuário.
- `DELETE /tools/usuarios/{username_param}` — Deleta um usuário.
- `POST /tools/admin/migrate-passwords` — Migra senhas em texto plano para hashes bcrypt.

### Funcionalidades do Usuário
- `POST /tools/usuarios/alterar-senha` — Permite ao usuário logado alterar sua própria senha.
- `GET /tools/usuarios/requisitos-senha` — Retorna os requisitos de segurança para senhas.

### Descoberta de Grupos e Ferramentas
- `GET /tools/grupos/disponivel` — Lista grupos dos quais o usuário logado não faz parte (para solicitar acesso).
- `GET /tools/ferramentas` — Lista todas as ferramentas definidas globalmente no sistema.
- `GET /user_tools` — Lista todas as ferramentas que o usuário logado pode acessar.

### Solicitações de Acesso a Grupos
- `POST /tools/requests/` — Cria uma nova solicitação de acesso a um grupo.
- `GET /tools/requests/me` — Lista todas as solicitações do usuário atual.
- `GET /tools/requests/admin` — Lista solicitações pendentes para admin/global_admin.
- `GET /tools/requests/{request_id}` — Obtém detalhes de uma solicitação específica.
- `POST /tools/requests/{request_id}/review` — Aprova ou rejeita uma solicitação de acesso.

### Infraestrutura e Exemplos
- `GET /tools/health` — Healthcheck da aplicação.
- `GET /tools/ferramenta_x` — Exemplo de execução de ferramenta X (usuário autorizado).
- `GET /tools/ferramenta_y` — Exemplo de execução de ferramenta Y (usuário autorizado).
- `GET /tools/ferramenta_z` — Exemplo de execução de ferramenta Z (usuário autorizado).

---

## Exemplos de Uso
Veja exemplos de payloads e respostas diretamente no Swagger (`/docs`) ou ReDoc (`/redoc`).

---

## Observações e Boas Práticas
- Para detalhes completos, incluindo schemas de request/response, códigos de status e mensagens de erro, **consulte sempre a documentação automática do FastAPI em `/docs` (Swagger) ou `/redoc` (ReDoc)**. Esta documentação em Markdown é um resumo.
- Mantenha os endpoints documentados e atualizados conforme a evolução da API.
- Utilize JWT para autenticação em todas as requisições protegidas.
- Sugestão: utilize issues e pull requests para propor alterações nesta documentação.

---

*Este documento deve ser revisado e atualizado periodicamente conforme a API evoluir, mas a fonte primária de verdade para a API é a documentação gerada automaticamente.*
