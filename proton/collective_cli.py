"""Command-line interface for Proton's shared knowledge exchange."""
from __future__ import annotations

import argparse
from pathlib import Path

from .collective import (
    CollectiveError, export_training_text, publish_pending, submit, sync,
)


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
        elif args.command == "export-training":
            print(f"Lições aprovadas exportadas: {export_training_text(args.output)}")
            print(f"Arquivo: {args.output}")
    except (CollectiveError, OSError) as exc:
        parser.exit(2, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
