"""Fetch the latest published Proton checkpoint without requiring PyTorch."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT = ROOT / "checkpoints" / "proton-evolved.pt"
VERSION_FILE = ROOT / "checkpoints" / ".proton-model-version"
RELEASE_API = "https://api.github.com/repos/brawlstarsarthurgg415-byte/Proton-AI/releases/tags/proton-model-latest"


def update_model(timeout: int = 8) -> str:
    """Download a newly published champion; preserve the current model on failure."""
    request = urllib.request.Request(
        RELEASE_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Proton-AI-model-updater"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            release = json.loads(response.read().decode("utf-8"))
        asset = next((item for item in release.get("assets", [])
                      if item.get("name") == "proton-evolved.pt"), None)
        if not asset:
            return "Nenhum modelo publicado ainda."
        version = f"{asset.get('id')}:{asset.get('updated_at')}"
        try:
            current_version = VERSION_FILE.read_text(encoding="utf-8").strip()
        except OSError:
            current_version = ""
        if CHECKPOINT.is_file() and version == current_version:
            return "Modelo já está atualizado."

        download_url = asset.get("browser_download_url")
        if not download_url:
            return "Publicação encontrada, mas sem link de download."
        CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
        temporary = CHECKPOINT.with_suffix(".download")
        download_request = urllib.request.Request(
            download_url, headers={"User-Agent": "Proton-AI-model-updater"}
        )
        try:
            with urllib.request.urlopen(download_request, timeout=max(timeout, 30)) as response:
                payload = response.read()
            if len(payload) < 1024:
                return "Download incompleto; mantive o modelo anterior."
            temporary.write_bytes(payload)
            temporary.replace(CHECKPOINT)
            VERSION_FILE.write_text(version, encoding="utf-8")
            return "Novo modelo baixado automaticamente."
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
    except (OSError, ValueError, KeyError, urllib.error.URLError) as exc:
        return f"Não foi possível verificar atualizações ({exc.__class__.__name__}); mantendo o modelo atual."
