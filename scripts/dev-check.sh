#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/native"
cargo test
cargo build --release
if command -v cmake >/dev/null 2>&1; then
  cmake -S "$ROOT/cpp" -B "$ROOT/cpp/build"
  cmake --build "$ROOT/cpp/build"
fi
