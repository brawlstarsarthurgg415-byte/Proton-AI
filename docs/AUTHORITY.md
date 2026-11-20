# Proton Authority (primeira etapa)

O módulo `proton.authority` fornece uma base de autenticação e permissões para o painel.

## Cargos

- `ceo`: único proprietário configurado por `PROTON_OWNER_USERNAME`; pode promover/rebaixar usuários comuns para `official_admin` ou `user`.
- `official_admin`: consulta usuários e auditoria.
- `user`: altera somente as configurações básicas do próprio perfil e pode apagar as próprias memórias armazenadas neste subsistema.

Usuários comuns não têm endpoints para alterar a voz oficial, configurações globais ou dados de outras contas.

## Configuração necessária no servidor

Configure os seguintes segredos no gerenciador de variáveis do servidor (nunca no Git):

- `PROTON_PANEL_ACCESS_CODE`: senha global compartilhada exigida no cadastro, configuração do Authenticator e login.
- `PROTON_OWNER_USERNAME`: nome de usuário reservado para a conta CEO inicial.
- `PROTON_OWNER_BOOTSTRAP_CODE`: segredo separado, usado uma vez para registrar a conta CEO.
- `PROTON_TOTP_ENCRYPTION_KEY`: chave Fernet para cifrar os segredos TOTP em repouso. Gere com `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.

Cada conta também tem senha individual (hash scrypt) e TOTP de 6 dígitos. A sessão expira em 12 horas e pode ser revogada com logout. O segredo TOTP é mostrado apenas durante a configuração inicial; guarde-o no aplicativo autenticador.

## Rotas

- `POST /authority/register`
- `POST /authority/2fa/setup`
- `POST /authority/2fa/confirm`
- `POST /authority/login`
- `POST /authority/logout`
- `GET /authority/me`
- `GET/PATCH /authority/me/settings`
- `DELETE /authority/me/memory`
- `GET /authority/admin/users`
- `PATCH /authority/admin/users/{user_id}/role` (CEO)
- `GET /authority/admin/audit` (admin oficial ou CEO)

Todas as rotas administrativas, exceto cadastro e autenticação, exigem `Authorization: Bearer <token>`.

## Limites atuais

Esta é a camada inicial de identidade e autorização, não o painel gráfico completo. O login ainda precisa ser integrado a uma interface; as configurações e memórias deste subsistema ainda não estão conectadas ao motor de chat existente. Presença online, mensagens globais, recuperação por códigos, rate limiting, gerenciamento de dispositivos e treinamento de voz ficam para etapas seguintes. Não publique o serviço antes de configurar segredos, HTTPS, limites de tentativas e revisão de segurança.
