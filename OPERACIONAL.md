# OPERACIONAL / RUNBOOK MCP GATEWAY

## Como Rodar Localmente
1. Instale dependências do backend (Python) e frontend (Node.js)
2. Rode `npm run build` no frontend
3. Rode o backend FastAPI (`uvicorn app.main:app --reload`)
4. Acesse http://localhost:8000

## Monitoramento
- Verifique logs do backend para erros e auditoria
- Healthcheck disponível em `/tools/health`

## Backup e Restauração
- Faça backup regular dos arquivos JSON em `data/`
- Para restaurar, substitua os arquivos e reinicie o backend

## Atualização e Deploy
- Atualize dependências com `pip install -r requirements.txt` e `npm install`
- Gere novo build do frontend antes de deploy
- Deploy recomendado em ambiente cloud (Azure, AWS, etc)

## Troubleshooting
- Verifique logs para erros de autenticação, permissão ou integração
- Use logs para rastrear ações administrativas

---

Este documento deve ser atualizado conforme o sistema evoluir.
