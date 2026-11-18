# Arquitetura multilíngue do Proton-AI

Cada linguagem tem uma responsabilidade delimitada. A regra é evitar duplicar o mesmo sistema em várias linguagens sem necessidade: cada módulo faz uma tarefa e troca dados por formatos documentados.

## Módulos e responsabilidades

| Linguagem | Módulo | Tarefa concreta | Entrada e saída |
|---|---|---|---|
| Rust | `native/` | Comando `proton`, memória local, currículo e checkpoints | Argumentos do terminal e arquivos locais |
| Python | `proton/` | Modelo neural experimental, treinamento e avaliação | Corpus de texto e checkpoints PyTorch |
| C++17 | `cpp/` | Tokenização e rotinas de texto de baixo nível | Texto UTF-8; sequência de tokens |
| TypeScript | `ui/src/proton.ts` | Tipos, estado e descrição das funções da interface | Tipos e objetos de estado |
| JavaScript | `ui/src/commands.js` | Montar comandos de interface com validação de entrada | Texto digitado; comando validado |
| Shell | `scripts/` | Instalação e verificações do ambiente | Sistema operacional e comandos |
| Go | `go/cmd/corpuscheck/` | Verificar se um corpus é UTF-8 e tem conteúdo mínimo | Arquivo de texto; resultado de validação |
| Java | `java/` | Tokenização Unicode para ferramentas JVM | Texto; palavras normalizadas |
| Ruby | `ruby/corpus_report.rb` | Relatório de tamanho e repetição aproximada do corpus | Arquivo de texto; estatísticas |
| PHP | `php/public/status.php` | Endpoint HTTP de estado, somente leitura | Requisição HTTP; JSON de status |
| C# | `csharp/Proton.Tools/` | Verificação básica de arquivo de corpus no .NET | Arquivo de texto; resultado de validação |
| Swift | `swift/` | Tokenização Unicode para ferramentas Apple | Texto; palavras normalizadas |

## Como os módulos cooperam

1. O Rust oferece a interface de terminal e mantém os dados locais.
2. A interface usa TypeScript para tipos e JavaScript para preparar comandos.
3. C++, Java e Swift oferecem implementações de tokenização para diferentes ambientes.
4. Go, Ruby e C# verificam ou descrevem arquivos de dados antes de serem usados.
5. PHP expõe um status HTTP de leitura.
6. Python executa o experimento de treinamento neural e avaliação.

## Estado real da integração

Os módulos acima já têm arquivos de código, mas nem todos estão conectados ao processo principal. Em especial, o comando Rust ainda não chama o treinador Python automaticamente; os tokenizadores alternativos não são ainda uma biblioteca comum chamada pelo núcleo. Essa integração deve ser feita com testes de contrato e formatos de dados estáveis, sem alegar que está pronta antes de funcionar.

## Verificação local

Consulte os comandos de compilação e teste no README principal. O workflow `.github/workflows/extra-languages.yml` verifica compilação/sintaxe dos módulos Go, Java, Ruby, PHP, C#, Swift; o workflow multilíngue cobre Rust, C++, TypeScript.
