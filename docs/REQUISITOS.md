# Requisitos do Sistema – MCP Gateway

Este documento apresenta os requisitos essenciais para o desenvolvimento, operação e evolução do MCP Gateway. Ele serve como referência central para desenvolvedores, administradores, gestores e demais stakeholders.

---

## Sumário
- [1. Requisitos Funcionais](#1-requisitos-funcionais)
- [2. Requisitos Não-Funcionais](#2-requisitos-não-funcionais)
- [3. Requisitos de Negócio](#3-requisitos-de-negócio)
- [4. Requisitos Operacionais](#4-requisitos-operacionais)
- [Legenda](#legenda)
- [Observações e Boas Práticas](#observações-e-boas-práticas)

---

## 1. Requisitos Funcionais
Definem as funcionalidades obrigatórias para atender as necessidades dos usuários e administradores. Cada requisito funcional deve ser validado por meio de testes e revisões de usabilidade.
*(Status atualizado em 2025-05-10 com base na documentação e TODOs existentes. Para detalhes da implementação, consulte `docs/BACKEND_DOCUMENTATION.md` e `docs/CHANGELOG.md`.)*

- **RF01:** Permitir login de usuários, administradores de grupo e administrador global via portal web e API.
    - *Status: Concluído (Backend API e Frontend básico implementados).*
- **RF02:** Permitir ao administrador global criar, editar e remover grupos, além de designar administradores de grupo.
    - *Status: Concluído (Endpoints backend implementados: `POST /tools/grupos`, `PUT /tools/grupos/{grupo}`, `DELETE /tools/grupos/{grupo}`, `POST /tools/grupos/{grupo}/admins`).*
- **RF03:** Permitir ao administrador de grupo adicionar/remover usuários do grupo e promover usuários a administradores do grupo.
    - *Status: Concluído (Endpoints backend implementados: `POST /tools/grupos/{grupo}/usuarios`, `DELETE /tools/grupos/{grupo}/usuarios/{username}`, `POST /tools/grupos/{grupo}/promover-admin`).*
- **RF04:** Permitir ao administrador de grupo criar, editar e remover ferramentas do grupo.
    - *Status: Parcialmente Concluído (Backend permite adicionar/remover ferramentas a grupos: `POST /tools/grupos/{grupo}/ferramentas`, `DELETE /tools/grupos/{grupo}/ferramentas/{tool_id}`. A "criação/edição" de ferramentas no contexto do grupo refere-se principalmente à associação de nomes/IDs de ferramentas, não à definição completa da ferramenta em si dentro do grupo).*
- **RF05:** Permitir ao usuário comum consumir ferramentas às quais tem acesso.
    - *Status: Concluído (Endpoints backend implementados: `GET /user_tools` e exemplos como `GET /tools/ferramenta_x`).*
- **RF06:** Permitir ao usuário solicitar acesso a grupos (workflow de aprovação).
    - *Status: Concluído (Endpoints backend em `app/groups/requests_routes.py` e Frontend básico implementados).*
- **RF07:** Permitir ao administrador global auditar todas as ações do sistema, com trilha de auditoria detalhada.
    - *Status: Pendente (Item em `docs/TODO.md`).*
- **RF08:** Expor documentação automática e interativa da API (Swagger/Redoc), sempre atualizada.
    - *Status: Concluído (Fornecido pelo FastAPI em `/docs` e `/redoc`).*
- **RF09:** Permitir integração futura com banco NoSQL e SSO corporativo, com arquitetura preparada para expansão.
    - *Status: Pendente (Migração para BD e implementação de SSO são itens futuros em `docs/TODO.md`).*

---

## 2. Requisitos Não-Funcionais
Garantem qualidade, segurança, escalabilidade e usabilidade do sistema. Devem ser considerados em todas as fases do ciclo de vida do software.

- **RNF01:** O sistema deve ser seguro, utilizando autenticação JWT e RBAC (controle de acesso baseado em papéis), com proteção contra ataques comuns (XSS, CSRF, etc).
    - *Status: Parcialmente Concluído (Autenticação JWT e RBAC implementados. Headers de segurança adicionais e revisão de CSRF estão em `docs/TODO.md`).*
- **RNF02:** O sistema deve ser escalável e modular, pronto para ambientes de produção e fácil de manter.
    - *Status: Em Andamento (Estrutura modular existe, escalabilidade depende da migração de persistência e otimizações futuras).*
- **RNF03:** O frontend deve ser responsivo, acessível (WCAG 2.1), e funcionar integrado ao backend.
    - *Status: Em Andamento (Frontend básico integrado. Responsividade e acessibilidade WCAG 2.1 requerem avaliação e melhorias contínuas).*
- **RNF04:** O backend deve registrar logs detalhados de todas as ações administrativas e de acesso, com níveis configuráveis.
    - *Status: Pendente (Melhoria do sistema de logging é um item em `docs/TODO.md`).*
- **RNF05:** O sistema deve ser facilmente auditável e extensível, com código limpo e documentação técnica.
    - *Status: Em Andamento (Documentação técnica existe e está sendo revisada. Extensibilidade e auditoria completa dependem de RF07 e RNF04).*
- **RNF06:** O sistema deve permitir deploy em ambiente cloud (nuvem) ou on-premises (local), com scripts e automação.
    - *Status: Pendente (Preparação para containerização e deployment são itens em `docs/TODO.md`).*
- **RNF07:** O frontend deve suportar internacionalização (i18n) e ser preparado para múltiplos idiomas.
    - *Status: Pendente (Item em `docs/TODO.md`).*

---

## 3. Requisitos de Negócio
Asseguram que o sistema atenda às necessidades estratégicas e operacionais da organização, promovendo autonomia e governança.

- **RN01:** Garantir segregação de acesso entre grupos/projetos, com políticas claras de permissão.
- **RN02:** Permitir autoatendimento para criação de ferramentas e gestão de usuários, reduzindo dependência de TI.
- **RN03:** Permitir que cada grupo/projeto tenha autonomia sobre suas ferramentas e usuários, com limites configuráveis.
- **RN04:** Permitir que o administrador global tenha visão e controle total do ambiente, com dashboards e relatórios.
- **RN05:** Permitir integração com sistemas legados e APIs internas, com conectores e documentação de integração.

---

## 4. Requisitos Operacionais
Asseguram a operação, manutenção e evolução do sistema, facilitando o suporte e a continuidade do serviço.

- **RO01:** O sistema deve ser facilmente monitorável (healthcheck, logs, métricas), com alertas configuráveis.
- **RO02:** O sistema deve permitir backup e restauração dos dados de configuração, com procedimentos documentados.
- **RO03:** O sistema deve ser documentado e possuir onboarding rápido para novos usuários e administradores, com tutoriais e FAQs.

---

## Legenda
- **JWT:** JSON Web Token
- **RBAC:** Role-Based Access Control (Controle de Acesso Baseado em Papéis)
- **SSO:** Single Sign-On (Autenticação Única)
- **i18n:** Internacionalização
- **WCAG:** Web Content Accessibility Guidelines
- **API:** Application Programming Interface

---

## Observações e Boas Práticas
- Para detalhes de endpoints, payloads e exemplos de uso, consulte o arquivo [`API.md`](API.md) e a documentação Swagger gerada pelo backend.
- Este documento deve ser revisado e atualizado periodicamente para refletir mudanças nas necessidades do negócio ou na arquitetura do sistema.
- Utilize issues e pull requests para propor alterações e manter o histórico de decisões.
- Recomenda-se a revisão colaborativa deste documento por todas as áreas envolvidas (negócio, desenvolvimento, operações e segurança).
- Mantenha a documentação sempre alinhada com o código-fonte e as práticas de DevOps adotadas pelo time.
