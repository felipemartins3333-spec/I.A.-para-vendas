#!/usr/bin/env bash
# Liga o n8n dentro do Codespace e deixa ele acessível pelo navegador.
# Uso:  ./start-n8n.sh

PORTA=5678

if [ -z "$CODESPACE_NAME" ]; then
  echo "⚠️  Não parece que estamos num Codespace (CODESPACE_NAME vazio)."
  echo "    O n8n vai ligar, mas só em http://localhost:$PORTA"
  export WEBHOOK_URL="http://localhost:$PORTA/"
else
  # Endereço público que o GitHub dá para a porta 5678 deste Codespace
  export WEBHOOK_URL="https://${CODESPACE_NAME}-${PORTA}.app.github.dev/"
fi

# Avisa o n8n que existe 1 "intermediário" (o proxy do GitHub) na frente dele
export N8N_PROXY_HOPS=1
export N8N_PORT=$PORTA

echo "🔗 Endereço do n8n: $WEBHOOK_URL"

# Tenta deixar a porta pública. A porta só existe depois que o n8n liga,
# então esperamos ele subir e tentamos em segundo plano.
if [ -n "$CODESPACE_NAME" ] && command -v gh >/dev/null 2>&1; then
  (
    for i in $(seq 1 60); do
      sleep 5
      if gh codespace ports visibility "${PORTA}:public" -c "$CODESPACE_NAME" >/dev/null 2>&1; then
        echo "✅ Porta $PORTA agora está PÚBLICA."
        exit 0
      fi
    done
    echo "⚠️  Não consegui deixar a porta $PORTA pública pelo comando."
    echo "    Faça manualmente: aba PORTAS > clique direito na 5678 > Visibilidade da porta > Público."
  ) &
fi

echo "⏳ Ligando o n8n (a primeira vez demora alguns minutos para baixar)..."
exec npx --yes n8n
