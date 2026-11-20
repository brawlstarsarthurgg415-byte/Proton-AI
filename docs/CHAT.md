# Conversa informal do Proton

O Proton agora aceita mensagens comuns no terminal, sem exigir um comando para cada frase:

```bash
proton
```

Comandos continuam disponíveis:
- `/help`: mostra os comandos;
- `/learn texto`: envia uma anotação para revisão e memória;
- `/ask pergunta`: procura anotações;
- `/list`: lista a memória;
- `/quit`: encerra a conversa.

A primeira personalidade usa português brasileiro informal, gírias e brincadeiras leves. Ela mantém um contexto curto durante a sessão — por exemplo, pode responder com deboche por algumas mensagens depois de uma provocação e aceitar um pedido de desculpas.

## API privada

O endpoint autenticado `POST /chat` recebe:

```json
{
  "message": "E aí, Proton!",
  "session_id": null
}
```

Envie `Authorization: Bearer $PROTON_API_KEY`. A resposta contém `reply` e `session_id`; reutilize o identificador para continuar a mesma conversa.

## Limitações honestas

Esta etapa é um motor de respostas por regras, não um modelo de linguagem treinado. Ele reconhece algumas expressões e situações comuns, mas ainda não entende assuntos livres, não raciocina como uma pessoa e pode não captar ironia ou gírias novas. O contexto da API fica na memória do processo e se perde quando o serviço reinicia. Nenhuma API externa de IA é chamada.

O próximo passo para uma conversa realmente aberta é integrar um modelo de linguagem executado localmente, mantendo esta personalidade como orientação de estilo.
