# Proton Voice Training

O menu administrativo local é aberto pelo comando discreto `/p-admin` no terminal nativo do Proton (ou `/p-admin` no terminal Python). A primeira execução pede para criar uma senha de administrador com pelo menos 12 caracteres.

## Android / Termux

1. Instale o aplicativo Termux:API e conceda permissão de microfone ao Android.
2. No Termux, instale a ferramenta: `pkg install termux-api`.
3. Na pasta do repositório, instale a dependência de criptografia: `pip install "cryptography>=42"`.
4. Entre na pasta do repositório, inicie `proton` e digite `/p-admin`. Assim o Python encontra o módulo local.

O menu apresenta cinco frases e grava até oito segundos por frase usando `termux-microphone-record`. Os arquivos temporários são apagados após a criptografia. As amostras criptografadas ficam em `data/voice_vault/samples` (ou em `$PROTON_HOME/voice_vault/samples` quando PROTON_HOME estiver definido).

## Limites desta etapa

- A senha não é salva; o cofre usa scrypt para derivar a chave e Fernet para criptografar cada amostra.
- Esta implementação é uma coleta local de amostras, não um clonador nem um sintetizador de voz.
- Nenhuma gravação é enviada ao Railway, GitHub ou a uma API pública.
- Não há endpoint público de geração de voz e nenhum modelo de voz é publicado.
- A criptografia protege os arquivos armazenados; quem controla o dispositivo desbloqueado ou conhece a senha ainda pode acessar o conteúdo. Faça backup da senha com segurança: sem ela, as amostras não podem ser descriptografadas.
- Antes de qualquer compartilhamento ou geração pública, será necessária uma revisão de segurança, autorização explícita e proteções contra falsificação.
