#!/usr/bin/env bash
# Liga Evolution API + Redis + Postgres (Docker).  Uso: ./start-evolution.sh
cd "$(dirname "$0")"

if ! docker info >/dev/null 2>&1; then
  echo "❌ O Docker não está respondendo. Reinicie o Codespace e tente de novo."
  exit 1
fi

# 1) Cria o .env com senhas aleatórias na primeira vez (o .env NÃO vai pro GitHub)
if [ ! -f .env ]; then
  echo "🔐 Criando o arquivo .env com senhas aleatórias..."
  cat > .env <<ENV
EVOLUTION_SERVER_URL=https://${CODESPACE_NAME}-8080.app.github.dev
EVOLUTION_API_KEY=$(openssl rand -hex 24)
REDIS_PASSWORD=$(openssl rand -hex 16)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
ENV
  chmod 600 .env
fi

# 2) Sobe tudo em segundo plano
echo "⏳ Ligando Evolution, Redis e Postgres (1ª vez baixa ~1 GB, pode levar alguns minutos)..."
docker compose up -d || { echo "❌ Falhou ao subir. Veja: docker compose logs"; exit 1; }

# 3) Espera a Evolution responder
for i in $(seq 1 60); do
  curl -s -o /dev/null --max-time 3 http://localhost:8080/ && break
  sleep 5
done
if ! curl -s -o /dev/null --max-time 3 http://localhost:8080/; then
  echo "❌ A Evolution não respondeu. Últimas linhas do log:"
  docker compose logs --tail 30 evolution
  exit 1
fi

source .env
echo ""
echo "✅ Evolution ligada!"
echo "🔗 Painel:      https://${CODESPACE_NAME}-8080.app.github.dev/manager"
echo "🔑 Chave (API Key global) para entrar no painel:"
echo "   $EVOLUTION_API_KEY"
echo "   (ela fica guardada no arquivo .env — não compartilhe)"
echo ""
echo "Webhook para o n8n:  http://host.docker.internal:5678/webhook/bia_message_received"
