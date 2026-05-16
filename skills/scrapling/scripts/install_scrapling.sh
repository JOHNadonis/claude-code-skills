#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"
PY_BIN="${PY_BIN:-python3}"

pip_install() {
  if "$PY_BIN" -m pip install "$@"; then
    return 0
  fi
  "$PY_BIN" -m pip install --break-system-packages "$@"
}

install_browsers_if_needed() {
  if [[ "$MODE" == "fetchers" || "$MODE" == "all" ]]; then
    if command -v scrapling >/dev/null 2>&1; then
      scrapling install
      return
    fi

    if "$PY_BIN" -m scrapling install 2>/dev/null; then
      return
    fi

    echo "[WARN] 无法自动执行 'scrapling install'（浏览器依赖）。"
    echo "[WARN] 请手动执行: scrapling install"
  fi
}

case "$MODE" in
  base)
    pip_install scrapling
    ;;
  fetchers)
    pip_install "scrapling[fetchers]"
    ;;
  shell)
    pip_install "scrapling[shell]"
    ;;
  ai)
    pip_install "scrapling[ai]"
    ;;
  all)
    pip_install "scrapling[all]"
    ;;
  *)
    echo "Usage: $0 [base|fetchers|shell|ai|all]" >&2
    exit 1
    ;;
esac

install_browsers_if_needed

echo "[OK] Scrapling 安装流程完成，模式: $MODE"
