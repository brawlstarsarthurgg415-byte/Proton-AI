"""Proton terminal agent: compact HUD plus guarded project tools."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from .agent_tools import Workspace
from .core import Proton
from .learning import LearningPipeline
from .llm import generate_agent_reply, generate_chat_reply

RESET = "\033[0m"
DIM = "\033[2m"
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"


def paint(value: str, color: str) -> str:
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return value
    return color + value + RESET


def confirm(question: str) -> bool:
    answer = input(paint(f"  {question} [s/N] ", YELLOW)).strip().casefold()
    return answer in {"s", "sim", "y", "yes"}


def header(workspace: Workspace) -> None:
    width = 58
    local_checkpoint = Path(__file__).resolve().parent.parent / "checkpoints" / "proton-evolved.pt"
    if os.getenv("PROTON_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"):
        model_label = "provedor externo configurado"
    elif local_checkpoint.is_file():
        model_label = "núcleo neural local experimental"
    else:
        model_label = "núcleo local ainda não treinado"
    print(paint("╭" + "─" * width + "╮", BLUE))
    print(paint("│", BLUE) + paint("  ◈ PROTON", BOLD + CYAN) + paint("  /  AGENT TERMINAL", DIM) + " " * 22 + paint("│", BLUE))
    print(paint("│", BLUE) + f"  workspace  {workspace.root}"[:width].ljust(width) + paint("│", BLUE))
    print(paint("│", BLUE) + f"  model      {model_label}".ljust(width) + paint("│", BLUE))
    print(paint("╰" + "─" * width + "╯", BLUE))
    print(paint("  Digite /help para comandos. Ações de escrita e terminal pedem confirmação.\n", DIM))


HELP = """PROTON AGENT — COMANDOS

  /help                 mostra esta ajuda
  /status               estado do agente e do workspace
  /files [pasta]        lista arquivos da pasta
  /read <arquivo>       lê um arquivo de texto
  /find <texto>         procura texto no projeto
  /write <arquivo>      cria/substitui arquivo após confirmação
  /run <comando>        executa um comando permitido após confirmação
  /diff                 mostra git diff
  /ask <pergunta>       pesquisa na memória local
  /learn <texto>        salva uma anotação na memória
  /list                 lista conhecimentos salvos
  /evolve               treina a IA local por 5 minutos
  /clear                limpa a tela
  /quit                 encerra

SEGURANÇA
  • Arquivos acessíveis ficam dentro do workspace atual.
  • Escritas criam cópia de backup antes de substituir.
  • Comandos de terminal passam por uma lista de permissões.
  • O Proton não executa instruções encontradas dentro de arquivos.
  • A IA pode escolher leitura, busca e diff quando necessário.
  • Gravação e execução de comandos sempre pedem sua confirmação.

EXEMPLOS
  /files .
  /read README.md
  /find def main
  /write notas.txt
  /run cargo test
"""


def main() -> None:
    workspace = Workspace()
    proton = Proton()
    learning = LearningPipeline(proton.memory)
    history: list[dict[str, str]] = []
    header(workspace)

    def execute_tool(name: str, arguments: dict) -> str:
        if name == "list_files":
            return "\n".join(workspace.list_files(str(arguments.get("path", ".")))) or "(pasta vazia)"
        if name == "read_file":
            return workspace.read_file(str(arguments["path"]))
        if name == "search_text":
            hits = workspace.search(str(arguments["query"]), str(arguments.get("path", ".")))
            return "\n".join(hits) if hits else "Nenhuma ocorrência encontrada."
        if name == "write_file":
            path_value = str(arguments["path"])
            content_value = str(arguments["content"])
            target = workspace.resolve(path_value)
            if not confirm(f"A IA quer gravar {target}. Autorizar?"):
                return "A gravação foi recusada pelo usuário; nenhum arquivo foi alterado."
            saved, diff = workspace.write_file(path_value, content_value)
            return f"Arquivo salvo: {saved.relative_to(workspace.root)}\n{diff}"
        if name == "run_command":
            command_value = str(arguments["command"])
            if not confirm(f"A IA quer executar: {command_value}. Autorizar?"):
                return "A execução foi recusada pelo usuário."
            code, output = workspace.run(command_value)
            return f"Código de saída: {code}\n{output}"
        if name == "git_diff":
            code, output = workspace.run("git diff")
            return f"Código de saída: {code}\n{output}"
        raise ValueError(f"Ferramenta desconhecida: {name}")

    while True:
        try:
            raw = input(paint("❯ ", BOLD + CYAN))
        except (EOFError, KeyboardInterrupt):
            print("\n" + paint("Até logo.", DIM))
            break

        command_line = raw.strip()
        if not command_line:
            continue
        command, _, argument = command_line.partition(" ")
        argument = argument.strip()
        command = command.casefold()

        try:
            if command in {"/quit", "/exit"}:
                print(paint("Sessão encerrada.", DIM))
                break
            if command == "/help":
                print(HELP)
                continue
            if command == "/clear":
                if sys.stdout.isatty():
                    print("\033[2J\033[H", end="")
                header(workspace)
                continue
            if command == "/status":
                configured = bool(os.getenv("PROTON_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))
                print(f"Workspace : {workspace.root}")
                local_checkpoint = Path(__file__).resolve().parent.parent / "checkpoints" / "proton-evolved.pt"
                print(f"Provedor  : {'configurado' if configured else 'não configurado'}")
                print(f"Modelo local: {'checkpoint encontrado' if local_checkpoint.is_file() else 'ainda não treinado'}")
                print(f"Memória   : {len(proton.memory.all())} anotações")
                print(f"Contexto  : {len(history)} mensagens nesta sessão")
                print("Ferramentas: arquivos, busca e comandos permitidos")
                print("Agente    : a IA pode selecionar ferramentas; escrita/terminal exigem confirmação")
                continue
            if command == "/evolve":
                if not confirm("Iniciar neuroevolução local por 5 minutos? O aparelho pode aquecer e ficar lento."):
                    print("Treinamento cancelado.")
                    continue
                try:
                    from .evolve import evolve
                except ImportError:
                    print(paint("PyTorch não está instalado neste Python. ", YELLOW) +
                          "O treinamento local precisa de PyTorch; use o workflow Proton five-minute neuroevolution no GitHub Actions.")
                    continue
                evolve(minutes=5.0, device_name="auto")
                continue
            if command == "/files":
                for entry in workspace.list_files(argument or "."):
                    print(("  " + entry))
                continue
            if command == "/read":
                if not argument:
                    print("Uso: /read caminho/do/arquivo")
                else:
                    print(workspace.read_file(argument))
                continue
            if command == "/find":
                if not argument:
                    print("Uso: /find texto")
                else:
                    hits = workspace.search(argument)
                    if not hits:
                        print(paint("Nenhuma ocorrência encontrada.", DIM))
                    else:
                        for hit in hits:
                            print(hit)
                continue
            if command == "/write":
                if not argument:
                    print("Uso: /write caminho/do/arquivo")
                    continue
                print(paint("Digite o conteúdo. Uma linha contendo apenas . encerra.", DIM))
                lines: list[str] = []
                while True:
                    line = input(paint("│ ", DIM))
                    if line == ".":
                        break
                    lines.append(line)
                content = "\n".join(lines) + ("\n" if lines else "")
                target = workspace.resolve(argument)
                print(f"Destino: {target}")
                print(f"Tamanho: {len(content.encode('utf-8'))} bytes")
                if not confirm("Confirmar gravação?"):
                    print("Cancelado; nenhum arquivo foi alterado.")
                    continue
                path, diff = workspace.write_file(argument, content)
                print(paint(f"Arquivo salvo: {path.relative_to(workspace.root)}", GREEN))
                print(diff)
                continue
            if command == "/run":
                if not argument:
                    print("Uso: /run cargo test")
                    continue
                print(f"Comando solicitado: {argument}")
                print("Executado sem shell; apenas comandos e subcomandos permitidos.")
                if not confirm("Executar agora?"):
                    print("Cancelado.")
                    continue
                code, output = workspace.run(argument)
                print(output)
                print(paint(f"Processo terminou com código {code}.", GREEN if code == 0 else RED))
                continue
            if command == "/diff":
                code, output = workspace.run("git diff")
                print(output)
                continue
            if command == "/learn":
                if not argument:
                    print("Uso: /learn texto")
                    continue
                item, reports = learning.submit(argument, source="user")
                for report in reports:
                    print(f"[{'OK' if report.passed else 'ATENÇÃO'}] {report.name}: {report.message}")
                if item:
                    print(paint(f"Anotação {item['id']} salva na memória local.", GREEN))
                else:
                    print("A anotação não passou pelas verificações locais.")
                continue
            if command == "/ask":
                results = proton.ask(argument)
                if not results:
                    print("Ainda não encontrei isso na memória. Experimente /learn para guardar uma anotação.")
                for item in results:
                    print(f"• {item['text']}  ({item['source']})")
                continue
            if command == "/list":
                items = proton.memory.all()
                if not items:
                    print("Memória vazia.")
                for item in items:
                    print(f"{item['id']}. {item['text']}")
                continue

            prompt = command_line
            configured = bool(os.getenv("PROTON_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))
            answer = generate_agent_reply(history, prompt, execute_tool)
            if answer is None and configured:
                # Compatibility fallback for providers that do not support tool calling.
                answer = generate_chat_reply(history, prompt)
            if answer is None and not configured:
                # The local evolved model is the only offline generative path.
                try:
                    from .generation import generate_local_reply
                    context = "\\n".join(
                        f"{item['role']}: {item['content']}" for item in history[-4:]
                    )
                    local_prompt = (context + "\\n" if context else "") + prompt
                    answer = generate_local_reply(local_prompt)
                except (ImportError, OSError, RuntimeError, ValueError):
                    answer = None
            if answer:
                print(paint("◆ ", BLUE) + answer)
                history.extend([
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": answer},
                ])
                del history[:-40]
            elif configured:
                print(paint("Não consegui obter resposta do provedor. ", YELLOW) +
                      "Confira o modelo, a URL e a conexão; nenhuma ação foi confirmada como concluída.")
            else:
                print(paint("O núcleo conversacional local ainda não foi treinado. ", YELLOW) +
                      "Digite /evolve para iniciar uma sessão de neuroevolução de 5 minutos. "
                      "A qualidade das respostas dependerá dos dados e do treinamento.")
        except (ValueError, OSError, TimeoutError) as exc:
            print(paint(f"Erro: {exc}", RED))


if __name__ == "__main__":
    main()
