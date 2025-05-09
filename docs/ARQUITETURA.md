# Arquitetura do Sistema – MCP Gateway

Este documento apresenta a visão técnica e os principais componentes da arquitetura do MCP Gateway.

---

## Sumário
- [Visão Geral](#visão-geral)
- [Diagrama de Componentes](#diagrama-de-componentes)
- [Fluxos Principais](#fluxos-principais)
- [Decisões Técnicas](#decisões-técnicas)
- [Pontos de Extensão](#pontos-de-extensão)
- [Observações e Boas Práticas](#observações-e-boas-práticas)

---

## Visão Geral
O MCP Gateway é composto por dois grandes módulos:
- **Backend:** FastAPI (Python), responsável por autenticação, RBAC, APIs RESTful, lógica de negócio e servir o frontend estático.
- **Frontend:** React + Vite (TypeScript), portal de autoatendimento para gestão e uso das ferramentas MCP.

---

## Diagrama de Componentes (alto nível)
```text
[Usuário] <-> [Frontend React] <-> [Backend FastAPI] <-> [Dados JSON/Banco]
```

---

## Fluxos Principais
- **Login:** Usuário faz login no frontend, que envia credenciais para o backend. Backend retorna JWT.
- **Gestão:** Admin global/por grupo gerencia grupos, usuários e ferramentas via portal, que consome APIs REST do backend.
- **Execução:** Usuário acessa ferramentas permitidas, executando-as via portal (requisições autenticadas).
- **Build:** Frontend é buildado em `/frontend/dist` e servido pelo backend como estático.

---

## Decisões Técnicas
- **RBAC:** Controle de acesso por papel (global_admin, admin, user) e grupo.
- **JWT:** Autenticação stateless e segura.
- **Persistência:** Inicialmente em JSON, pronta para migração para banco relacional/NoSQL.
- **Modularidade:** Separação clara de responsabilidades, fácil manutenção e escalabilidade.

---

## Pontos de Extensão
- Integração futura com SSO (Azure AD, etc)
- Migração para banco de dados
- CI/CD e deploy cloud

---

## Observações e Boas Práticas
- Atualize este documento sempre que houver mudanças na arquitetura.
- Inclua diagramas detalhados conforme o sistema evoluir.
- Sugestão: utilize issues e pull requests para propor alterações e manter o histórico de decisões.

---

*Este documento deve ser revisado e atualizado periodicamente conforme a arquitetura evoluir.*
