"""Interactive terminal for Proton-AI."""
from .core import Proton

HELP = """Comandos do Proton:
  /learn texto   salva um conhecimento na memória
  /ask pergunta  procura na memória
  /list          lista conhecimentos salvos
  /help          mostra esta ajuda
  /quit          encerra
"""


def main() -> None:
    proton = Proton()
    print("Proton-AI 0.1.0 — protótipo de memória local")
    print("Digite /help para ver os comandos.")
    while True:
        try:
            command = input("\nVocê > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nProton encerrado.")
            break
        if command == "/quit":
            print("Proton encerrado.")
            break
        if command == "/help":
            print(HELP)
        elif command.startswith("/learn "):
            try:
                item = proton.learn(command[7:])
                print(f"Proton: conhecimento {item['id']} salvo na memória local.")
            except ValueError as exc:
                print(f"Proton: {exc}")
        elif command.startswith("/ask "):
            results = proton.ask(command[5:])
            if not results:
                print("Proton: ainda não encontrei isso na memória. Você pode me ensinar com /learn.")
            else:
                print("Proton: encontrei estas anotações:")
                for item in results:
                    print(f"  • {item['text']} (fonte: {item['source']})")
        elif command == "/list":
            items = proton.memory.all()
            if not items:
                print("A memória ainda está vazia.")
            for item in items:
                print(f"  {item['id']}. {item['text']}")
        elif command:
            print("Comando não reconhecido. Digite /help.")


if __name__ == "__main__":
    main()
