"""Local, password-protected voice sample vault for Proton.

Recordings stay on this device. This module does not upload audio or train/publish
a voice model. Encrypted samples are only a protected collection step.
"""
from __future__ import annotations

import base64
import getpass
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

PHRASES = [
    "Oi, eu sou o dono da voz do Proton.",
    "Hoje está um dia muito bom para aprender coisas novas.",
    "O Proton é meu projeto de inteligência artificial.",
    "Esta é uma gravação de treinamento da minha própria voz.",
    "Olá! Como posso ajudar você hoje?",
]
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def _paths() -> tuple[Path, Path, Path]:
    root = Path(os.environ.get("PROTON_HOME", "data")).expanduser() / "voice_vault"
    return root, root / "admin.json", root / "samples"


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=SCRYPT_N,
        r=SCRYPT_R, p=SCRYPT_P, dklen=32,
    )


def _fernet(password: str, salt: bytes):
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise RuntimeError(
            'Dependência ausente. Instale com: pip install "cryptography>=42"'
        ) from exc
    key = base64.urlsafe_b64encode(_derive(password, salt))
    return Fernet(key)


def _secure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass


def _setup_password(config: Path) -> str:
    print("\nPrimeiro acesso: crie uma senha administrativa forte (mínimo 12 caracteres).")
    while True:
        password = getpass.getpass("Nova senha: ")
        if len(password) < 12:
            print("Use pelo menos 12 caracteres.")
            continue
        confirm = getpass.getpass("Repita a senha: ")
        if not hmac.compare_digest(password, confirm):
            print("As senhas não coincidem.")
            continue
        salt = os.urandom(16)
        key = _derive(password, salt)
        verifier = hmac.new(key, b"Proton Voice Vault v1", hashlib.sha256).hexdigest()
        config.write_text(json.dumps({
            "version": 1,
            "kdf": "scrypt",
            "salt": base64.b64encode(salt).decode("ascii"),
            "verifier": verifier,
        }, indent=2), encoding="utf-8")
        try:
            config.chmod(0o600)
        except OSError:
            pass
        return password


def _authenticate(config: Path) -> str | None:
    if not config.exists():
        return _setup_password(config)
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
        salt = base64.b64decode(data["salt"], validate=True)
        expected = str(data["verifier"])
    except (OSError, ValueError, KeyError, TypeError):
        print("Configuração administrativa inválida. Não vou abrir o cofre.")
        return None
    for _ in range(3):
        password = getpass.getpass("Senha de administrador: ")
        actual = hmac.new(
            _derive(password, salt), b"Proton Voice Vault v1", hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(actual, expected):
            return password
        print("Senha incorreta.")
    print("Acesso bloqueado após 3 tentativas.")
    return None


def _record_sample(fernet, samples: Path, index: int) -> bool:
    recorder = shutil.which("termux-microphone-record")
    if not recorder:
        print("Não encontrei termux-microphone-record.")
        print("Instale o Termux:API e o pacote termux-api no Termux.")
        return False

    phrase = PHRASES[index]
    print(f"\nFrase {index + 1}/{len(PHRASES)}: {phrase}")
    input("Pressione Enter e fale a frase quando a gravação começar...")
    fd, raw_name = tempfile.mkstemp(prefix="proton-voice-", suffix=".m4a")
    os.close(fd)
    raw_path = Path(raw_name)
    try:
        raw_path.unlink(missing_ok=True)
        result = subprocess.run(
            [recorder, "-f", str(raw_path), "-l", "8"],
            check=False, capture_output=True, text=True, timeout=20,
        )
        if result.returncode != 0 or not raw_path.is_file() or raw_path.stat().st_size == 0:
            detail = (result.stderr or result.stdout).strip()
            print("Não consegui gravar. Confira a permissão do microfone e o Termux:API.")
            if detail:
                print(detail[:300])
            return False

        encrypted = fernet.encrypt(raw_path.read_bytes())
        target = samples / f"sample-{index + 1:02d}.m4a.fernet"
        target.write_bytes(encrypted)
        try:
            target.chmod(0o600)
        except OSError:
            pass
        print("Amostra criptografada e salva somente neste dispositivo.")
        return True
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Falha na gravação: {exc}")
        return False
    finally:
        raw_path.unlink(missing_ok=True)


def main() -> None:
    root, config, samples = _paths()
    _secure_dir(root)
    _secure_dir(samples)
    password = _authenticate(config)
    if password is None:
        return
    try:
        salt = base64.b64decode(json.loads(config.read_text(encoding="utf-8"))["salt"])
        fernet = _fernet(password, salt)
    except Exception as exc:
        print(f"Não consegui abrir o cofre: {exc}")
        return

    print("\n=== PROTON VOICE — ADMIN ===")
    print("Amostras são criptografadas e permanecem locais.")
    print("Este recurso ainda NÃO cria um modelo de voz nem envia arquivos ao servidor.")
    while True:
        print("\n1. Gravar frases de treinamento")
        print("2. Ver quantidade de amostras")
        print("3. Apagar todas as amostras")
        print("4. Sair")
        choice = input("Administrador > ").strip()
        if choice == "1":
            for i in range(len(PHRASES)):
                _record_sample(fernet, samples, i)
            print("\nEtapa de coleta encerrada.")
        elif choice == "2":
            count = len(list(samples.glob("*.fernet")))
            print(f"{count} amostra(s) criptografada(s) neste dispositivo.")
        elif choice == "3":
            confirm = input("Digite APAGAR para confirmar: ").strip()
            if confirm == "APAGAR":
                for item in samples.glob("*.fernet"):
                    item.unlink(missing_ok=True)
                print("Amostras apagadas.")
            else:
                print("Cancelado.")
        elif choice == "4":
            print("Menu administrativo fechado.")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
