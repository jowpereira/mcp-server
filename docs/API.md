# API MCP Gateway

Esta documentação apresenta os principais endpoints e exemplos de uso da API do MCP Gateway. A documentação OpenAPI/Swagger é gerada automaticamente pelo FastAPI em `/docs`.

---

## Sumário
- [Endpoints Principais](#endpoints-principais)
- [Exemplos de Uso](#exemplos-de-uso)
- [Observações e Boas Práticas](#observações-e-boas-práticas)

---

## Endpoints Principais

### Autenticação
- `POST /tools/login` — Login de usuário, retorna JWT

### Grupos
- `GET /tools/grupos` — Lista todos os grupos (admin global)
- `GET /tools/grupos/{grupo}/usuarios` — Lista usuários do grupo (admin do grupo ou global)
- `POST /tools/grupos/{grupo}/ferramentas` — Cria nova ferramenta no grupo (admin do grupo ou global)

### Ferramentas
- `GET /tools/ferramenta_x` — Executa ferramenta X (usuário autorizado)
- `GET /tools/ferramenta_y` — Executa ferramenta Y (usuário autorizado)
- `GET /tools/ferramenta_z` — Executa ferramenta Z (usuário autorizado)

### Infraestrutura
- `GET /tools/health` — Healthcheck

---

## Exemplos de Uso
Veja exemplos de payloads e respostas diretamente no Swagger (`/docs`).

---

## Observações e Boas Práticas
- Para detalhes completos, consulte a documentação automática do FastAPI em `/docs` (Swagger) ou `/redoc` (Redoc).
- Mantenha os endpoints documentados e atualizados conforme a evolução da API.
- Utilize JWT para autenticação em todas as requisições protegidas.
- Sugestão: utilize issues e pull requests para propor alterações nesta documentação.

---

*Este documento deve ser revisado e atualizado periodicamente conforme a API evoluir.*
