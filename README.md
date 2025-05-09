# MCP Gateway – API & Portal de Autoatendimento

Este repositório contém o MCP Gateway, uma solução corporativa para expor, gerenciar e consumir ferramentas (APIs internas) de forma segura, escalável e auditável, com autenticação RBAC e portal de autoatendimento.

---

## Sumário
- [Visão Geral](#visão-geral)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Como Rodar (Desenvolvimento)](#como-rodar-desenvolvimento)
- [Funcionalidades](#funcionalidades)
- [Exemplo de Estrutura RBAC](#exemplo-de-estrutura-rbac)
- [Segurança](#segurança)
- [Documentação da API](#documentação-da-api)
- [Requisitos do Sistema](#requisitos-do-sistema)
- [Documentação Completa](#documentação-completa)
- [Boas Práticas e Observações](#boas-práticas-e-observações)

---

## Visão Geral
O MCP Gateway é composto por:
- **Backend:** FastAPI + RBAC + JWT + persistência em JSON (pronto para NoSQL)
- **Frontend:** React (Vite) rodando integrado ao backend (build em `/frontend/dist` servido como estático)

---

## Estrutura de Pastas
```text
mcp-server/
├── app/                # Backend FastAPI
│   ├── main.py         # Entrypoint
│   ├── config.py       # Configurações
│   ├── auth.py         # Autenticação/JWT
│   ├── utils/          # Utilitários (RBAC, dependências)
│   └── groups/
│       ├── routes.py   # Rotas (APIs)
│       └── tools.py    # Utilitários de permissão
├── data/               # Dados persistentes
│   └── rbac.json       # Usuários, grupos, permissões
├── frontend/           # Portal React (Vite)
│   ├── src/            # Código-fonte React
│   └── dist/           # Build de produção (servido pelo FastAPI)
├── requirements.txt    # Dependências Python
├── README.md           # Este documento
└── ...
```

---

## Como Rodar (Desenvolvimento)

### 1. Backend (FastAPI)
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. Frontend (React)
```powershell
cd frontend
npm install
npm run dev
```
Acesse: http://localhost:5173 (dev) ou http://localhost:8000 (prod)

### 3. Build do Frontend para Produção
```powershell
cd frontend
npm run build
```
Os arquivos serão gerados em `frontend/dist`. O FastAPI pode servir esses arquivos automaticamente.

---

## Funcionalidades
- Login JWT (usuário, admin de grupo, admin global)
- Gestão de grupos, usuários e ferramentas (CRUD)
- Criação dinâmica de ferramentas por admin de grupo
- Consumo seguro de ferramentas via portal
- Healthcheck, logging, documentação automática (Swagger)
- Pronto para integração com banco NoSQL e SSO

---

## Exemplo de Estrutura RBAC
Veja `data/rbac.json` para exemplo de usuários, grupos e permissões.

---

## Segurança
- JWT, RBAC, logging de ações
- Pronto para CORS, HTTPS, rate limit, etc.

---

## Documentação da API
Acesse `/docs` para Swagger ou `/redoc` para Redoc.

---

## Requisitos do Sistema
Veja o arquivo [`docs/REQUISITOS.md`](docs/REQUISITOS.md) para requisitos funcionais, não-funcionais e de negócio detalhados.

---

## Documentação Completa
A documentação detalhada do projeto está centralizada na pasta [`docs/`](docs/):
- [`docs/REQUISITOS.md`](docs/REQUISITOS.md): Requisitos do sistema
- [`docs/API.md`](docs/API.md): Endpoints e exemplos de uso da API
- [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md): Arquitetura técnica
- [`docs/SEGURANCA.md`](docs/SEGURANCA.md): Segurança e práticas recomendadas
- [`docs/GOVERNANCA.md`](docs/GOVERNANCA.md): Governança e papéis
- [`docs/OPERACIONAL.md`](docs/OPERACIONAL.md): Operação, monitoramento e troubleshooting
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md): Histórico de versões

---

## Boas Práticas e Observações
- Mantenha as dependências atualizadas.
- Utilize ambientes virtuais para Python.
- Sempre gere o build do frontend antes de deploy em produção.
- Consulte a documentação dos demais módulos em [`docs/`](docs/).
- Sugestão: utilize issues e pull requests para propor alterações e manter o histórico de decisões.

---

*Este documento deve ser revisado e atualizado periodicamente para refletir mudanças no projeto.*