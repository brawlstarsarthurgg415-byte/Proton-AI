# Plano técnico para desenvolver a inteligência do Proton

Este plano separa capacidades comprovadas de ideias futuras. O núcleo atual é um Transformer causal pequeno, treinado em nível de caractere. Ele **não é ainda um assistente conversacional** e não deve ser anunciado como um modelo que sabe programar.

## Estado confirmado no código

- Modelo Transformer decoder-only inicializado com pesos aleatórios.
- Treino causal de próximo caractere em corpus local.
- Divisão treino/validação (90/10) e medição de loss.
- Checkpoint com pesos, otimizador, vocabulário, configuração e estado de aleatoriedade.
- Retomada de checkpoint somente quando corpus/vocabulário/configuração são compatíveis.
- Testes unitários para forma da saída, atualização dos pesos, divisão de corpus, lotes e checkpoint.

A loss mede previsão de caracteres. Uma loss menor não prova compreensão, conhecimento factual, raciocínio ou capacidade de programação.

## Etapas obrigatórias

### 1. Dados de qualidade e rastreáveis

Cada conjunto deve ter fonte, licença/permissão, idioma, assunto, data de obtenção, método de limpeza e responsável pela revisão. Remover dados pessoais, segredos, duplicatas e conteúdo sem permissão. Separar treino, validação e teste por documento/fonte para reduzir vazamento.

### 2. Tokenizador adequado

Substituir o tokenizador de caractere por um tokenizador subword treinado em corpus permitido. Versionar o vocabulário e nunca reutilizar checkpoint com tokenizador diferente.

### 3. Avaliação antes de ampliar o modelo

Criar benchmarks separados para compreensão de leitura; perguntas e respostas com fatos presentes no contexto; matemática com passos verificáveis; programação (explicar código, completar funções e corrigir erros em sandbox); português e inglês; e segurança (reconhecer incerteza, instruções maliciosas e pedidos que não deve executar).

Manter conjuntos de teste privados do treinamento. Registrar score, versão do corpus, configuração, checkpoint e custo de execução.

### 4. Treinamento por fases

Começar com experimento pequeno e reproduzível. Só aumentar tamanho e duração se a avaliação independente melhorar. Monitorar overfitting, diversidade de exemplos, consumo de memória e temperatura do aparelho. Não usar sessões longas em celular como substituto de dados ou computação.

### 5. Assistente conversacional

Depois de validar o modelo base: formato de diálogo, ajuste supervisionado em exemplos permitidos, avaliação humana, geração com limites e memória recuperável. A memória deve distinguir fatos fornecidos pelo usuário, fontes externas e conteúdo gerado pelo próprio modelo.

### 6. Ferramentas e programação

Liberar leitura de arquivos primeiro; depois edição em cópia de trabalho, diff, testes e reversão. Terminal deve iniciar desabilitado, sem rede e com diretório permitido. Cada ferramenta precisa de autorização explícita, logs e limites. O modelo não ganha permissão irrestrita só porque produziu uma resposta plausível.

## Critérios para declarar uma capacidade

Uma capacidade só muda para “implementada” quando existe código executável, testes automatizados reproduzíveis, aprovação em exemplos não usados no treinamento, limitações documentadas e resultados reproduzíveis por versão.

## Próximo marco

Fechar a infraestrutura de dados e criar um benchmark independente de português/programação antes de aumentar o Transformer. Isso dará evidência de progresso real, em vez de apenas mais parâmetros ou mais horas de treino.
