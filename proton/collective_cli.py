"""Command-line interface for Proton's shared knowledge exchange."""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from .collective import (
    CollectiveError, OUTBOX, export_training_text, publish_pending,
    publish_all_pending, submit, sync,
)
from .guardian import GuardianError, review_outbox


def main() -> None:
    parser = argparse.ArgumentParser(prog="proton-collective")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("submit", help="create a local contribution proposal")
    add.add_argument("content")
    add.add_argument("--kind", choices=("lesson", "ownership_claim", "correction"), default="lesson")
    add.add_argument("--subject", default="")
    add.add_argument("--source", action="append", default=[])

    pub = sub.add_parser("publish", help="upload a pending proposal to GitHub")
    pub.add_argument("id")

    sub.add_parser("sync", help="download the approved collective feed")

    watch = sub.add_parser("watch", help="retry queued uploads and receive approved knowledge while online")
    watch.add_argument("--interval", type=int, default=60, help="seconds between checks")

    guard = sub.add_parser("guard", help="screen queued proposals with local Qwen3Guard")
    guard.add_argument("--limit", type=int, default=20)
    guard.add_argument("--model", default="Qwen/Qwen3Guard-Gen-0.6B")

    export = sub.add_parser("export-training", help="export approved lessons for neural training")
    export.add_argument("--output", type=Path, default=Path("data/collective-training.txt"))

    args = parser.parse_args()
    try:
        if args.command == "submit":
            record = submit(args.content, kind=args.kind, sources=args.source, subject=args.subject)
            print(f"Proposta local criada: {record['id']}")
            print(f"Estado: {record['status']}")
            for report in record["review_reports"]:
                print(f"[{'OK' if report['passed'] else 'ATENÇÃO'}] {report['reviewer']}: {report['message']}")
            print("Nada foi publicado automaticamente. Revise o conteúdo antes de enviar.")
        elif args.command == "publish":
            print(f"Proposta enviada para revisão: {publish_pending(args.id)}")
        elif args.command == "sync":
            print(f"Registros aprovados recebidos: {sync()}")
        elif args.command == "watch":
            if args.interval < 10:
                parser.error("--interval must be at least 10 seconds")
            print("Sincronização coletiva ativa. Propostas ficam na fila sem internet.")
            print("Somente propostas submetidas explicitamente são enviadas; conversas privadas não são coletadas.")
            while True:
                try:
                    sent, failed = publish_all_pending()
                    received = sync()
                    if sent or received or failed:
                        print(f"Enviadas: {sent} | falhas mantidas na fila: {failed} | aprovadas recebidas: {received}")
                except (CollectiveError, OSError) as exc:
                    print(f"Sincronização indisponível; nova tentativa em breve: {exc}")
                time.sleep(args.interval)
        elif args.command == "guard":
            results = review_outbox(OUTBOX, limit=args.limit, model_id=args.model)
            for item in results:
                print(f"{item['id']}: {item['verdict']} | {item['recommendation']} | {', '.join(item['categories'])}")
            print(f"Propostas analisadas: {len(results)}")
            print("A Guardiã não aprova conteúdo nem o envia ao treinamento; resultados incertos ficam para revisão.")
        elif args.command == "export-training":
            print(f"Lições aprovadas exportadas: {export_training_text(args.output)}")
            print(f"Arquivo: {args.output}")
    except (CollectiveError, GuardianError, OSError) as exc:
        parser.exit(2, f"Erro: {exc}\\n")


if __name__ == "__main__":
    main()
