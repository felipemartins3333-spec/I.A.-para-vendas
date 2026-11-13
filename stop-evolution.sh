#!/usr/bin/env bash
# Desliga Evolution, Redis e Postgres (os dados e a conexão do WhatsApp ficam salvos)
cd "$(dirname "$0")"
docker compose stop && echo "🛑 Evolution, Redis e Postgres desligados."
