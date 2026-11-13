# Guia passo a passo: agente SDR de WhatsApp (MVP grátis, só texto)

Este guia liga um agente que conversa no WhatsApp do **chip reserva**, responde só texto e usa IA grátis da Groq.

## Como as peças se encaixam

```
Cliente (WhatsApp)  ->  Evolution API  ->  n8n (fluxo SDR)  ->  Groq (IA grátis)
                         (no Docker)          |                      |
                                              +-> Supabase (lista de leads, nuvem grátis)
                                              +-> Redis / Postgres (memória, no Docker)
n8n responde  ->  Evolution API  ->  WhatsApp do cliente
```

- **Evolution API**: "ponte" não oficial entre o WhatsApp e o n8n. É ela que lê o QR Code.
- **n8n**: onde mora o fluxo (o "cérebro" do SDR).
- **Groq**: dá a IA de graça (modelo `llama-3.3-70b-versatile`).
- **Supabase**: guarda a lista de leads (tabela `users`).

> ⚠️ **Aviso importante:** a Evolution API **não é oficial**. Use **só o chip reserva**, nunca o número principal da empresa. Não dispare mensagens em massa: o WhatsApp pode banir o número.

---

## Parte 1 — Ligar tudo (a cada vez que abrir o Codespace)

No terminal do Codespace:

1. `./start-evolution.sh` (liga Evolution, Redis e Postgres). Na 1ª vez demora uns minutos.
2. `./start-n8n.sh` (liga o n8n).

Para desligar e **economizar as horas grátis**: `./stop-n8n.sh` e `./stop-evolution.sh`, e depois pare o Codespace em https://github.com/codespaces (`...` → **Stop codespace**).

---

## Parte 2 — Abrir as telas (aba PORTAS)

Você precisa abrir duas telas: o **n8n** (porta 5678) e o **painel da Evolution** (porta 8080).

1. Abra o Codespace pelo navegador: https://github.com/codespaces → clique no nome **potential fishstick**.
2. Na parte de baixo da tela do VS Code, clique na aba **PORTAS** (fica ao lado de TERMINAL). Se o painel de baixo estiver escondido, aperte `Ctrl + J`.
3. Procure as linhas **5678** e **8080**.
   - Se faltar alguma, clique no botão **Adicionar porta** (ou "Forward a Port"), digite o número e aperte Enter.
4. Para abrir uma tela: passe o mouse na coluna **Endereço encaminhado** da linha e clique no ícone de **globo 🌐** ("Abrir no navegador").
5. Se o GitHub perguntar "Continue" / pedir login, clique em **Continue** (é o seu próprio Codespace).

> As duas portas podem ficar **Privadas**. Não é preciso deixá-las públicas, porque a Evolution fala com o n8n por dentro do Codespace.

---

## Parte 3 — Conectar o chip reserva (QR Code)

A instância **`vertice`** já foi criada e já está com o webhook apontando para o n8n. Falta só ler o QR Code.

**Onde está a chave da Evolution** (você vai precisar para entrar no painel):
1. No VS Code, na barra da esquerda, clique no ícone de **Explorador** (dois papéis).
2. Clique no arquivo **`.env`** (se não aparecer, é porque o `start-evolution.sh` ainda não rodou).
3. A linha `EVOLUTION_API_KEY=...` é a chave. Selecione só o valor (depois do `=`) e copie. **Nunca cole essa chave no chat nem no GitHub.**

**Conectar:**
1. Abra o painel da Evolution (Parte 2, linha **8080**) e acrescente `/manager` no final do endereço, se ainda não estiver.
2. Na tela de login, preencha:
   - **Server URL**: o endereço que aparece na barra do navegador (sem o `/manager`).
   - **API Key Global**: a chave que você copiou do `.env`.
   - Clique em **Login**.
3. Você verá a instância **vertice** com o estado "connecting". Clique nela.
4. Clique no botão **Connect** / **Conectar** para mostrar o **QR Code**.
5. No celular do **chip reserva**:
   1. Abra o **WhatsApp**.
   2. Toque nos **três pontinhos** (Android) ou em **Configurações** (iPhone).
   3. Toque em **Aparelhos conectados**.
   4. Toque em **Conectar um aparelho**.
   5. Aponte a câmera para o QR Code da tela do computador.
6. Espere uns segundos: o estado da instância muda para **open** / "Connected". Pronto!

> O QR Code expira em cerca de 1 minuto. Se expirar, clique em **Connect** de novo para gerar outro.

### Conferir o webhook (opcional)
No painel, entre na instância → aba **Webhook** (ou "Events"):
- URL: `http://host.docker.internal:5678/webhook/bia_message_received`
- Evento ligado: **MESSAGES_UPSERT** (só ele)
- "Webhook by Events" e "Webhook Base64": **desligados**.

### Se um dia precisar recriar a instância pelo painel
Botão **Instance +** → nome `vertice`, integração **WHATSAPP-BAILEYS** → depois configure o webhook como acima e, em **Settings**, ligue **Ignore Groups**.

---

## Parte 4 — Criar o projeto grátis no Supabase

1. Acesse https://supabase.com e clique em **Start your project**. Entre com a sua conta do GitHub.
2. Clique em **New project**:
   - **Name**: `sdr-vertice`.
   - **Database Password**: clique em *Generate a password* e **guarde num lugar seguro** (você não vai usar no n8n, mas não perca).
   - **Region**: *South America (São Paulo)*.
   - Plano **Free**. Clique em **Create new project** e espere 1 a 2 minutos.
3. **Criar a tabela de leads:**
   1. Menu da esquerda → **SQL Editor** → **New query**.
   2. No VS Code, abra o arquivo **`docs/supabase-usuarios.sql`**, selecione tudo (`Ctrl + A`) e copie (`Ctrl + C`).
   3. Cole no Supabase (`Ctrl + V`) e clique em **Run**. Deve aparecer "Success. No rows returned".
   4. Confira: menu **Table Editor** → deve existir a tabela **users**.
4. **Pegar os dados de conexão** (você vai colar no n8n, nunca no chat):
   1. Menu da esquerda → engrenagem **Project Settings** → **API** (ou **API Keys**).
   2. **Project URL**: algo como `https://xxxxxxxx.supabase.co` (sem `/rest/v1`).
   3. Chave **`service_role`** (secreta). Ela fica na aba **Legacy API keys** ("chaves legadas"). Clique em **Reveal** e copie.
   - ⚠️ Use a **service_role**, e não a `anon`/`publishable`. Ela nunca pode ir para o GitHub.

---

## Parte 5 — Pegar a chave da Groq (IA grátis)

1. Acesse https://console.groq.com e crie a conta (pode entrar com Google ou GitHub).
2. Menu **API Keys** → **Create API Key** → dê o nome `sdr` → **Submit**.
3. **Copie a chave agora** (ela só aparece uma vez). Ela começa com `gsk_`.

Limites do plano grátis: poucas dezenas de mensagens por minuto e um teto de tokens por minuto/dia. Para uma demonstração, sobra. Se aparecer erro 429 ("rate limit"), espere 1 minuto. Para ver os seus limites exatos: console.groq.com → **Settings** → **Limits**.

---

## Parte 6 — Credenciais no n8n

Cinco credenciais, todas com **nomes fixos** (o fluxo procura por esses nomes):

| Nome no n8n | Para quê | Situação | De onde vem |
|---|---|---|---|
| **Redis SDR** | buffer de mensagens | ✅ já criada | gerada no `.env` |
| **Postgres SDR** | memória do agente | ✅ já criada | gerada no `.env` |
| **Evolution API** | enviar respostas | ✅ já criada | `EVOLUTION_API_KEY` do `.env` |
| **Groq SDR** | IA do agente | ✏️ você cola a chave | Parte 5 (`gsk_...`) |
| **Supabase SDR** | lista de leads | ✏️ você cola URL e chave | Parte 4 |

**Para preencher as duas que faltam:**
1. Abra o n8n (Parte 2, linha **5678**) e faça login (se esqueceu a senha, peça para o Claude resetar).
2. Menu da esquerda → **Overview** → aba **Credentials** (ou ícone de chave 🔑).
3. Clique em **Groq SDR** → no campo **API Key** apague o texto de exemplo e cole a chave `gsk_...` → **Save**.
   - Não mexa no campo **Base URL** (`https://api.groq.com/openai/v1`).
4. Clique em **Supabase SDR** → em **Host** cole a *Project URL*; em **Service Role Secret** cole a chave `service_role` → **Save**.
5. Se aparecer "Couldn't connect" no teste das credenciais da Groq ou do Supabase, confira se não ficou espaço sobrando no começo ou no fim.

### Ativar o fluxo
1. Menu da esquerda → **Workflows** → abra **SDR Vertice MVP (Groq, so texto)**.
2. No canto superior direito, clique em **Publish** (em versões antigas do n8n: o botão **Inactive** → **Active**).
3. Confirme. O fluxo agora recebe mensagens.

> O fluxo precisa estar **publicado**; fluxo salvo mas não publicado não recebe nada.

---

## Parte 7 — Teste de verdade, de ponta a ponta

1. Confira que tudo está ligado: Evolution (`vertice` = open), n8n com o fluxo **publicado**, `users` criada no Supabase.
2. Use **outro celular** (o seu pessoal, por exemplo) e mande **"Oi, quero saber como a Vértice funciona"** para o número do **chip reserva**.
   - ❌ Não teste mandando mensagem para o próprio chip reserva a partir dele mesmo.
3. Aguarde de **10 a 20 segundos**. (O fluxo espera 8 segundos para juntar mensagens seguidas.)
4. A Bia deve responder, em pedacinhos curtos.
5. Testes extras:
   - Mande um **áudio** → deve vir: *"Por enquanto só consigo ler texto 🙂"*.
   - Mande uma **foto** → mesma resposta.
   - Escreva **"quero falar com um humano"** → a Bia avisa e **para de responder** esse contato (no Supabase, `users.ai_response` vira `false`).
   - Mande 3 mensagens seguidas, rápido → deve vir **uma** resposta só.

### Para ver o que aconteceu dentro do n8n
Abra o fluxo → aba **Executions** (no topo). Cada mensagem recebida é uma linha: verde = deu certo, vermelha = erro (clique para ver em qual nó parou).

---

## Parte 8 — Se o agente não responder

Siga na ordem, parando quando achar:

1. **A Evolution está conectada?** Painel → instância **vertice** deve estar **open**. Se estiver "close"/"connecting", leia o QR de novo (Parte 3).
2. **O n8n recebeu a mensagem?** Abra o fluxo → **Executions**.
   - **Nada aparece:** o fluxo não está **publicado**, ou o webhook da Evolution está errado (Parte 3 → *Conferir o webhook*). Teste: no terminal, `docker compose logs --tail 30 evolution`.
   - **Aparece, mas vermelho:** clique na execução e veja o nó com erro:
     - **Redis / Postgres**: confira se `./start-evolution.sh` está rodando (`docker compose ps`).
     - **Supabase** (`Get User`, `Create User`): URL ou `service_role` errada, ou a tabela `users` não foi criada.
     - **Groq Chat Model**: chave errada (401) ou limite estourado (429 → espere 1 minuto).
     - **Send Text Message**: chave da Evolution errada (401) ou instância desconectada.
   - **Aparece, verde, mas sem resposta no WhatsApp:** veja se `users.ai_response` ficou `false` no Supabase (a IA foi desligada para esse contato) ou se existe bloqueio de 24h por "humano assumiu". Para liberar, no Supabase mude `ai_response` para `true`, e no terminal rode `docker compose exec redis redis-cli -a "$REDIS_PASSWORD" --no-auth-warning keys '*timeout*'` (e apague a chave que aparecer).
3. **Só recebeu o aviso "só consigo ler texto"?** A mensagem não era texto simples (era áudio, figurinha, foto etc.).
4. **O modelo da Groq deu erro de ferramenta ("tool call validation")?** Troque o modelo no nó **Groq Chat Model** para `openai/gpt-oss-120b`.
5. **Ainda nada?** Rode `./start-n8n.sh` e `./start-evolution.sh` de novo e olhe `tail -n 30 /tmp/n8n.log`.

---

## O que ficou desligado de propósito (dá para religar depois)

| Parte | Como religar |
|---|---|
| Áudio (transcrição) | Ligue a saída **Áudio** do nó *Content Type* em *Less Than 2 Minutes…* e troque a credencial dos nós de IA. |
| Imagem | Ligue a saída **Imagem** do *Content Type* em *Set Base*. |
| Base de conhecimento (RAG) | Ative *Supabase Vector Store* e *Embeddings*, crie as tabelas de documentos e atualize o prompt. |
| CRM (`add_lead_crm`) | O sub-fluxo **não está no arquivo**. Decida o destino (planilha, HubSpot, Pipedrive...), crie o sub-fluxo e ative a ferramenta. |

## Segurança, em uma linha
Chaves ficam só em: `.env` (fora do GitHub), credenciais do n8n e Codespaces Secrets. Nunca no código, nunca no chat.
