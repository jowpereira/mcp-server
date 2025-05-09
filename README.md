# 🧠 MCP Gateway: Expondo Serviços Corporativos para LLMs

## Visão Geral

O **MCP Gateway** é uma aplicação baseada em [FastAPI](https://fastapi.tiangolo.com/) e [FastAPI-MCP](https://github.com/tadata-org/fastapi_mcp) que serve como uma camada de exposição de serviços e APIs internas da empresa para modelos de linguagem (LLMs). Ele atua como uma ponte segura e escalável, permitindo que LLMs interajam com APIs corporativas de forma controlada e contextualizada.

## Funcionalidades

* **Autenticação Segura:** Implementação de autenticação baseada em tokens (Bearer) para controlar o acesso aos endpoints.
* **Segregação por Grupos:** Organização de ferramentas por grupos, garantindo que cada grupo tenha acesso apenas às ferramentas designadas.
* **Exposição via MCP:** Transformação automática dos endpoints FastAPI em ferramentas MCP, facilitando a integração com LLMs.
* **Arquitetura Modular:** Estrutura de projeto organizada em módulos para facilitar a manutenção e escalabilidade.
* **Pronto para Produção:** Configurações e práticas recomendadas para ambientes de produção.

## Estrutura do Projeto

```
mcp-gateway/
├── app/
│   ├── main.py             # Ponto de entrada da aplicação
│   ├── auth.py             # Lógica de autenticação
│   ├── config.py           # Configurações da aplicação
│   ├── groups/
│   │   ├── __init__.py     # Inicialização do módulo de grupos
│   │   └── tools.py        # Definição das ferramentas
│   └── utils/
│       └── dependencies.py # Dependências reutilizáveis
├── data/
│   └── groups.json         # Definição dos grupos e suas ferramentas
├── requirements.txt        # Dependências do projeto
└── README.md               # Documentação do projeto
```

## Definição de Grupos e Ferramentas

A segregação de ferramentas por grupos é definida no arquivo `data/groups.json`. Cada grupo possui uma lista de ferramentas às quais tem acesso. Exemplo:

```json
{
  "grupo_a": {
    "token": "token_grupo_a",
    "ferramentas": ["ferramenta_x", "ferramenta_y"]
  },
  "grupo_b": {
    "token": "token_grupo_b",
    "ferramentas": ["ferramenta_z"]
  }
}
```

> **Nota:** No futuro, este arquivo pode ser substituído por uma base de dados NoSQL para maior flexibilidade e escalabilidade.

## Pré-requisitos

* Python 3.8 ou superior
* [Uvicorn](https://www.uvicorn.org/) para execução do servidor ASGI

## Instalação

1. Clone o repositório:

   ```bash
   git clone https://github.com/sua-empresa/mcp-gateway.git
   cd mcp-gateway
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

## Configuração

Defina as variáveis de ambiente necessárias no arquivo `.env` ou diretamente no ambiente:

```
SECRET_KEY=seu_token_secreto
```

## Execução

Inicie o servidor com o Uvicorn:

```bash
uvicorn app.main:app --reload
```

A aplicação estará disponível em `http://localhost:8000`.

## Autenticação

A autenticação é baseada em tokens Bearer. Para acessar os endpoints protegidos, inclua o cabeçalho `Authorization` nas requisições:

```
Authorization: Bearer token_grupo_a
```

> **Nota:** Os tokens devem corresponder aos definidos no arquivo `groups.json`.

## Segregação por Grupos

As ferramentas são organizadas por grupos, e cada grupo possui acesso apenas às ferramentas designadas. Isso é implementado por meio de dependências que verificam o grupo associado ao token de autenticação.

## Exposição via MCP

O FastAPI-MCP transforma automaticamente os endpoints FastAPI em ferramentas MCP. Após iniciar o servidor, as ferramentas estarão disponíveis no endpoint `/mcp`.

Exemplo de requisição para listar as ferramentas disponíveis:

```bash
curl -X GET "http://localhost:8000/mcp" -H "Authorization: Bearer token_grupo_a"
```

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests com melhorias, correções ou novas funcionalidades.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).