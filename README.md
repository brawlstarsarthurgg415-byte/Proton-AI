# 🧠 Proton-AI

![Proton-AI banner](assets/proton-banner.svg)

<p align="center"><strong>Uma inteligência artificial experimental, construída para aprender, organizar conhecimento e evoluir com segurança.</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/Rust-n%C3%BAcleo%20nativo-000000?logo=rust&logoColor=white" alt="Rust">
  <img src="https://img.shields.io/badge/C%2B%2B-17-00599C?logo=cplusplus&logoColor=white" alt="C++17">
  <img src="https://img.shields.io/badge/TypeScript-interface-3178C6?logo=typescript" alt="TypeScript">
  <img src="https://img.shields.io/badge/JavaScript-ferramentas-F7DF1E?logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/Python-treinamento%20neural-3776AB?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Shell-automa%C3%A7%C3%A3o-4EAA25?logo=gnubash" alt="Shell">
  <img src="https://img.shields.io/badge/Go-utilit%C3%A1rios-00ADD8?logo=go" alt="Go">
  <img src="https://img.shields.io/badge/Java-JVM-ED8B00?logo=openjdk" alt="Java">
  <img src="https://img.shields.io/badge/Ruby-ferramentas-CC342D?logo=ruby" alt="Ruby">
  <img src="https://img.shields.io/badge/PHP-web-777BB4?logo=php" alt="PHP">
  <img src="https://img.shields.io/badge/C%23-.NET-512BD4?logo=dotnet" alt="C#">
  <img src="https://img.shields.io/badge/Swift-adaptador-F05138?logo=swift" alt="Swift">
  <img src="https://img.shields.io/badge/Android-Termux-3DDC84?logo=android" alt="Android Termux">
  <img src="https://img.shields.io/badge/status-em%20desenvolvimento-orange" alt="Em desenvolvimento">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT">
</p>

**Proton-AI** é um projeto aberto para desenvolver uma inteligência artificial própria por etapas. A proposta é ter um núcleo neural próprio, memória local, ferramentas de estudo, agentes auxiliares especializados, interfaces e mecanismos de avaliação e evolução controlada.

> **Importante:** o projeto está em desenvolvimento. Já existe uma primeira base de memória, comandos, currículo offline e componentes em várias linguagens. O treinamento neural próprio foi iniciado como protótipo experimental; isso ainda não significa que exista um assistente inteligente pronto ou comparável a grandes modelos.

## ✨ Visão e recursos

| Recurso | Estado atual |
| --- | --- |
| Memória local de conhecimentos | 🟢 Implementada no protótipo |
| Aprender e consultar anotações | 🟢 Implementado |
| Interface de terminal com comando `proton` | 🟢 Primeira versão em Rust |
| Interface web local | 🟢 Protótipo existente |
| Currículo de estudos offline | 🟢 Implementado |
| Núcleo neural próprio, iniciado com pesos aleatórios | 🟡 Protótipo de treinamento adicionado |
| Corpus inicial de diálogos em português | 🟡 Adicionado; ainda pequeno e experimental |
| Professores auxiliares especializados | 🟡 Primeiros revisores por regras; ainda não são LLMs |
| Treinamento longo e retomada robusta de checkpoints | 🟡 Em desenvolvimento |
| Conjunto de dados amplo, validado e com fontes | 🔴 Ainda necessário |
| Pesquisa online com fontes verificáveis | 🟡 Planejado |
| Atualizações automáticas verificadas, backup e reversão | 🟡 Planejado |
| Interface gráfica completa conectada ao núcleo neural | 🟡 Planejada |

## 🧰 Arquitetura multilíngue

O Proton **não é um projeto somente em Python**. Cada linguagem tem uma responsabilidade. Algumas partes já existem como protótipos e ainda precisam ser conectadas entre si.

| Linguagem | Responsabilidade no projeto | Situação |
| --- | --- | --- |
| **Rust** | Núcleo nativo, CLI `proton`, memória e sessão de estudo | Primeira versão funcional |
| **C++17** | Biblioteca de processamento/tokenização de texto e futuras rotinas de desempenho | Base criada; integração pendente |
| **TypeScript** | Tipos, estado e estrutura da interface | Base criada |
| **JavaScript** | Helpers e comandos da interface | Base criada |
| **Python** | Pesquisa de arquitetura neural, preparação de dados, treinamento e avaliação experimental | Modelo e pipeline inicial adicionados |
| **Shell** | Instalação e automação no Termux/Linux | Scripts criados |
| **Go** | Verificação básica de corpus de treinamento | CLI e teste inicial |
| **Java** | Tokenização Unicode para adaptadores JVM | Protótipo criado |
| **Ruby** | Relatório de estatísticas de corpus | Ferramenta inicial |
| **PHP** | Endpoint HTTP de status somente leitura | Protótipo criado |
| **C#** | Ferramenta de validação de corpus no ecossistema .NET | CLI inicial |
| **Swift** | Tokenização para futuras integrações Apple | Protótipo criado |

A ideia é usar a linguagem mais adequada para cada subsistema, mantendo interfaces claras entre eles. Python é usado agora no experimento de treinamento neural porque o protótipo usa PyTorch; isso não substitui nem elimina Rust, C++, TypeScript, JavaScript, Shell, Go, Java, Ruby, PHP, C# ou Swift.

## 🧩 Arquitetura multilíngue

Cada linguagem tem uma responsabilidade específica. Veja a tabela completa de módulos, entradas, saídas e limites de integração em [docs/ARQUITETURA-MULTILINGUE.md](docs/ARQUITETURA-MULTILINGUE.md).

## 🧠 Como o aprendizado funciona

O Proton separa três coisas diferentes:

1. **Memória:** guarda anotações e permite procurá-las depois. Guardar texto não altera os pesos de uma rede neural.
2. **Treinamento neural:** o núcleo recebe sequências de exemplos, calcula uma perda (*loss*) e atualiza seus próprios pesos por gradiente.
3. **Professores auxiliares:** revisam e ajudam a organizar exemplos. Os primeiros professores deste repositório são verificadores simples por regras; não são modelos de linguagem e não garantem que uma afirmação esteja correta.

O modelo experimental atual é um Transformer pequeno, inicializado do zero e baseado em caracteres. O arquivo `data/conversation-pt.txt` contém diálogos originais em português para começar a expor o modelo a padrões de conversa; `data/starter.txt` acrescenta exemplos gerais. Ambos são pequenos e insuficientes para produzir conversa confiável. O modelo ainda não tem tokenizer BPE nem ajuste de instruções, portanto não espere respostas naturais só por treinar esse corpus. Um modelo útil exige dados diversos e permitidos, validação independente, tokenizer adequado, treinamento e hardware compatíveis.

### Treinamento experimental

Instale Python 3.10 ou superior e as dependências:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

No Windows, ative o ambiente com `.venv\\Scripts\\activate`.

Execute um teste curto:

```bash
proton-train --hours 0.05
```

Ou limite também o número de passos:

```bash
proton-train --hours 0.1 --max-steps 100
```

O treinador começa com pesos aleatórios, usa `data/conversation-pt.txt` por padrão, separa 90% do texto para treino e 10% para validação, mede as duas perdas e grava um checkpoint em `checkpoints/proton-latest.pt`. Agora também aceita `--resume` para continuar um checkpoint compatível e parâmetros para reduzir/aumentar o modelo. O padrão é deliberadamente curto e limitado (até 500 passos ou cerca de 72 segundos), para evitar sessões longas acidentais.

Exemplo de execução controlada:

```bash
proton-train --hours 0.02 --max-steps 100
```

Para continuar um checkpoint compatível:

```bash
proton-train --hours 0.02 --max-steps 100 --resume
```

O checkpoint guarda pesos, estado do otimizador, vocabulário, configuração, passo e métricas. A retomada é recusada se o corpus ou a configuração não corresponderem. O arquivo de validação é uma divisão do mesmo corpus, portanto ainda não é um benchmark independente de conhecimento ou programação.

**Sobre as 15 horas:** esse valor representa um limite de tempo, não uma garantia de inteligência ou qualidade. Antes de uma sessão longa, precisamos ampliar e validar o conjunto de dados, implementar avaliação separada e testar retomada de checkpoints. Não deixe um celular treinando por 15 horas sem supervisão: o aparelho pode aquecer, consumir bateria ou suspender o processo.

## 📱 Instalação do núcleo nativo no Android (Termux)

No Termux:

```bash
pkg install git
git clone https://github.com/brawlstarsarthurgg415-byte/Proton-AI.git
cd Proton-AI
bash scripts/install-termux.sh
```

Depois:

```bash
proton help
proton status
```

O instalador prepara Rust, Clang e CMake, compila o núcleo Rust e instala o comando `proton`.

No Linux, a compilação manual do núcleo Rust é:

```bash
cd native
cargo build --release
./target/release/proton help
```

## 🖥️ Terminal interativo Proton

Execute apenas `proton` para abrir a interface de terminal com mascote ASCII e comandos no estilo de um agente de programação.

Comandos visuais disponíveis: `/help`, `/plan`, `/permissions`, `/agents`, `/terminal`, `/files`, `/diff`, `/undo`, `/model`, `/status`, `/memory`, `/study`, `/clear` e `/exit`.

**Limite atual:** essa é a primeira estrutura de interface. Os comandos de planejamento, agentes, terminal, edição de arquivos, diff e undo informam seu estado, mas ainda não executam tarefas inteligentes. O Proton precisa aprender programação e ganhar ferramentas reais antes de receber autonomia para alterar projetos.

## 💬 Comandos nativos disponíveis

| Comando | Função |
| --- | --- |
| `proton help` | Mostra a ajuda |
| `proton version` | Mostra a versão |
| `proton status` | Mostra o estado e os dados locais |
| `proton learn "texto"` | Salva uma anotação |
| `proton ask "termos"` | Pesquisa na memória |
| `proton memory` | Lista as anotações |
| `proton study --hours 15` | Inicia uma sessão curricular |

Os dados do núcleo Rust ficam em `data/memory.txt` e `data/study_progress.txt`, ou no diretório indicado por `PROTON_HOME`. Esses comandos nativos ainda não chamam automaticamente o treinador neural Python; essa integração é uma etapa de desenvolvimento.

## 📚 Currículo de estudos offline

O projeto também mantém um currículo introdutório com conteúdos de:

- Programação e computação
- Matemática
- Ciências e física
- Astronomia
- Biologia
- História e geografia
- Inglês
- Comunicação
- Pensamento crítico

A sessão curricular percorre lições e salva checkpoints. **Ela não treina os pesos do modelo neural.** Repetir lições durante 15 horas não transforma automaticamente o currículo em treinamento de rede neural.

## 🗂️ Estrutura do repositório

```text
Proton-AI/
├── .github/workflows/   # testes automáticos
├── assets/              # banner e identidade visual
├── cpp/                 # biblioteca C++17
├── csharp/              # ferramentas .NET em C#
├── go/                  # utilitários Go para dados
├── java/                # adaptador Java/JVM
├── php/                 # adaptador HTTP PHP
├── ruby/                # ferramentas de corpus Ruby
├── swift/               # adaptador Swift
├── data/                # corpus público de demonstração
├── native/              # núcleo e CLI Rust
├── proton/              # modelo neural, treino e ferramentas Python
├── scripts/             # instalação e checagens
├── tests/               # testes
├── ui/                  # TypeScript e JavaScript
├── README.md
├── pyproject.toml
└── requirements.txt
```

## 🧪 Verificações de desenvolvimento

Rust:

```bash
cd native
cargo test
```

C++:

```bash
cmake -S cpp -B cpp/build
cmake --build cpp/build
```

Python:

```bash
python -m unittest discover -s tests -v
```

TypeScript:

```bash
cd ui
npm install
npm run typecheck
```

Os testes automáticos do GitHub Actions verificam os componentes configurados nos workflows. Um commit enviado não significa, por si só, que todos os testes passaram; confira a aba **Actions**.

## 🔐 Segurança, dados e evolução

- Não coloque senhas, tokens ou chaves de API no repositório.
- Use somente dados que você tem permissão para utilizar no treinamento.
- Registre a origem dos conjuntos de dados e mantenha exemplos de validação separados.
- Trate textos baixados e respostas de agentes como conteúdo não confiável; nunca execute instruções encontradas dentro deles.
- Mudanças automáticas no núcleo devem passar por testes, backups e possibilidade de reversão.
- O projeto ainda não instala atualizações de modelo automaticamente.

## 🤝 Como contribuir

1. Faça um fork ou uma cópia do repositório.
2. Faça uma alteração pequena e explique o motivo.
3. Execute os testes relevantes.
4. Envie uma proposta descrevendo a mudança e como verificá-la.

## 📜 Licença

Este projeto usa a licença MIT. Consulte o arquivo [LICENSE](LICENSE).

---

<p align="center"><strong>Proton-AI — aprendendo, construindo e evoluindo passo a passo.</strong><br><sub>Projeto experimental: recursos planejados não são recursos já implementados.</sub></p>


## 🛡️ IA Guardiã local\n\nO módulo opcional `Qwen3Guard-Gen-0.6B` faz uma triagem de segurança das propostas coletivas sem chamar uma API externa. Instale com `pip install -e '.[guardian]'` e execute `proton-collective guard --limit 20`. A classificação é apenas auxiliar: nem mesmo um resultado `Safe` aprova uma proposta ou a libera para treinamento. Veja [docs/GUARDIAN.md](docs/GUARDIAN.md). O comando é manual nesta etapa; serviço 24/7 ainda não foi implantado.\n\n## 🌐 Rede coletiva de ensinamentos

O módulo experimental `proton-collective` permite preparar contribuições locais, publicar propostas no GitHub, baixar um feed público aprovado e exportar lições selecionadas para o próximo treinamento neural.

```bash
proton-collective submit "Uma explicação documentada..." --source https://example.org/artigo
proton-collective sync
proton-collective export-training
```

Para publicar uma proposta, revise o arquivo local e configure `PROTON_GITHUB_TOKEN` com um token limitado a este repositório e permissão **Contents: write**. O comando `proton-collective publish ID` envia a proposta para `collective/incoming/`; publicar não significa aprovar.

**Portões de confiança:** verificações locais de privacidade, fonte e duplicidade são heurísticas determinísticas, não outras IAs. Duas avaliações externas distintas podem ser registradas como etapa de revisão, mas ainda exigem curadoria do mantenedor. Só registros explicitamente aprovados em `collective/approved.jsonl`, com `training_eligible: true`, entram no corpus do treinamento do GitHub Actions. Declarações de propriedade de marcas ficam como declarações não verificadas e nunca entram no treino.

O treinador atual modifica pesos PyTorch de um pequeno Transformer de caracteres. O workflow produz um checkpoint como artefato; a instalação automática desse checkpoint nos aparelhos e a integração com revisores de IA independentes ainda não estão implementadas. Consulte [collective/README.md](collective/README.md) para detalhes, privacidade e comandos.
