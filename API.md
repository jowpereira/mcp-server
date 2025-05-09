# API MCP GATEWAY

A documentação OpenAPI/Swagger é gerada automaticamente pelo FastAPI em `/docs`.

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

### Infra
- `GET /tools/health` — Healthcheck

## Exemplos de Uso
Veja exemplos de payloads e respostas no Swagger (`/docs`).

---

Para detalhes completos, consulte a documentação automática do FastAPI.
