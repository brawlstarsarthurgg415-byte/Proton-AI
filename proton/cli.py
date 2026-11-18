"""Interactive terminal for Proton-AI."""
from .core import Proton
from .learning import LearningPipeline

HELP = """Comandos do Proton:
  /learn texto   envia uma anotação para revisão local e memória
  /ask pergunta  procura na memória
  /list          lista conhecimentos salvos
  /help          mostra esta ajuda
  /quit          encerra

A revisão local verifica clareza básica, origem e duplicidade.
Ela NÃO confirma se uma informação é verdadeira.
"""


def main() -> None:
    proton = Proton()
    learning = LearningPipeline(proton.memory)
    print("Proton-AI 0.2.0 — memória e revisão local")
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
            item, reports = learning.submit(command[7:], source="user")
            for report in reports:
                status = "OK" if report.passed else "ATENÇÃO"
                print(f"  [{status}] Professor {report.name}: {report.message}")
            if item:
                print(f"Proton: anotação {item['id']} aprovada nas verificações locais e salva.")
            else:
                print("Proton: não salvei a anotação. Revise os avisos acima.")
        elif command.startswith("/ask "):
            results = proton.ask(command[5:])
            if not results:
                print("Proton: ainda não encontrei isso na minha memória. Você pode me ensinar com /learn.")
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
