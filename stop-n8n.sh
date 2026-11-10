#!/usr/bin/env bash
# Desliga o n8n que foi ligado pelo start-n8n.sh
PIDFILE=/tmp/n8n.pid
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  # Desliga o grupo inteiro (npx + o n8n que ele abriu)
  kill -- -"$(cat "$PIDFILE")" 2>/dev/null || kill "$(cat "$PIDFILE")"
  rm -f "$PIDFILE"
  sleep 2
  echo "🛑 n8n desligado."
else
  rm -f "$PIDFILE"
  echo "ℹ️  O n8n não estava rodando."
fi
