"""Interactive terminal for Proton."""
from .core import Proton
from .learning import LearningPipeline
from .llm import generate_chat_reply

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
    history: list[dict[str, str]] = []
    print("Proton-AI — bora trocar uma ideia? 😎")
    print("Manda uma mensagem ou digite /help pra ver os comandos.")
    while True:
        try:
            command = input("\nVocê > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nProton: Falou! Até a próxima KKKK.")
            break
        if command == "/p-admin":
            from .voice_admin import main as voice_admin_main
            voice_admin_main()
        elif command == "/quit":
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
            # Use the same generative adapter as the hosted API when a provider
            # key is configured. Keep the rule-based engine as an honest fallback.
            answer = generate_chat_reply(history, command)
            if answer:
                history.extend([
                    {"role": "user", "content": command},
                    {"role": "assistant", "content": answer},
                ])
                del history[:-24]
                print(f"Proton: {answer}")
            else:
                print(f"Proton [modo básico]: {proton.chat(command)}")


if __name__ == "__main__":
    main()
