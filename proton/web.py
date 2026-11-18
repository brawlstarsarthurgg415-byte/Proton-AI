"""A tiny local-only browser interface using Python's standard library."""
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from .core import Proton

proton = Proton()

PAGE = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Proton-AI</title><style>
*{box-sizing:border-box}body{margin:0;background:#081326;color:#edf4ff;font:16px system-ui,sans-serif;min-height:100vh;display:grid;place-items:center;padding:20px}
main{width:min(760px,100%);background:#111f3b;border:1px solid #30466e;border-radius:22px;padding:28px;box-shadow:0 20px 70px #0008}
h1{margin:0;font-size:2rem}p{color:#b8c9e8}.tag{color:#7de7ff;font-size:.85rem;letter-spacing:.12em}
form{display:grid;gap:12px;margin:22px 0}textarea{width:100%;min-height:100px;background:#081326;color:#fff;border:1px solid #40577f;border-radius:12px;padding:14px;font:inherit}
.actions{display:flex;gap:10px;flex-wrap:wrap}button{border:0;border-radius:10px;padding:12px 18px;background:#68d9f4;color:#071426;font-weight:700;cursor:pointer}button.secondary{background:#a78bfa}
.result{white-space:pre-wrap;background:#09172c;border:1px solid #2c4267;border-radius:12px;padding:16px;min-height:70px;line-height:1.6}
small{color:#9db2d6}
</style></head><body><main><div class="tag">PROTÓTIPO 0.1.0</div><h1>🧠 Proton-AI</h1><p>Ensine uma anotação ou faça uma pergunta sobre o que já está salvo na memória local.</p>
<form method="post"><textarea name="text" placeholder="Digite uma informação ou pergunta..."></textarea><div class="actions"><button name="action" value="learn">Ensinar ao Proton</button><button class="secondary" name="action" value="ask">Perguntar</button><button name="action" value="list">Ver memória</button></div></form>
<div class="result">__RESULT__</div><p><small>Os dados ficam no aparelho em que o Proton está executando. Esta versão não é um modelo de linguagem treinado.</small></p></main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _page(self, message: str = "") -> None:
        body = PAGE.replace("__RESULT__", escape(message)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self._page("Pronto. Como posso ajudar?")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 10000:
            self.send_error(413)
            return
        form = parse_qs(self.rfile.read(length).decode("utf-8", errors="replace"))
        text = form.get("text", [""])[0].strip()
        action = form.get("action", [""])[0]
        if action == "learn":
            try:
                item = proton.learn(text)
                message = f"Anotação {item['id']} salva na memória local. Obrigado pelo ensinamento!"
            except ValueError as exc:
                message = str(exc)
        elif action == "ask":
            results = proton.ask(text)
            message = "\n".join(f"• {item['text']}" for item in results) or "Não encontrei essa informação na memória. Você pode ensiná-la ao Proton."
        elif action == "list":
            items = proton.memory.all()
            message = "\n".join(f"{item['id']}. {item['text']}" for item in items) or "A memória ainda está vazia."
        else:
            message = "Ação não reconhecida."
        self._page(message)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8765), Handler)
    print("Proton-AI disponível em http://127.0.0.1:8765")
    print("Apenas conexões deste aparelho são aceitas. Ctrl+C para encerrar.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
