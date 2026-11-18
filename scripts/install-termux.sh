#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

if ! command -v pkg >/dev/null 2>&1; then
  echo "Este instalador foi feito para Termux. No Linux, instale Rust e execute cargo build --release em native/." >&2
  exit 1
fi

echo "== Proton-AI: preparando compiladores =="
pkg update -y
pkg install -y git rust clang cmake

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/native"
cargo build --release
install -Dm755 target/release/proton "$PREFIX/bin/proton"

echo
echo "Proton instalado! Comandos iniciais:"
echo "  proton help"
echo "  proton status"
echo "  proton study --hours 15"
