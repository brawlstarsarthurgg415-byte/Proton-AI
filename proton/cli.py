"""Interactive terminal for Proton."""
from .core import Proton
from .learning import LearningPipeline

HELP = """Comandos do Proton:
  /learn texto   envia uma anotação para revisão local e memória
  /ask pergunta  procura na memória
  /list          lista conhecimentos salvos
  /help          mostra esta ajuda
  /quit          encerra

Pode conversar normalmente também: o Proton responde no estilo informal brasileiro.
A personalidade atual usa regras e contexto curto da sessão; ainda não é um LLM.
"""


def main() -> None:
    proton = Proton()
    learning = LearningPipeline(proton.memory)
    print("Proton-AI — bora trocar uma ideia? 😎")
    print("Manda uma mensagem ou digite /help pra ver os comandos.")
    while True:
        try:
            command = input("\nVocê > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nProton: Falou! Até a próxima KKKK.")
            break
        if command == "/quit":
            print("Proton: Demorô, fui nessa! 😎")
            break
        if command == "/help":
            print(HELP)
        elif command.startswith("/learn "):
            item, reports = learning.submit(command[7:], source="user")
            for report in reports:
                status = "OK" if report.passed else "ATENÇÃO"
                print(f"  [{status}] Professor {report.name}: {report.message}")
            if item:
                print(f"Proton: Boa! Anotação {item['id']} salva depois das verificações locais.")
            else:
                print("Proton: Não salvei essa, confere os avisos ali em cima.")
        elif command.startswith("/ask "):
            results = proton.ask(command[5:])
            if not results:
                print("Proton: Ainda não achei isso na minha memória. Se quiser, me ensina com /learn.")
            else:
                print("Proton: Ó, achei isso aqui:")
                for item in results:
                    print(f"  • {item['text']} (fonte: {item['source']})")
        elif command == "/list":
            items = proton.memory.all()
            if not items:
                print("Proton: Minha memória tá vazia ainda KKKK.")
            for item in items:
                print(f"  {item['id']}. {item['text']}")
        elif command:
            print(f"Proton: {proton.chat(command)}")


if __name__ == "__main__":
    main()
