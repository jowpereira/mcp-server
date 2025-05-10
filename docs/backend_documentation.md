# Documentação Técnica do Backend (MCP Gateway)

Esta documentação visa fornecer um entendimento detalhado da API backend para facilitar o desenvolvimento de testes automatizados e a manutenção do sistema.

**1. Visão Geral**

O backend do MCP Gateway é uma API RESTful construída com FastAPI (Python). Ele gerencia usuários, grupos, ferramentas e o acesso a essas ferramentas através de um sistema de controle de acesso baseado em papéis (RBAC). Os dados são persistidos em arquivos JSON (`data/rbac.json` e `data/requests.json`).

**2. Configuração**

*   **Arquivo Principal:** `app/main.py`
*   **Variáveis de Ambiente (via `.env`):**
    *   `RBAC_FILE`: Caminho para o arquivo de dados RBAC (padrão: `data/rbac.json`).
*   **Constantes de Configuração (`app/config.py`):**
    *   `settings.SECRET_KEY`: Chave secreta para assinatura de JWTs (atualmente 'changeme', **deve ser alterada para produção**).
    *   `settings.RBAC_FILE`: Caminho para o arquivo RBAC, derivado da variável de ambiente ou padrão.

**3. Autenticação e Autorização**

*   **Módulo:** `app/auth.py`
*   **Fluxo de Autenticação:**
    1.  Cliente envia `username` e `password` para `POST /tools/login`.
    2.  `authenticate_user` verifica as credenciais.
        *   Suporta senhas em texto plano (legado) e hashes bcrypt.
    3.  Se válido, `create_jwt_for_user` gera um JWT.
    4.  JWT é retornado ao cliente.
*   **Token JWT:**
    *   **Payload:** `sub` (username), `grupos` (lista de nomes de grupos), `papel` (`user`, `admin`, `global_admin`), `exp` (timestamp de expiração).
    *   **Algoritmo:** HS256.
    *   **Validação:** `get_current_user` (dependência FastAPI) valida o token em rotas protegidas.
*   **Papéis:**
    *   `user`: Acesso básico, pode solicitar entrada em grupos e usar ferramentas de seus grupos.
    *   `admin`: Permissões de `user`, mais gerenciar usuários e ferramentas dentro dos grupos que administra. Pode aprovar/rejeitar solicitações para seus grupos.
    *   `global_admin`: Controle total sobre todos os usuários, grupos e ferramentas.

**4. Estrutura de Dados (Persistência)**

*   **`data/rbac.json`:**
    *   `grupos`: Dicionário. Chave é o nome do grupo.
        *   `descricao`: String (opcional).
        *   `admins`: Lista de usernames dos administradores do grupo.
        *   `users`: Lista de usernames dos membros do grupo.
        *   `ferramentas`: Lista de IDs de ferramentas disponíveis para o grupo.
    *   `usuarios`: Dicionário. Chave é o username.
        *   `senha`: String (hash bcrypt ou texto plano legado).
        *   `grupos`: Lista de nomes de grupos aos quais o usuário pertence.
        *   `papel`: String (`user`, `admin`, `global_admin`).
    *   `ferramentas`: Dicionário (opcional, para definições globais de ferramentas). Chave é o ID da ferramenta.
        *   `nome`: String (nome amigável).
        *   `url_base`: String (URL da ferramenta).
        *   `descricao`: String (opcional).
*   **`data/requests.json`:**
    *   `requests`: Lista de objetos de solicitação de acesso.
        *   `request_id`: UUID.
        *   `username`: Username do solicitante.
        *   `grupo`: Nome do grupo solicitado.
        *   `status`: `pending`, `approved`, `rejected`.
        *   `justificativa`: String.
        *   `created_at`: ISO datetime.
        *   `updated_at`: ISO datetime (opcional).
        *   `reviewed_by`: Username do admin que revisou (opcional).
        *   `review_comment`: Comentário da revisão (opcional).

**5. Endpoints da API**

Os endpoints são divididos em dois roteadores principais montados sob o prefixo `/tools`.

**5.1. Roteador Principal (`app/groups/routes.py`)**

*   **Tag: Auth**
    *   `POST /login`
        *   **Descrição:** Autentica um usuário.
        *   **Request Body:** `{"username": "str", "password": "str"}`
        *   **Response (200):** `{"access_token": "jwt_string", "token_type": "bearer"}`
        *   **Response (400):** "Usuário e senha obrigatórios."
        *   **Response (401):** "Usuário ou senha inválidos"
        *   **Response (500):** Erro interno.
    *   `POST /refresh-token`
        *   **Descrição:** Renova um token JWT para o usuário autenticado.
        *   **Auth:** Requer token JWT válido.
        *   **Response (200):** `{"access_token": "new_jwt_string", "token_type": "bearer"}`
        *   **Response (500):** Erro interno.

*   **Tag: Infra**
    *   `GET /health`
        *   **Descrição:** Verifica a saúde da aplicação.
        *   **Response (200):** `{"status": "ok"}`

*   **Tag: Admin (Gerenciamento de Grupos)**
    *   `GET /grupos`
        *   **Descrição:** Lista todos os grupos com detalhes.
        *   **Auth:** `global_admin`.
        *   **Response (200):** `List[GroupDetailSchema]` (ver modelos Pydantic abaixo).
        *   **Response (403):** "Acesso restrito ao admin global."
    *   `POST /grupos`
        *   **Descrição:** Cria um novo grupo.
        *   **Auth:** `global_admin`.
        *   **Request Body:** `CreateGroupRequest` (`{"nome": "str", "descricao": "Optional[str]"}`)
        *   **Response (200):** `{"message": "Grupo '<nome>' criado com sucesso."}`
        *   **Response (400):** "Nome do grupo é obrigatório."
        *   **Response (403):** "Acesso restrito ao admin global."
        *   **Response (409):** "Grupo já existe."
    *   `PUT /grupos/{grupo}`
        *   **Descrição:** Edita nome e/ou descrição de um grupo.
        *   **Auth:** `global_admin`.
        *   **Path Param:** `grupo` (nome do grupo a editar).
        *   **Request Body:** `EditGroupRequest` (`{"nome": "Optional[str]", "descricao": "Optional[str]"}`)
        *   **Response (200):** `{"message": "Grupo '<novo_nome_ou_nome_antigo>' editado com sucesso."}` ou "Nenhuma alteração fornecida."
        *   **Response (403):** "Acesso restrito ao admin global."
        *   **Response (404):** "Grupo não encontrado."
        *   **Response (409):** "Já existe um grupo com o nome '<novo_nome>'."
    *   `DELETE /grupos/{grupo}`
        *   **Descrição:** Remove um grupo.
        *   **Auth:** `global_admin`.
        *   **Path Param:** `grupo` (nome do grupo a remover).
        *   **Response (200):** `{"message": "Grupo '<nome>' removido com sucesso."}`
        *   **Response (403):** "Acesso restrito ao admin global."
        *   **Response (404):** "Grupo não encontrado."
    *   `POST /grupos/{grupo}/admins`
        *   **Descrição:** Designa um usuário como administrador de um grupo.
        *   **Auth:** `global_admin`.
        *   **Path Param:** `grupo`.
        *   **Request Body:** `{"username": "str"}`
        *   **Response (200):** `{"message": "Usuário '<username>' agora é admin do grupo '<grupo>'"}`
        *   **Response (400):** "Usuário inválido." ou "Usuário '<username>' não é membro do grupo '<grupo>'. Adicione como membro primeiro."
        *   **Response (403):** "Acesso restrito ao admin global."
        *   **Response (404):** "Grupo não encontrado."
    *   `DELETE /grupos/{grupo}/admins/{username_param}`
        *   **Descrição:** Remove um administrador de um grupo.
        *   **Auth:** `global_admin` ou `admin` do grupo.
        *   **Path Params:** `grupo`, `username_param` (admin a ser removido).
        *   **Response (200):** `{"message": "Usuário '<username_param>' não é mais admin do grupo '<grupo>'."}`
        *   **Response (400):** "Não é possível remover o último administrador do grupo." (se não for `global_admin`).
        *   **Response (403):** "Acesso restrito ao admin global ou admin do grupo."
        *   **Response (404):** "Grupo '<grupo>' não encontrado.", "Usuário admin '<username_param>' não encontrado.", "Usuário '<username_param>' não é admin do grupo '<grupo>'."
    *   `POST /grupos/{grupo}/usuarios`
        *   **Descrição:** Adiciona um usuário a um grupo.
        *   **Auth:** `global_admin` ou `admin` do grupo.
        *   **Path Param:** `grupo`.
        *   **Request Body:** `{"username": "str"}`
        *   **Response (200):** `{"message": "Usuário '<username>' adicionado ao grupo '<grupo>'"}`
        *   **Response (400):** "Usuário inválido."
        *   **Response (403):** "Acesso restrito ao admin do grupo ou global."
        *   **Response (404):** "Grupo não encontrado."
    *   `DELETE /grupos/{grupo}/usuarios/{username}`
        *   **Descrição:** Remove um usuário de um grupo.
        *   **Auth:** `global_admin` ou `admin` do grupo.
        *   **Path Params:** `grupo`, `username` (usuário a ser removido).
        *   **Response (200):** `{"message": "Usuário '<username>' removido do grupo '<grupo>'"}`
        *   **Response (403):** "Acesso restrito ao admin do grupo ou global."
        *   **Response (404):** "Grupo não encontrado." ou "Usuário não está no grupo."
    *   `POST /grupos/{grupo}/promover-admin`
        *   **Descrição:** Promove um membro do grupo a administrador do grupo.
        *   **Auth:** `global_admin` ou `admin` do grupo.
        *   **Path Param:** `grupo`.
        *   **Request Body:** `{"username": "str"}`
        *   **Response (200):** `{"message": "Usuário '<username>' agora é admin do grupo '<grupo>'"}`
        *   **Response (400):** "Usuário inválido."
        *   **Response (403):** "Acesso restrito ao admin do grupo ou global."
        *   **Response (404):** "Grupo não encontrado."
    *   `GET /grupos/{grupo}/usuarios`
        *   **Descrição:** Lista administradores e usuários de um grupo.
        *   **Auth:** `global_admin` ou `admin` do grupo (ou membro do grupo para ver a lista).
        *   **Path Param:** `grupo`.
        *   **Response (200):** `{"admins": List[str], "users": List[str]}`
        *   **Response (403):** "Acesso restrito..." (se não for membro nem admin).
        *   **Response (404):** "Grupo não encontrado."
    *   `POST /grupos/{grupo}/ferramentas`
        *   **Descrição:** Adiciona uma ferramenta existente (global) a um grupo.
        *   **Auth:** `global_admin` ou `admin` do grupo.
        *   **Path Param:** `grupo`.
        *   **Request Body:** `{"tool_id": "str"}` (ID da ferramenta global).
        *   **Response (200):** `{"message": "Ferramenta '<tool_id>' adicionada com sucesso ao grupo '<grupo>'"}`
        *   **Response (400):** "ID da ferramenta (tool_id) é obrigatório."
        *   **Response (403):** "Acesso restrito ao admin do grupo ou global."
        *   **Response (404):** "Grupo não encontrado." ou "Ferramenta com ID '<tool_id>' não encontrada nas definições globais."
        *   **Response (409):** "Ferramenta '<tool_id>' já existe no grupo '<grupo>'."
    *   `DELETE /grupos/{grupo}/ferramentas/{tool_id}`
        *   **Descrição:** Remove uma ferramenta de um grupo.
        *   **Auth:** `global_admin` ou `admin` do grupo.
        *   **Path Params:** `grupo`, `tool_id`.
        *   **Response (200):** `{"message": "Ferramenta '<tool_id>' removida com sucesso do grupo '<grupo>'"}`
        *   **Response (403):** "Acesso restrito ao admin do grupo ou global."
        *   **Response (404):** "Grupo '<grupo>' não encontrado." ou "Ferramenta '<tool_id>' não encontrada no grupo '<grupo>'."

*   **Tag: Ferramentas (Gerenciamento Global e Acesso)**
    *   `GET /ferramentas`
        *   **Descrição:** Lista todas as ferramentas definidas globalmente no sistema.
        *   **Auth:** Requer token JWT válido (qualquer usuário autenticado).
        *   **Response (200):** `List[ToolResponseSchema]`
    *   `GET /ferramenta_x`, `GET /ferramenta_y`, `GET /ferramenta_z` (e seus `OPTIONS`)
        *   **Descrição:** Endpoints de exemplo para acessar ferramentas.
        *   **Auth:** Requer token JWT válido. Acesso permitido se o usuário for `global_admin` ou pertencer a um grupo que tenha a ferramenta.
        *   **Response (200):** `{"result": "Execução da ferramenta <nome> por <username>"}`
        *   **Response (403):** "Acesso negado"
    *   `GET /user_tools`
        *   **Descrição:** Lista todas as ferramentas que o usuário logado pode acessar, com base nos seus grupos.
        *   **Auth:** Requer token JWT válido.
        *   **Response (200):** `List[ToolResponseSchema]`
        *   **Response (403):** "Usuário não identificado."

*   **Tag: Admin (Gerenciamento de Usuários Globais)**
    *   `POST /usuarios`
        *   **Descrição:** Cria um novo usuário.
        *   **Auth:** `global_admin`.
        *   **Request Body:** `{"username": "str", "password": "str", "papel": "Optional[str]", "grupos": "Optional[List[str]]"}`
        *   **Response (200):** `{"message": "Usuário '<username>' criado com sucesso."}`
        *   **Response (400):** "Username e password são obrigatórios.", "Papel inválido...", "Grupo '<grupo>' não existe.", "A senha não atende aos requisitos..."
        *   **Response (403):** "Acesso restrito ao admin global."
        *   **Response (409):** "Usuário já existe."
    *   `GET /usuarios`
        *   **Descrição:** Lista todos os usuários.
        *   **Auth:** `global_admin`.
        *   **Response (200):** `List[UserDetailResponse]`
        *   **Response (403):** "Acesso restrito ao admin global."
    *   `GET /usuarios/{username_param}`
        *   **Descrição:** Obtém detalhes de um usuário específico.
        *   **Auth:** `global_admin` ou o próprio usuário solicitando seus dados.
        *   **Path Param:** `username_param`.
        *   **Response (200):** `UserDetailResponse`
        *   **Response (403):** "Acesso restrito." (Se não for global_admin nem o próprio usuário)
        *   **Response (404):** "Usuário '<username_param>' não encontrado."
    *   `PUT /usuarios/{username_param}`
        *   **Descrição:** Atualiza o papel e/ou grupos de um usuário.
        *   **Auth:** `global_admin`.
        *   **Path Param:** `username_param`.
        *   **Request Body:** `UserUpdateRequest` (`{"papel": "Optional[str]", "grupos": "Optional[List[str]]"}`)
        *   **Response (200):** `UserDetailResponse` (com os dados atualizados).
        *   **Response (400):** "Papel inválido...", "Grupo '<grupo_nome>' não encontrado.", "Não é possível remover o último administrador global."
        *   **Response (403):** "Acesso restrito ao admin global."
        *   **Response (404):** "Usuário '<username_param>' não encontrado."
    *   `DELETE /usuarios/{username_param}`
        *   **Descrição:** Deleta um usuário.
        *   **Auth:** `global_admin`.
        *   **Path Param:** `username_param`.
        *   **Response (200):** `{"message": "Usuário '<username_param>' deletado com sucesso."}`
        *   **Response (400):** "Não é possível deletar a si mesmo."
        *   **Response (403):** "Acesso restrito ao admin global."
        *   **Response (404):** "Usuário '<username_param>' não encontrado."
    *   `POST /admin/migrate-passwords`
        *   **Descrição:** Migra senhas em texto plano para hashes bcrypt no `rbac.json`.
        *   **Auth:** `global_admin`.
        *   **Response (200):** `{"message": "Migração de senhas concluída com sucesso."}`
        *   **Response (403):** "Acesso restrito ao admin global."
        *   **Response (500):** "Erro ao migrar senhas."

*   **Tag: User (Funcionalidades do Usuário)**
    *   `POST /usuarios/alterar-senha`
        *   **Descrição:** Permite ao usuário logado alterar sua própria senha.
        *   **Auth:** Requer token JWT válido.
        *   **Request Body:** `{"senha_atual": "str", "nova_senha": "str"}`
        *   **Response (200):** `{"message": "Senha alterada com sucesso"}`
        *   **Response (400):** "Senha atual e nova senha são obrigatórias", "A nova senha não pode ser igual à senha atual", "A senha não atende aos requisitos..."
        *   **Response (401):** "Senha atual incorreta"
    *   `GET /usuarios/requisitos-senha`
        *   **Descrição:** Retorna os requisitos de segurança para senhas.
        *   **Auth:** Nenhuma (público, mas geralmente acessado por usuários logados ou na tela de criação/alteração de senha).
        *   **Response (200):** Dicionário com os requisitos (min_length, require_uppercase, etc.).

*   **Tag: Grupos (Descoberta)**
    *   `GET /grupos/disponivel`
        *   **Descrição:** Lista grupos dos quais o usuário logado não faz parte (para solicitar acesso).
        *   **Auth:** Requer token JWT válido.
        *   **Response (200):** `{"grupos": List[str]}`

**5.2. Roteador de Solicitações (`app/groups/requests_routes.py`)**

*   **Prefixo:** `/requests` (resultando em `/tools/requests/...`)
*   **Tag: Solicitações**
    *   `POST /`
        *   **Descrição:** Cria uma nova solicitação de acesso a um grupo.
        *   **Auth:** Requer token JWT válido.
        *   **Request Body:** `GroupAccessRequestCreate` (`{"grupo": "str", "justificativa": "str"}`)
        *   **Response (200):** `GroupAccessRequestResponse`
        *   **Response (400):** "Você já pertence ao grupo '<grupo>'"
        *   **Response (404):** "Grupo '<grupo>' não encontrado"
    *   `GET /me`
        *   **Descrição:** Lista todas as solicitações do usuário atual.
        *   **Auth:** Requer token JWT válido.
        *   **Response (200):** `List[GroupAccessRequestResponse]`
    *   `GET /admin`
        *   **Descrição:** Lista solicitações pendentes para grupos onde o usuário é admin (ou todas para `global_admin`).
        *   **Auth:** `admin` ou `global_admin`.
        *   **Response (200):** `List[GroupAccessRequestResponse]`
        *   **Response (403):** "Acesso restrito a administradores"
    *   `GET /{request_id}`
        *   **Descrição:** Obtém detalhes de uma solicitação específica.
        *   **Auth:** Usuário da solicitação, `admin` do grupo da solicitação, ou `global_admin`.
        *   **Path Param:** `request_id`.
        *   **Response (200):** `GroupAccessRequestResponse`
        *   **Response (403):** "Sem permissão para acessar esta solicitação"
        *   **Response (404):** "Solicitação não encontrada"
    *   `POST /{request_id}/review`
        *   **Descrição:** Aprova ou rejeita uma solicitação de acesso.
        *   **Auth:** `admin` do grupo da solicitação ou `global_admin`.
        *   **Path Param:** `request_id`.
        *   **Request Body:** `GroupAccessRequestReview` (`{"status": "RequestStatus ('approved'|'rejected')", "comment": "Optional[str]"}`)
        *   **Response (200):** `GroupAccessRequestResponse` (com o status atualizado).
        *   **Response (400):** "Solicitação já foi <status>"
        *   **Response (403):** "Acesso restrito a administradores" ou "Sem permissão para administrar este grupo"
        *   **Response (404):** "Solicitação não encontrada"
        *   **Response (500):** "Erro ao processar revisão" ou "Solicitação aprovada, mas houve erro ao adicionar usuário ao grupo" (se `apply_approved_request` falhar).

**6. Modelos Pydantic Principais (Schemas)**

*   **`app/groups/routes.py`:**
    *   `ToolResponseSchema(BaseModel)`:
        *   `id: str` (nome/ID da ferramenta)
        *   `nome: str`
        *   `url_base: str`
        *   `descricao: Optional[str]`
    *   `GroupDetailSchema(BaseModel)`:
        *   `id: str` (nome do grupo)
        *   `nome: str`
        *   `descricao: Optional[str]`
        *   `administradores: List[str]`
        *   `usuarios: List[str]`
        *   `ferramentas_disponiveis: List[ToolResponseSchema]`
    *   `UserDetailResponse(BaseModel)`:
        *   `username: str`
        *   `papel: str`
        *   `grupos: List[str]`
    *   `UserUpdateRequest(BaseModel)`:
        *   `papel: Optional[str]`
        *   `grupos: Optional[List[str]]`
        *   `ferramentas_disponiveis: List[ToolResponseSchema]` (Nota: este campo parece desalinhado com a lógica do endpoint `PUT /usuarios/{username_param}`, que não atualiza ferramentas diretamente no usuário, mas sim seus grupos e papel).
    *   `CreateGroupRequest(BaseModel)`:
        *   `nome: str`
        *   `descricao: Optional[str]`
    *   `EditGroupRequest(BaseModel)`:
        *   `nome: Optional[str]`
        *   `descricao: Optional[str]`

*   **`app/models/requests.py`:**
    *   `RequestStatus(str, Enum)`: `PENDING`, `APPROVED`, `REJECTED`.
    *   `GroupAccessRequestCreate(BaseModel)`:
        *   `grupo: str`
        *   `justificativa: str` (min_length=5, max_length=500)
    *   `GroupAccessRequestReview(BaseModel)`:
        *   `status: RequestStatus`
        *   `comment: Optional[str]` (max_length=500)
    *   `GroupAccessRequestResponse(BaseModel)`:
        *   `request_id: str`
        *   `username: str`
        *   `grupo: str`
        *   `status: RequestStatus`
        *   `justificativa: str`
        *   `created_at: datetime`
        *   `updated_at: Optional[datetime]`
        *   `reviewed_by: Optional[str]`
        *   `review_comment: Optional[str]`

**7. Lógica de Negócios Auxiliar**

*   **`app/utils/password_validator.py`:**
    *   `PasswordValidator` class e `default_validator` instance.
    *   `validate_password()`: Verifica comprimento mínimo, maiúsculas, minúsculas, dígitos, caracteres especiais, caracteres únicos.
    *   `get_requirements_text()`: Gera texto descritivo dos requisitos.
*   **`app/utils/password.py`:**
    *   `hash_password()`: Gera hash bcrypt (usado na migração).
    *   `migrate_rbac_passwords()`: Itera sobre usuários no `rbac.json` e converte senhas em texto plano para hash.
*   **`app/utils/request_manager.py`:**
    *   Gerencia o ciclo de vida das solicitações de acesso no `requests.json`.
    *   `apply_approved_request()`: Modifica o `rbac.json` para adicionar um usuário a um grupo após a aprovação da solicitação. Garante que o usuário seja adicionado à lista `users` do grupo e à lista `grupos` do próprio usuário.

**8. Considerações para Testes (Resumo)**

*   **Testes Unitários:**
    *   Funções em `app/auth.py` (verificação de senha, hashing, criação/validação de JWT).
    *   Funções em `app/utils/password_validator.py`.
    *   Funções em `app/utils/password.py`.
    *   Funções em `app/utils/request_manager.py` (simulando a leitura/escrita de arquivos JSON).
    *   Função `has_permission` em `app/groups/routes.py`.
*   **Testes de Integração (API Endpoints):**
    *   Para cada endpoint, testar:
        *   **Caminho Feliz:** Requisição válida com permissões corretas.
        *   **Validação de Payload:** Campos ausentes, tipos incorretos, valores inválidos.
        *   **Autorização:** Tentativas de acesso com papéis insuficientes ou sem ser o "dono" do recurso.
        *   **Casos de Borda:** Entidades não encontradas (404), conflitos (409), remoção do último admin, etc.
        *   **Respostas:** Código de status HTTP e schema do corpo da resposta.
        *   **Efeitos Colaterais:** Verificar se os arquivos `rbac.json` e `requests.json` são atualizados corretamente.
    *   **Fluxos Completos:**
        *   Criação de usuário -> Login -> Solicitação de acesso a grupo -> Aprovação pelo admin -> Verificação de acesso à ferramenta do grupo.
        *   Criação de grupo -> Adição de usuário -> Promoção a admin -> Remoção de admin.
        *   Alteração de senha.
        *   Migração de senhas.
