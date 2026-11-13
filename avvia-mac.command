#!/bin/bash
# Avvia la Regia sul Mac: server locale + pagina nel browser. Doppio clic (la prima volta: tasto destro → Apri).
cd "$(dirname "$0")" || exit 1
PORTA="${1:-8765}"
if lsof -iTCP:"$PORTA" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Porta $PORTA già in uso: apro la pagina e basta."
  open "http://127.0.0.1:$PORTA"
  exit 0
fi
( sleep 1.5; open "http://127.0.0.1:$PORTA" ) &
exec python3 plancia/server.py "$PORTA"
