"""Guarded local project tools used by the Proton terminal agent.

The tools are intentionally explicit: paths stay inside the chosen workspace,
writes require a caller-side confirmation, and terminal commands use argv (no shell).
"""
from __future__ import annotations

import difflib
import os
import subprocess
from pathlib import Path

IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "target", ".proton-backups"}
MAX_READ_BYTES = 160_000
SAFE_COMMANDS = {
    "pwd", "ls", "git", "python", "python3", "cargo", "npm",
}


class Workspace:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or os.environ.get("PROTON_WORKSPACE", Path.cwd())).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, value: str = ".") -> Path:
        candidate = (self.root / value).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Por segurança, só posso acessar arquivos dentro da pasta do projeto.") from exc
        return candidate

    def list_files(self, value: str = ".", limit: int = 80) -> list[str]:
        folder = self.resolve(value)
        if not folder.is_dir():
            raise ValueError("Esse caminho não é uma pasta.")
        results = []
        for path in sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold())):
            if path.name in IGNORED_DIRS or path.name.startswith(".proton-backup"):
                continue
            suffix = "/" if path.is_dir() else ""
            results.append(path.name + suffix)
            if len(results) >= limit:
                break
        return results

    def read_file(self, value: str) -> str:
        path = self.resolve(value)
        if not path.is_file():
            raise ValueError("Arquivo não encontrado.")
        if path.stat().st_size > MAX_READ_BYTES:
            raise ValueError("Arquivo grande demais para exibir de uma vez (limite de 160 KB).")
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Esse arquivo não parece ser texto UTF-8.") from exc

    def search(self, query: str, value: str = ".") -> list[str]:
        if not query.strip():
            raise ValueError("Informe o texto que deseja procurar.")
        folder = self.resolve(value)
        if not folder.is_dir():
            raise ValueError("A pasta de busca não existe.")
        hits: list[str] = []
        for base, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".proton-backup")]
            for name in files:
                path = Path(base) / name
                try:
                    if path.stat().st_size > 500_000:
                        continue
                    lines = path.read_text(encoding="utf-8").splitlines()
                except (OSError, UnicodeDecodeError):
                    continue
                for number, line in enumerate(lines, 1):
                    if query.casefold() in line.casefold():
                        hits.append(f"{path.relative_to(self.root)}:{number}: {line.strip()[:220]}")
                        if len(hits) >= 60:
                            return hits
        return hits

    def write_file(self, value: str, content: str) -> tuple[Path, str]:
        path = self.resolve(value)
        if path == self.root:
            raise ValueError("Escolha o nome de um arquivo.")
        if path.exists() and not path.is_file():
            raise ValueError("O destino existe e não é um arquivo.")
        path.parent.mkdir(parents=True, exist_ok=True)
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        backup = ""
        if path.exists():
            backup_dir = self.root / ".proton-backups"
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / (path.name + ".bak")
            backup_path.write_text(old, encoding="utf-8")
            backup = str(backup_path.relative_to(self.root))
        path.write_text(content, encoding="utf-8")
        diff = "".join(difflib.unified_diff(
            old.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=f"a/{path.relative_to(self.root)}",
            tofile=f"b/{path.relative_to(self.root)}",
        ))
        return path, (diff or "(sem diferenças)") + (f"\nBackup: {backup}" if backup else "")

    def run(self, command: str, timeout: int = 60) -> tuple[int, str]:
        import shlex
        argv = shlex.split(command)
        if not argv:
            raise ValueError("Informe um comando.")
        executable = Path(argv[0]).name
        if executable not in SAFE_COMMANDS:
            raise ValueError(f"Comando não permitido nesta versão: {executable}")
        if executable == "git" and len(argv) > 1 and argv[1] not in {"status", "diff", "log", "branch"}:
            raise ValueError("Por enquanto, Git só permite status, diff, log e branch.")
        if executable == "cargo" and len(argv) > 1 and argv[1] not in {"test", "check", "build"}:
            raise ValueError("Por enquanto, Cargo só permite test, check e build.")
        if executable in {"python", "python3"} and len(argv) > 1 and argv[1] not in {"-m"}:
            raise ValueError("Por enquanto, Python só permite executar módulos com -m.")
        if executable in {"npm"} and len(argv) > 1 and argv[1] not in {"test", "run"}:
            raise ValueError("Por enquanto, npm só permite test e run.")
        if executable == "npm" and len(argv) > 2 and argv[1] == "run" and argv[2] not in {"test", "typecheck", "lint", "build"}:
            raise ValueError("Script npm não liberado nesta versão.")
        if executable == "python" or executable == "python3":
            if len(argv) < 3 or argv[1] != "-m" or argv[2] not in {"pytest", "unittest"}:
                raise ValueError("Python só permite os módulos pytest e unittest nesta versão.")
        completed = subprocess.run(
            argv, cwd=self.root, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout, check=False,
        )
        output = completed.stdout[-20_000:] if completed.stdout else "(sem saída)"
        return completed.returncode, output
