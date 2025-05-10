# Arquitetura do Sistema – MCP Gateway

Este documento apresenta a visão técnica e os principais componentes da arquitetura do MCP Gateway.
*(Atualizado em 2025-05-10 para refletir o estado atual do projeto)*

---

## Sumário
- [Visão Geral](#visão-geral)
- [Componentes Principais](#componentes-principais)
  - [Backend (FastAPI)](#backend-fastapi)
  - [Frontend (React + Vite)](#frontend-react--vite)
  - [Persistência de Dados](#persistência-de-dados)
- [Diagrama de Componentes (alto nível)](#diagrama-de-componentes-alto-nível)
- [Fluxos Principais](#fluxos-principais)
- [Decisões Técnicas Chave](#decisões-técnicas-chave)
- [Pontos de Extensão e Melhorias Futuras](#pontos-de-extensão-e-melhorias-futuras)
- [Observações e Boas Práticas](#observações-e-boas-práticas)

---

## Visão Geral
O MCP Gateway é uma aplicação web desenhada para gerenciar o acesso a ferramentas e recursos de forma centralizada, utilizando um modelo de controle de acesso baseado em papéis (RBAC) e grupos.

---

## Componentes Principais

### Backend (FastAPI)
- **Linguagem:** Python
- **Framework:** FastAPI
- **Responsabilidades:**
    - Autenticação e autorização (JWT, RBAC).
    - Definição e exposição de APIs RESTful para gerenciamento de usuários, grupos, ferramentas e solicitações de acesso.
    - Lógica de negócio principal.
    - Servir os arquivos estáticos do frontend buildado.
- **Módulos Chave:**
    - `app/main.py`: Ponto de entrada da aplicação, configuração dos routers.
    - `app/auth.py`: Lógica de autenticação, geração e validação de JWT, hashing de senhas.
    - `app/config.py`: Configurações da aplicação.
    - `app/groups/routes.py`: Endpoints principais para gerenciamento de grupos, usuários em grupos, ferramentas em grupos, e funcionalidades de usuário (login, alteração de senha, etc.). Inclui também endpoints de administração global de usuários.
    - `app/groups/requests_routes.py`: Endpoints dedicados ao workflow de solicitação de acesso a grupos (criar, listar, aprovar/rejeitar).
    - `app/models/`: Definições de modelos Pydantic para validação de dados e schemas de API.
    - `app/utils/`: Utilitários para RBAC, gerenciamento de senhas, manipulação de arquivos JSON de dados.

### Frontend (React + Vite)
- **Linguagem:** TypeScript
- **Framework/Lib:** React
- **Build Tool:** Vite
- **Responsabilidades:**
    - Interface de usuário para interação com o sistema.
    - Consumo das APIs do backend para exibir dados e executar ações.
    - Gerenciamento de estado local e contexto de autenticação.
- **Estrutura Chave (dentro de `frontend/src/`):**
    - `main.tsx`: Ponto de entrada da aplicação React.
    - `App.tsx`, `AppRouter.tsx`: Componentes principais e roteamento.
    - `pages/`: Componentes de página (Dashboard, Login, UserRequests, RequestsAdmin, etc.).
    - `components/`: Componentes reutilizáveis (Navbar, ProtectedRoute, LoadingSpinner).
    - `contexts/`: Contextos globais (AuthContext, ErrorContext).
    - `services/`: Lógica para interagir com a API backend.

### Persistência de Dados
- **Formato Atual:** Arquivos JSON.
    - `data/rbac.json`: Armazena informações sobre usuários (credenciais, papéis, grupos), grupos (membros, admins, ferramentas) e definições de ferramentas.
    - `data/requests.json`: Armazena as solicitações de acesso a grupos.
- **Observação:** Esta abordagem é para simplicidade inicial e desenvolvimento. Uma migração para um sistema de banco de dados (SQL ou NoSQL) é planejada para ambientes de produção e maior escalabilidade (ver [Pontos de Extensão](#pontos-de-extensão-e-melhorias-futuras)).

---

## Diagrama de Componentes (alto nível)
```text
+------------------+     HTTP/S     +-------------------+     Leitura/Escrita     +------------------------+
|      Usuário     | <------------> |  Frontend (React) | <-------------------> |   Backend (FastAPI)    |
| (Navegador Web)  |                +-------------------+                       +------------------------+
+------------------+                                                                      |
                                                                                           | Leitura/Escrita
                                                                                           V
                                                                                +------------------------+
                                                                                |   Dados (JSON Files)   |
                                                                                | - rbac.json            |
                                                                                | - requests.json        |
                                                                                +------------------------+
```

---

## Fluxos Principais
- **Login de Usuário:**
    1. Usuário insere credenciais no Frontend.
    2. Frontend envia para `POST /tools/login` no Backend.
    3. Backend valida credenciais (comparando com `rbac.json`, suportando senhas em texto plano legadas e hashes bcrypt).
    4. Se válido, Backend gera um JWT (contendo `username`, `papel`, `grupos`) e retorna ao Frontend.
    5. Frontend armazena o JWT e atualiza o estado de autenticação.
- **Gerenciamento (Ex: Admin Global criando um Grupo):**
    1. Admin Global navega para a funcionalidade no Frontend.
    2. Frontend envia uma requisição autenticada (com JWT) para `POST /tools/grupos` no Backend.
    3. Backend valida o JWT, verifica as permissões do `global_admin`.
    4. Backend processa a criação do grupo, atualizando `rbac.json`.
    5. Backend retorna uma resposta de sucesso/erro ao Frontend.
- **Solicitação de Acesso a Grupo:**
    1. Usuário logado visualiza grupos disponíveis (via `GET /tools/grupos/disponivel`).
    2. Usuário submete uma solicitação para um grupo via Frontend.
    3. Frontend envia para `POST /tools/requests/` no Backend.
    4. Backend cria um novo registro de solicitação em `requests.json` com status "pending".
    5. Administrador (do grupo ou global) visualiza solicitações pendentes (via `GET /tools/requests/admin`).
    6. Administrador aprova/rejeita a solicitação via Frontend, que chama `POST /tools/requests/{request_id}/review`.
    7. Se aprovado, Backend atualiza `requests.json` e adiciona o usuário ao grupo em `rbac.json`.
- **Consumo de Ferramenta:**
    1. Usuário logado acessa uma lista de suas ferramentas (via `GET /user_tools` no Frontend).
    2. Ao tentar usar uma ferramenta, Frontend faz uma requisição autenticada para o endpoint da ferramenta (ex: `GET /tools/ferramenta_x`).
    3. Backend valida o JWT e verifica se o usuário (ou um de seus grupos) tem permissão para acessar a ferramenta.
    4. Se permitido, a lógica da ferramenta é executada.
- **Build e Deploy (Simplificado):**
    1. Frontend é buildado (`npm run build` em `frontend/`) gerando arquivos estáticos em `frontend/dist/`.
    2. O Backend FastAPI é configurado para servir esses arquivos estáticos.

---

## Decisões Técnicas Chave
- **Backend Framework - FastAPI:** Escolhido por sua performance, facilidade de uso, tipagem moderna com Python, e geração automática de documentação OpenAPI (Swagger/ReDoc).
- **Frontend Framework - React com Vite:** React pela popularidade e ecossistema. Vite pela experiência de desenvolvimento rápida e build otimizado. TypeScript para tipagem estática.
- **Autenticação - JWT:** Para permitir autenticação stateless e segura entre Frontend e Backend.
- **Autorização - RBAC:** Implementado programaticamente com base nos papéis (`user`, `admin`, `global_admin`) e associações de grupo definidas em `rbac.json`.
- **Persistência Inicial - Arquivos JSON:** Adotada para simplicidade de setup e desenvolvimento inicial, com a intenção clara de evoluir para um banco de dados mais robusto.
- **Modularidade:** Separação de responsabilidades entre Frontend e Backend, e dentro do Backend (ex: `routes.py` vs `requests_routes.py`) para facilitar manutenção e escalabilidade.

---

## Pontos de Extensão e Melhorias Futuras
Conforme listado em `docs/TODO.md` e `docs/REQUISITOS.md`:
- **Persistência de Dados:** Migrar de arquivos JSON para um sistema de banco de dados (ex: PostgreSQL, MongoDB) para melhor performance, concorrência e integridade de dados.
- **Segurança Avançada:** Implementar limite de tentativas de login, expiração de senha, rate limiting, headers de segurança (CSP, HSTS), trilha de auditoria completa (RF07).
- **Testes:** Expandir a cobertura de testes unitários e de integração para Backend e Frontend.
- **CI/CD:** Configurar pipelines de Integração Contínua e Deploy Contínuo.
- **Containerização:** Dockerizar a aplicação (Backend e Frontend) para facilitar o deploy.
- **Integração SSO:** Permitir autenticação via provedores de identidade corporativos (ex: Azure AD).
- **Melhorias de UI/UX:** Notificações, páginas de erro customizadas, tema escuro/claro, internacionalização (RNF07).
- **Logging Avançado:** Implementar sistema de logging estruturado e configurável (RNF04).

---

## Observações e Boas Práticas
- Mantenha este documento atualizado conforme a arquitetura evolui. Mudanças significativas na estrutura, adição de novos componentes principais ou alteração nos fluxos devem ser refletidas aqui.
- Utilize diagramas mais detalhados (ex: sequência, componentes específicos) conforme necessário para explicar partes complexas do sistema.
- Vincule decisões arquiteturais a requisitos (funcionais e não-funcionais) sempre que possível.
- Revise este documento colaborativamente com a equipe para garantir um entendimento compartilhado.

---

*Este documento deve ser revisado e atualizado periodicamente conforme a arquitetura evoluir.*
