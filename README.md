# 🧠 Proton-AI

![Proton-AI banner](assets/proton-banner.svg)

<p align="center"><strong>Uma inteligência artificial experimental, construída para aprender, organizar conhecimento e evoluir com segurança.</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/Rust-native%20core-000000?logo=rust&logoColor=white" alt="Rust native core">\n  <img src="https://img.shields.io/badge/C%2B%2B-17-00599C?logo=cplusplus&logoColor=white" alt="C++17">\n  <img src="https://img.shields.io/badge/TypeScript-UI-3178C6?logo=typescript&logoColor=white" alt="TypeScript">\n  <img src="https://img.shields.io/badge/Python-research%20tools-3776AB?logo=python&logoColor=white" alt="Python research tools">
  <img src="https://img.shields.io/badge/Android-Termux-3DDC84?logo=android&logoColor=white" alt="Android Termux">
  <img src="https://img.shields.io/badge/status-prot%C3%B3tipo%20inicial-orange" alt="Status: protótipo inicial">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="Licença MIT">
</p>

**Proton-AI** é um projeto aberto para desenvolver uma inteligência artificial própria por etapas. A arquitetura agora é multilíngue: Rust fornece o primeiro núcleo nativo e a CLI `proton`; C++ contém uma biblioteca inicial de processamento de texto; TypeScript e JavaScript formam a base da interface e das ferramentas; Python permanece reservado para pesquisa, dados e treinamento experimental; Shell automatiza a instalação. Nem todos os módulos estão integrados ainda.

> **Importante:** esta é a fundação inicial do projeto, não um modelo de linguagem já treinado. A memória desta versão salva e recupera anotações; ela ainda não aprende pesos de uma rede neural nem conversa com a capacidade de um grande chatbot.

## ✨ Recursos e estado atual

| Recurso | Situação |
| --- | --- |
| Memória local de conhecimentos | 🟢 Implementada |
| Aprender anotações com revisão estrutural local | 🟢 Implementado |
| Consultar conhecimentos salvos | 🟢 Implementado |
| Interface de terminal | 🟢 Implementada |
| Interface gráfica local | 🟢 Implementada |
| Verificadores locais independentes (não são LLMs) | 🟢 Implementados |\n| Agentes professores baseados em modelos de IA | 🟡 Planejado |
| Treinamento de modelo próprio | 🟡 Planejado |
| Pesquisa online com fontes | 🟡 Planejado |
| Atualização validada e reversão | 🟡 Planejado |

## 🧰 Linguagens e responsabilidades

| Linguagem | Responsabilidade | Estado |
| --- | --- | --- |
| Rust | Núcleo nativo, CLI, memória e sessão de estudo | 🟢 Primeira versão |
| C++17 | Biblioteca inicial de tokenização | 🟡 Base criada, ainda não ligada ao núcleo |
| TypeScript | Tipos e estrutura da interface | 🟡 Base criada |
| JavaScript | Helpers de comandos da interface | 🟡 Base criada |
| Python | Pesquisa, preparação de dados e futuros experimentos de treino | 🟠 Módulos anteriores mantidos |
| Shell | Instalação e checagens de desenvolvimento | 🟢 Scripts criados |

A meta é que o comando principal seja `proton`, sem exigir que a pessoa execute módulos Python diretamente. O projeto ainda está em desenvolvimento e algumas linguagens têm componentes iniciais, não subsistemas completos.

## 📱 Instalação no Android (Termux)

No Termux, clone o repositório e execute o instalador:

```bash
pkg install git
git clone https://github.com/brawlstarsarthurgg415-byte/Proton-AI.git
cd Proton-AI
bash scripts/install-termux.sh
```

O instalador prepara Rust, Clang e CMake, compila o núcleo Rust e instala o comando `proton` no ambiente Termux. Depois, teste:

```bash
proton help
proton status
```

No Linux, instale Rust (Cargo) e execute:

```bash
cd native
cargo build --release
./target/release/proton help
```

## 💬 Comandos próprios do Proton

Depois de instalar o núcleo nativo, os comandos são:

| Comando | Função |
| --- | --- |
| `proton help` | Ajuda |
| `proton version` | Versão instalada |
| `proton status` | Estado e memória local |
| `proton learn "texto"` | Salva uma anotação |
| `proton ask "termos"` | Pesquisa na memória |
| `proton memory` | Lista as anotações |
| `proton study --hours 15` | Sessão de estudo de 15 horas |

Os comandos são executados pelo binário Rust. Os dados do núcleo nativo ficam em `data/memory.txt` e `data/study_progress.txt` (ou no diretório indicado por `PROTON_HOME`).

A busca e a memória ainda são simples. O núcleo nativo é uma fundação, não um chatbot neural completo.

## 🧩 Como modificar

- `native/src/main.rs`: comandos e núcleo Rust.
- `cpp/src/tokenizer.cpp`: tokenização C++.
- `ui/src/proton.ts`: tipos e estado da interface TypeScript.
- `ui/src/commands.js`: auxiliares JavaScript.
- `scripts/install-termux.sh`: instalador do Termux.
- `proton/`: protótipos Python anteriores para pesquisa e experiências.

Para compilar o núcleo: `cd native && cargo build --release`.
Para rodar testes Rust: `cd native && cargo test`.
Para compilar C++: `cmake -S cpp -B cpp/build && cmake --build cpp/build`.
Para verificar TypeScript: `cd ui && npm install && npm run typecheck`.

## 🗂️ Estrutura do projeto

```text
-Proton-AI/
├── assets/
├── data/                 # criada localmente ao executar
├── proton/
│   ├── core.py
│   ├── memory.py
│   ├── cli.py
│   └── web.py
├── tests/
├── .github/workflows/
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## 🔐 Privacidade e segurança

- A memória fica no aparelho, dentro de `data/knowledge.json`.
- A pasta `data/` é ignorada pelo Git para não publicar suas anotações pessoais.
- Nunca publique senhas, tokens ou chaves de API.
- A interface web escuta somente em `127.0.0.1`, isto é, no próprio aparelho.
- As verificações locais não validam a verdade de uma informação. Esta versão não baixa nem executa atualizações automaticamente.
- Futuras pesquisas online deverão guardar fontes e tratar páginas externas como conteúdo não confiável.

## 📚 Sessão de estudos de 15 horas

O Proton inclui um currículo inicial offline com lições introdutórias de programação, matemática, ciências, astronomia, física, biologia, história, geografia, inglês, comunicação, computação e pensamento crítico.

Para iniciar uma sessão de 15 horas no Termux:

```bash
python -m proton.study --hours 15
```

O programa percorre as lições, faz ciclos de revisão com baixo uso de CPU e salva checkpoints em `data/study_progress.json`. Se parar com Ctrl+C, o progresso fica salvo; ao iniciar novamente, ele continua do próximo item. Para uma execução curta de teste:

```bash
python -m proton.study --hours 0.01 --interval 1
```

**Limites desta versão:** o currículo é pequeno e introdutório; não cobre todo o conhecimento humano, não pesquisa a internet, não faz perguntas adaptativas e não treina os pesos de uma rede neural. Repetir as lições por 15 horas não cria, por si só, um modelo inteligente. A etapa seguinte é adicionar fontes educacionais verificáveis, exercícios, avaliação e, separadamente, um pipeline real de treinamento.

**No celular:** uma sessão de 15 horas pode aquecer o aparelho e consumir bateria. Use apenas com ventilação, evite superfícies que bloqueiem a dissipação de calor e interrompa se o aparelho aquecer demais. O Android pode suspender processos em segundo plano; mantenha o Termux aberto e não conte com execução garantida com o aplicativo fechado.

## 🧪 Testes

```bash
python -m unittest discover -s tests\ncd native && cargo test
```

## 🤝 Como contribuir

1. Faça um fork ou uma cópia do repositório.
2. Crie uma mudança pequena e explique o motivo.
3. Execute os testes.
4. Envie uma proposta descrevendo o que mudou e como testar.

## 📜 Licença

O projeto usa a licença MIT. Leia o arquivo [LICENSE](LICENSE).

---

<p align="center"><strong>Proton-AI — aprendendo passo a passo.</strong><br><sub>Projeto experimental: recursos planejados não são recursos já implementados.</sub></p>
