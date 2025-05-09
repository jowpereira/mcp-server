# ARQUITETURA DO SISTEMA MCP GATEWAY

## Visão Geral
O MCP Gateway é composto por dois grandes módulos:
- **Backend:** FastAPI (Python), responsável por autenticação, RBAC, APIs RESTful, lógica de negócio e servir o frontend estático.
- **Frontend:** React + Vite (TypeScript), portal de autoatendimento para gestão e uso das ferramentas MCP.

## Diagrama de Componentes (alto nível)
```
[Usuário] <-> [Frontend React] <-> [Backend FastAPI] <-> [Dados JSON/Banco]
```

## Fluxos Principais
- **Login:** Usuário faz login no frontend, que envia credenciais para o backend. Backend retorna JWT.
- **Gestão:** Admin global/por grupo gerencia grupos, usuários e ferramentas via portal, que consome APIs REST do backend.
- **Execução:** Usuário acessa ferramentas permitidas, executando-as via portal (requisições autenticadas).
- **Build:** Frontend é buildado em `/frontend/dist` e servido pelo backend como estático.

## Decisões Técnicas
- **RBAC:** Controle de acesso por papel (global_admin, admin, user) e grupo.
- **JWT:** Autenticação stateless e segura.
- **Persistência:** Inicialmente em JSON, pronta para migração para banco relacional/NoSQL.
- **Modularidade:** Separação clara de responsabilidades, fácil manutenção e escalabilidade.

## Pontos de Extensão
- Integração futura com SSO (Azure AD, etc)
- Migração para banco de dados
- CI/CD e deploy cloud

---

Este documento deve ser atualizado conforme a arquitetura evoluir.
