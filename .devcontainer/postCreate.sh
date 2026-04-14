#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[postCreate] %s\n' "$1"
}

warn() {
  printf '[postCreate][warn] %s\n' "$1" >&2
}

run_pkg_cmd() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    warn "sudo is not available; skipping command: $*"
    return 1
  fi
}

log "Installing Python dependencies"
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt pytest

if command -v apt-get >/dev/null 2>&1; then
  log "Detected apt-based image; installing GUI runtime packages"
  run_pkg_cmd apt-get update -qq || warn "apt update failed"
  run_pkg_cmd apt-get install -y -qq --no-install-recommends python3-tk chromium || \
    run_pkg_cmd apt-get install -y -qq --no-install-recommends python3-tk chromium-browser || \
    warn "Could not install chromium package; GUI report PDF support may be limited"
  run_pkg_cmd apt-get clean || true
elif command -v apk >/dev/null 2>&1; then
  log "Detected apk-based image; installing Tk runtime"
  run_pkg_cmd apk add --no-cache tcl tk || warn "Could not install tcl/tk on apk image"
else
  warn "No supported package manager found; skipping OS package install"
fi

log "Post-create setup complete"
