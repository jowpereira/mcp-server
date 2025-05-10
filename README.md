# MCP Gateway – API & Portal de Autoatendimento

Este repositório contém o MCP Gateway, uma solução corporativa para expor, gerenciar e consumir ferramentas (APIs internas) de forma segura, escalável e auditável, com autenticação RBAC e portal de autoatendimento.
*(Atualizado em 2025-05-10 para refletir o estado atual do projeto)*

---

## Sumário
- [Visão Geral](#visão-geral)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Como Rodar (Desenvolvimento)](#como-rodar-desenvolvimento)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Exemplo de Estrutura RBAC](#exemplo-de-estrutura-rbac)
- [Segurança](#segurança)
- [Documentação da API](#documentação-da-api)
- [Requisitos do Sistema](#requisitos-do-sistema)
- [Documentação Completa](#documentação-completa)
- [Boas Práticas e Observações](#boas-práticas-e-observações)

---

## Visão Geral
O MCP Gateway é composto por:
- **Backend:** FastAPI (Python) responsável pela lógica de negócio, autenticação (JWT), autorização (RBAC), e exposição de APIs RESTful. Atualmente, persiste dados em arquivos JSON, com planos de migração para um banco de dados mais robusto.
- **Frontend:** React (Vite + TypeScript) como portal de autoatendimento, consumindo as APIs do backend. O build de produção do frontend é servido estaticamente pelo backend FastAPI.

---

## Estrutura de Pastas
```text
mcp-server/
├── app/                      # Código-fonte do Backend FastAPI
│   ├── main.py             # Ponto de entrada da aplicação FastAPI
│   ├── config.py           # Configurações da aplicação
│   ├── auth.py             # Lógica de autenticação, JWT, hashing
│   ├── utils/              # Utilitários (RBAC, validadores, gerenciadores)
│   ├── models/             # Modelos Pydantic (schemas de dados)
│   │   ├── __init__.py
│   │   └── requests.py       # Modelos para solicitações de acesso
│   ├── groups/             # Módulo para rotas relacionadas a grupos e usuários
│   │   ├── __init__.py
│   │   ├── routes.py       # Rotas principais (usuários, grupos, ferramentas)
│   │   ├── requests_routes.py # Rotas para solicitações de acesso a grupos
│   │   └── tools.py        # Utilitários de permissão (legado ou específico)
│   └── scripts/            # Scripts utilitários (ex: gerar hash de senha)
├── data/                   # Dados persistentes (temporário, para desenvolvimento)
│   ├── rbac.json           # Configurações de usuários, grupos, papéis, ferramentas
│   └── requests.json       # Dados das solicitações de acesso a grupos
├── docs/                   # Documentação do projeto
├── frontend/               # Código-fonte do Portal Frontend React (Vite)
│   ├── src/                # Código-fonte React/TypeScript
│   ├── public/             # Arquivos públicos para o frontend
│   ├── dist/               # Build de produção do frontend (servido pelo FastAPI)
│   ├── package.json        # Dependências e scripts do frontend
│   └── README.md           # Documentação específica do frontend
├── tests/                  # Testes automatizados (Pytest)
│   ├── conftest.py         # Configurações e fixtures globais para testes
│   ├── integration/        # Testes de integração da API
│   └── data/               # Arquivos de dados para os testes
├── requirements.txt        # Dependências Python do backend
├── pytest.ini              # Configuração do Pytest
└── README.md               # Este documento (visão geral do projeto)
```

---

## Como Rodar (Desenvolvimento)

### 1. Backend (FastAPI)
No diretório raiz `mcp-server/`:
```powershell
# Crie e ative um ambiente virtual (recomendado)
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate # Linux/macOS

# Instale as dependências
pip install -r requirements.txt

# Rode o servidor de desenvolvimento
uvicorn app.main:app --reload
```
O backend estará disponível em `http://localhost:8000`.

### 2. Frontend (React)
Em um novo terminal, navegue até o diretório `frontend/`:
```powershell
cd frontend

# Instale as dependências
npm install

# Rode o servidor de desenvolvimento do frontend
npm run dev
```
O frontend estará disponível em `http://localhost:5173` (ou outra porta, se a 5173 estiver ocupada) e fará requisições para o backend em `http://localhost:8000`.

### 3. Build do Frontend para Produção
Para gerar a versão de produção do frontend que será servida pelo FastAPI:
```powershell
cd frontend
npm run build
```
Os arquivos estáticos serão gerados em `frontend/dist/`. O backend FastAPI já está configurado para servir esses arquivos quando não estiver em modo de desenvolvimento Vite.

---

## Funcionalidades Principais

- **Autenticação e Autorização:**
    - Login de usuários com JWT (suportando papéis: `user`, `admin`, `global_admin`).
    - Refresh token para manutenção da sessão.
    - Controle de Acesso Baseado em Papéis (RBAC) para proteger endpoints e funcionalidades.
- **Gerenciamento de Usuários (por Admin Global):**
    - CRUD completo de usuários (criar, listar, detalhar, atualizar, deletar).
    - Migração de senhas legadas para formato hasheado.
    - Definição de requisitos de senha e funcionalidade para alteração de senha pelo próprio usuário.
- **Gerenciamento de Grupos:**
    - **Admin Global:** CRUD de grupos, designação de administradores de grupo.
    - **Admin de Grupo (ou Global):** Adicionar/remover usuários de seus grupos, promover membros a admin do grupo.
- **Gerenciamento de Ferramentas:**
    - **Admin de Grupo (ou Global):** Associar/desassociar ferramentas a grupos.
    - Usuários podem visualizar e acessar as ferramentas para as quais seus grupos concedem permissão.
- **Workflow de Solicitação de Acesso a Grupos (RF06):**
    - Usuários podem solicitar acesso a grupos.
    - Administradores (de grupo ou globais) podem revisar (aprovar/rejeitar) essas solicitações.
- **Portal Frontend:**
    - Interface para login, dashboard, visualização de ferramentas, solicitação de acesso a grupos e administração de solicitações.
    - Navegação e componentes dinâmicos baseados no papel do usuário.
- **API Backend:**
    - Endpoints RESTful para todas as funcionalidades mencionadas.
    - Documentação automática da API via Swagger UI (`/docs`) e ReDoc (`/redoc`).
    - Healthcheck (`/tools/health`).

---

## Exemplo de Estrutura RBAC
Consulte o arquivo `data/rbac.json` para um exemplo da estrutura de dados que define usuários, senhas (hasheadas ou legadas para migração), papéis, grupos, membros de grupos, administradores de grupos e ferramentas associadas a grupos.

---

## Segurança
- Autenticação baseada em JWT.
- Controle de Acesso Baseado em Papéis (RBAC) em todos os endpoints sensíveis.
- Hashing de senhas com bcrypt.
- Validação de força de senha.
- CORS configurado para desenvolvimento.
- Planejamento para headers de segurança adicionais (HSTS, CSP), rate limiting, e trilha de auditoria detalhada (ver `docs/SEGURANCA.md` e `docs/TODO.md`).

---

## Documentação da API

A documentação interativa e detalhada da API está disponível automaticamente através do FastAPI:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

> **Nota:** Um resumo dos endpoints também está disponível em [`docs/API.md`](docs/API.md), mas a documentação gerada automaticamente é a fonte mais precisa e completa. A documentação técnica detalhada do backend, incluindo modelos e fluxos, pode ser encontrada em [`docs/BACKEND_DOCUMENTATION.md`](docs/BACKEND_DOCUMENTATION.md).

---

## Requisitos do Sistema
Consulte o arquivo [`docs/REQUISITOS.md`](docs/REQUISITOS.md) para uma lista detalhada de requisitos funcionais, não-funcionais, de negócio e operacionais, incluindo o status de implementação de muitos deles.

---

## Documentação Completa

A documentação detalhada do projeto está centralizada na pasta [`docs/`](docs/):
- [`docs/REQUISITOS.md`](docs/REQUISITOS.md): Requisitos do sistema
- [`docs/API.md`](docs/API.md): Resumo dos endpoints da API
- [`docs/BACKEND_DOCUMENTATION.md`](docs/BACKEND_DOCUMENTATION.md): Documentação técnica detalhada do Backend
- [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md): Arquitetura técnica do sistema
- [`docs/SEGURANCA.md`](docs/SEGURANCA.md): Práticas e considerações de segurança
- [`docs/GOVERNANCA.md`](docs/GOVERNANCA.md): Governança, papéis e responsabilidades
- [`docs/OPERACIONAL.md`](docs/OPERACIONAL.md): Operação, monitoramento e troubleshooting
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md): Histórico de versões e mudanças
- [`docs/TODO.md`](docs/TODO.md): Lista de melhorias e pendências
- [`frontend/README.md`](frontend/README.md): Documentação específica do Frontend

---

## Boas Práticas e Observações
- Mantenha as dependências atualizadas (`requirements.txt` para o backend, `package.json` para o frontend).
- Utilize ambientes virtuais Python para isolar as dependências do backend.
- Sempre gere o build de produção do frontend (`npm run build`) antes de realizar o deploy da aplicação integrada.
- Consulte a documentação específica de cada módulo/pasta para informações mais detalhadas.
- Utilize o sistema de issues do repositório para rastrear bugs, solicitar features e discutir melhorias.
- Contribuições são bem-vindas! Siga as diretrizes de contribuição (se houver) e utilize Pull Requests para propor mudanças.

---

*Este documento deve ser revisado e atualizado periodicamente para refletir o estado atual e a evolução do projeto.*