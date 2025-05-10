# Registro Temporário de Correções e Pendências de Testes

## Corrigido nesta iteração:
- Corrigido KeyError: 'members' ao padronizar o uso de 'users' e garantir compatibilidade para testes que esperam 'members' nos grupos.
- Corrigido erro de criação duplicada de usuário, retornando 409 Conflict corretamente.
- Corrigido KeyError em grupos recém-criados ao garantir a existência da chave 'users'.

## Falhas/Pendências atuais (exemplos):
- test_add_user_to_group_group_admin: Falha de permissão (403 ao invés de 200) — revisar se o admin de grupo está sendo corretamente designado no teste/setup.
- test_remove_user_from_group_group_admin: Falha de permissão (403 ao invés de 200) — revisar lógica de permissão para admin de grupo.
- test_designate_group_admin_user_not_in_group: Mensagem de erro diferente da esperada.
- Alguns testes de usuários ainda falham por detalhes de setup ou lógica de permissão.

## Próximos passos sugeridos:
- Revisar setup dos testes para garantir que o admin de grupo esteja corretamente atribuído antes das operações.
- Padronizar mensagens de erro para corresponder exatamente ao esperado nos asserts dos testes.
- Revisar lógica de permissão para admin de grupo nas rotas de adicionar/remover usuários.
- Validar se há outros pontos do backend que ainda usam 'members' e padronizar para 'users' (ou garantir compatibilidade temporária).
