# MCP Gateway Portal (Frontend)

Este projeto é um portal de autoatendimento para o MCP Gateway, desenvolvido em React + Vite + TypeScript.

## Funcionalidades
- Login com JWT
- Dashboard dinâmico por papel (admin global, admin de grupo, usuário)
- Gestão de grupos, usuários e ferramentas
- Criação de ferramentas por admin de grupo
- Consumo de ferramentas via interface amigável
- Healthcheck e integração RESTful com backend FastAPI

## Build e Deploy
- Para desenvolvimento: `npm run dev`
- Para build de produção: `npm run build` (os arquivos estáticos ficam em `/dist`)
- O backend FastAPI pode servir os arquivos estáticos de `/dist` para rodar tudo junto sem container extra

## Estrutura Recomendada
- O frontend fica em `frontend` e o backend em `mcp-server/`
- Comunicação via REST (CORS liberado no backend para dev)

## Como rodar
```sh
npm install
npm run dev
```

## Como buildar para produção
```sh
npm run build
```

Depois, configure o backend para servir os arquivos de `/dist` como estático.

---

Siga as instruções do backend para integração completa.
