#!/usr/bin/env bash
# Liga o n8n em segundo plano dentro do Codespace.
# Uso:  ./start-n8n.sh      (para desligar: ./stop-n8n.sh)

PORTA=5678
LOG=/tmp/n8n.log
PIDFILE=/tmp/n8n.pid
# Versão fixa do n8n, instalada uma única vez em /workspaces (não baixa versão nova sozinho).
N8N_VERSAO=2.47.7
N8N_APP=/workspaces/.n8n-app
N8N_BIN="$N8N_APP/node_modules/.bin/n8n"
LINK="https://${CODESPACE_NAME}-${PORTA}.app.github.dev/"

export WEBHOOK_URL="$LINK"
export N8N_PROXY_HOPS=1
# Dados do n8n (fluxos, contas, credenciais) ficam FORA do repositório
export N8N_USER_FOLDER=/workspaces/.n8n-dados
mkdir -p "$N8N_USER_FOLDER"

# Função: o n8n está respondendo na porta?
n8n_respondendo() {
  curl -s -o /dev/null --max-time 3 "http://localhost:${PORTA}/healthz"
}

# 1) Já está rodando? Então não liga outro.
if n8n_respondendo || { [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }; then
  echo "ℹ️  O n8n já está rodando. Não vou ligar outro."
else
  echo "⏳ Ligando o n8n em segundo plano (1ª vez pode levar 5-10 minutos para baixar)..."
  echo "   Log em: $LOG"
  # setsid: roda num "grupo" próprio, para o stop-n8n.sh desligar tudo de uma vez
  # Se o n8n ainda não estiver instalado, instala (1ª vez, uns 5-10 min) e depois liga.
  setsid nohup sh -c "[ -x '$N8N_BIN' ] || npm install --prefix '$N8N_APP' n8n@$N8N_VERSAO --no-audit --no-fund; exec '$N8N_BIN' start" > "$LOG" 2>&1 < /dev/null &
  echo $! > "$PIDFILE"

  # 2) Espera até 10 minutos o n8n responder
  for i in $(seq 1 120); do
    if n8n_respondendo; then break; fi
    sleep 5
  done

  if ! n8n_respondendo; then
    echo "❌ O n8n não respondeu a tempo. Últimas linhas do log:"
    tail -n 20 "$LOG"
    exit 1
  fi
fi

# 3) Deixa a porta pública (precisa do n8n já ligado)
if gh codespace ports visibility "${PORTA}:public" -c "$CODESPACE_NAME" >/dev/null 2>&1; then
  echo "✅ Porta $PORTA está PÚBLICA."
else
  echo "ℹ️  A porta 5678 ficou como Privada (tudo bem: só você acessa, e a Evolution fala com o n8n por dentro)."
  echo "   Se a 5678 não aparecer na aba PORTAS do VS Code, clique em 'Adicionar porta' e digite 5678."
fi

echo ""
echo "🔗 $LINK"
echo "n8n ligado, abra o link"
