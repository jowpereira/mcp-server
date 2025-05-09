# Operacional / Runbook – MCP Gateway

Este documento apresenta as rotinas operacionais, monitoramento, backup, atualização e troubleshooting do MCP Gateway.

---

## Sumário
- [Como Rodar Localmente](#como-rodar-localmente)
- [Monitoramento](#monitoramento)
- [Backup e Restauração](#backup-e-restauração)
- [Atualização e Deploy](#atualização-e-deploy)
- [Troubleshooting](#troubleshooting)
- [Observações e Boas Práticas](#observações-e-boas-práticas)

---

## Como Rodar Localmente
1. Instale dependências do backend (Python) e frontend (Node.js)
2. Rode `npm run build` no frontend
3. Rode o backend FastAPI (`uvicorn app.main:app --reload`)
4. Acesse http://localhost:8000

---

## Monitoramento
- Verifique logs do backend para erros e auditoria
- Healthcheck disponível em `/tools/health`

---

## Backup e Restauração
- Faça backup regular dos arquivos JSON em `data/`
- Para restaurar, substitua os arquivos e reinicie o backend

---

## Atualização e Deploy
- Atualize dependências com `pip install -r requirements.txt` e `npm install`
- Gere novo build do frontend antes de deploy
- Deploy recomendado em ambiente cloud (Azure, AWS, etc)

---

## Troubleshooting
- Verifique logs para erros de autenticação, permissão ou integração
- Use logs para rastrear ações administrativas

---

## Observações e Boas Práticas
- Atualize este documento conforme o sistema evoluir.
- Documente procedimentos específicos do seu ambiente de produção.
- Sugestão: utilize issues e pull requests para propor alterações e manter o histórico de decisões.

---

*Este documento deve ser revisado e atualizado periodicamente conforme o sistema evoluir.*
