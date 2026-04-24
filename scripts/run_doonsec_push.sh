#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/sec-daily-dingtalk-bot}"
ENV_FILE="${ENV_FILE:-$APP_DIR/.env}"
SLOT="${1:-auto}"
if [[ $# -gt 0 ]]; then
  shift
fi

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

cd "$APP_DIR"
mkdir -p logs

export STATE_FILE="${STATE_FILE:-$APP_DIR/data/sent_state.json}"
export TRIGGER_NAME="${TRIGGER_NAME:-cron}"

flock -n "$APP_DIR/.doonsec_push.lock" \
  "$APP_DIR/.venv/bin/python" -m doonsec_push --slot "$SLOT" "$@" \
  >> "$APP_DIR/logs/doonsec_push.log" 2>&1
