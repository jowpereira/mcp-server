# SEGURANÇA DO SISTEMA MCP GATEWAY

## Autenticação
- JWT assinado com chave secreta (SECRET_KEY)
- Expiração de token configurável
- Login obrigatório para todas as operações sensíveis

## Autorização
- RBAC: Papéis (global_admin, admin, user) e grupos
- Permissões validadas a cada requisição
- Admin global tem acesso total; admin de grupo só ao seu grupo

## Proteção de Dados
- Dados sensíveis nunca trafegam em texto puro
- Pronto para integração com SSO (Azure AD, OAuth2)
- Estrutura pronta para criptografia de dados em repouso

## Logs e Auditoria
- Todas as ações administrativas são logadas
- Logs incluem usuário, IP, ação, data/hora
- Logs de acesso e falha de autenticação

## Proteção contra Ataques
- CORS configurado para ambientes de produção
- Proteção contra CSRF (futuro)
- Rate limiting recomendado para endpoints sensíveis
- Validação de payloads e tratamento de erros

## Governança
- Revisão periódica de permissões e papéis
- Rotina de rotação de segredos
- Política de onboarding/offboarding de usuários

---

Este documento deve ser atualizado conforme as práticas de segurança evoluírem.
