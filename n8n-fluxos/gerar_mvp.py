#!/usr/bin/env python3
"""Gera o fluxo MVP (só texto, agente na Groq, envio direto pela Evolution) a partir da base.

Uso:
  python3 n8n-fluxos/gerar_mvp.py n8n-fluxos/Template_SDR_EVO_v2_Vertice.json n8n-fluxos/SDR_Vertice_MVP_Groq_Texto.json

A base NÃO é alterada. O que o script faz, em ordem:
  1. Agente: troca o modelo por um modelo grátis da Groq (endpoint compatível com OpenAI).
  2. Envio: troca o nó de comunidade da Evolution por uma chamada HTTP (não precisa instalar nada).
  3. Entrada: ignora grupos/status, entende texto "com link/resposta" e usa o endereço certo do contato.
  4. Áudio, imagem e outros tipos: respondem "Por enquanto só consigo ler texto 🙂" (nós antigos ficam, soltos).
  5. RAG (base de conhecimento) e criação de tabelas: nós DESLIGADOS (não apagados).
  6. Proteção: mensagem enviada pelo próprio bot não conta como "humano assumiu a conversa".
  7. Credenciais: todos os nós apontam para credenciais com NOMES fixos (veja docs/PASSO-A-PASSO.md).
"""
import copy
import json
import sys

MODELO = "llama-3.3-70b-versatile"  # reserva: openai/gpt-oss-120b
AVISO = "Por enquanto só consigo ler texto 🙂"
EVOLUTION_URL = "http://127.0.0.1:8080"  # não use "localhost": o Node tenta IPv6 primeiro e o Docker só publica IPv4

CRED = {
    "groq": ("openAiApi", "sdrGroq00000001", "Groq SDR"),
    "redis": ("redis", "sdrRedis0000001", "Redis SDR"),
    "postgres": ("postgres", "sdrPostgres0001", "Postgres SDR"),
    "supabase": ("supabaseApi", "sdrSupabase0001", "Supabase SDR"),
    "evolution": ("httpHeaderAuth", "sdrEvolution0001", "Evolution API"),
}

EXTRA_PROMPT_MARCA = "# Ferramentas disponíveis agora (MVP)"
EXTRA_PROMPT = f"""

---

{EXTRA_PROMPT_MARCA}
- Neste momento NÃO existem as ferramentas `base_conhecimento` nem `add_lead_crm`. Nunca tente chamá-las.
- Responda sobre a empresa usando só as informações deste texto. Se não souber, diga que um especialista confirma depois.
- Se o lead for qualificado, convide para o próximo passo e envie o link; o registro no CRM será feito por uma pessoa.
- As únicas ferramentas que você pode usar são `update_ai_response` (lead quer falar com uma pessoa) e `update_fup` (lead não quer mais receber mensagens de acompanhamento).
"""


def cred(no, chave):
    tipo, cid, nome = CRED[chave]
    no["credentials"] = {tipo: {"id": cid, "name": nome}}


def main(entrada, saida):
    base = json.load(open(entrada, encoding="utf-8"))
    w = copy.deepcopy(base)
    nos = {n["name"]: n for n in w["nodes"]}
    avisos = []

    def pega(nome):
        if nome not in nos:
            avisos.append(f"nó '{nome}' não existe na base (pulei)")
        return nos.get(nome)

    # 0) Tira credenciais de outra conta
    for n in w["nodes"]:
        n.pop("credentials", None)

    # 1) Modelo do agente -> Groq (nó OpenAI com Base URL da Groq, que fica na credencial)
    n = pega("OpenAI Chat Model") or pega("Google Gemini Chat Model")
    antigo = n["name"]
    n["name"] = "Groq Chat Model"
    n["type"] = "@n8n/n8n-nodes-langchain.lmChatOpenAi"
    n["typeVersion"] = 1.2
    n["parameters"] = {"model": {"__rl": True, "mode": "id", "value": MODELO},
                       "options": {"temperature": 0.4, "maxRetries": 2}}
    n["notes"] = f"Groq grátis. Modelo: {MODELO}. Reserva: openai/gpt-oss-120b. A chave fica na credencial 'Groq SDR'."
    cred(n, "groq")

    # 2) Envio de texto: nó de comunidade -> HTTP Request direto na Evolution
    n = pega("Send Text Message")
    n["type"] = "n8n-nodes-base.httpRequest"
    n["typeVersion"] = 4.2
    n["parameters"] = {
        "method": "POST",
        "url": "={{ '" + EVOLUTION_URL + "/message/sendText/' + $('Set Data').first().json.instance_name }}",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ number: $('Set Data').first().json.message.jid, text: $json.message_split, delay: 1200 }) }}",
        "options": {"timeout": 30000},
    }
    n["retryOnFail"] = True
    n["maxTries"] = 3
    n["waitBetweenTries"] = 2000
    n["notes"] = f"POST {EVOLUTION_URL}/message/sendText/<instância>. Chave na credencial 'Evolution API' (cabeçalho apikey)."
    cred(n, "evolution")

    # 3) Set Data: texto com link/resposta + endereço certo do contato
    n = pega("Set Data")
    ass = n["parameters"]["assignments"]["assignments"]
    for a in ass:
        if a["name"] == "message.content":
            a["value"] = ("={{ $('Webhook').first().json.body.data.message.conversation "
                          "|| $('Webhook').first().json.body.data.message.extendedTextMessage?.text || '' }}")
    ass.append({
        "id": "9f1c1b0e-0000-4a00-9000-0000000000a1",
        "name": "message.jid",
        # Contatos novos do WhatsApp vêm como ...@lid; o número real fica em remoteJidAlt
        "value": "={{ $('Webhook').first().json.body.data.key.remoteJidAlt || $('Webhook').first().json.body.data.key.remoteJid }}",
        "type": "string",
    })

    # 3b) Filtro logo depois do Webhook: só conversa 1 a 1 com mensagem
    filtro = {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                "conditions": [
                    {"id": "f1000000-0000-4000-8000-000000000001",
                     "leftValue": "={{ $json.body.data?.key?.remoteJid ?? '' }}", "rightValue": "",
                     "operator": {"type": "string", "operation": "notEmpty", "singleValue": True}},
                    {"id": "f1000000-0000-4000-8000-000000000002",
                     "leftValue": "={{ /@(g\\.us|broadcast|newsletter)$/.test($json.body.data?.key?.remoteJid ?? '') }}",
                     "rightValue": "",
                     "operator": {"type": "boolean", "operation": "false", "singleValue": True}},
                ],
                "combinator": "and",
            },
            "looseTypeValidation": True,
            "options": {},
        },
        "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [-60, 520],
        "id": "f1000000-0000-4000-8000-0000000000f1",
        "name": "So Conversa 1 a 1",
        "notes": "Ignora grupos, status e eventos que não são mensagem.",
    }
    w["nodes"].append(filtro)

    # 4) Content Type: texto (inclui link/resposta) segue; áudio, imagem e o resto -> aviso
    n = pega("Content Type")
    regras = n["parameters"]["rules"]["values"]
    for r in regras:
        if r.get("outputKey") == "Texto":
            r["conditions"]["conditions"] = [{
                "id": "17f3a3bf-27a4-4f03-aa45-9f6851bb9194",
                "leftValue": "={{ ['conversation','extendedTextMessage'].includes($('Set Data').first().json.message.content_type) }}",
                "rightValue": "",
                "operator": {"type": "boolean", "operation": "true", "singleValue": True},
            }]
    n["parameters"]["options"] = {"fallbackOutput": "extra", "renameFallbackOutput": "Outros (figurinha, vídeo, documento)"}
    aviso = {
        "parameters": {"assignments": {"assignments": [
            {"id": "a0000000-0000-4000-8000-000000000001", "name": "output", "value": AVISO, "type": "string"}]},
            "options": {}},
        "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [1184, 1392],
        "id": "a0000000-0000-4000-8000-0000000000a1", "name": "Aviso So Texto",
        "notes": "Áudio/imagem/outros caem aqui e recebem o aviso. Para religar áudio ou imagem, veja a nota amarela.",
    }
    w["nodes"].append(aviso)
    w["nodes"].append({
        "parameters": {"content": "## ÁUDIO e IMAGEM DESLIGADOS (MVP só texto)\nOs nós de áudio e imagem continuam aqui, soltos.\nPara religar: ligue a saída **Áudio** do 'Content Type' em 'Less Than 2 Minutes…' e a saída **Imagem** em 'Set Base' (e troque as credenciais dos nós de IA).",
                       "height": 220, "width": 900, "color": 3},
        "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [800, 1840],
        "id": "a0000000-0000-4000-8000-0000000000a2", "name": "Nota Audio Imagem Desligados"})

    # 5) RAG e criação de tabelas: desligados (não apagados)
    for nome in ("Supabase Vector Store", "Embeddings OpenAI", "Embeddings Google Gemini",
                 "Create Users Table", "Create Documents Table and Match Function"):
        if nome in nos:
            nos[nome]["disabled"] = True
    if "Sticky Note" in nos:
        nos["Sticky Note"]["parameters"]["content"] = "## RAG (DESLIGADO no MVP)\nPara ligar: ative os dois nós daqui e crie as tabelas de documentos."
    if "Sticky Note15" in nos:
        nos["Sticky Note15"]["parameters"]["content"] = ("## Tabelas do Supabase (nós desligados)\n"
                                                         "Crie a tabela de usuários colando docs/supabase-usuarios.sql no SQL Editor do Supabase.")

    # 6) add_lead_crm continua desligado
    if "add_lead_crm" in nos:
        nos["add_lead_crm"]["disabled"] = True

    # 7) Prompt: avisa o agente que a base de conhecimento e o CRM estão desligados
    ag = pega("Agente SDR")
    msg = ag["parameters"]["options"]["systemMessage"]
    if EXTRA_PROMPT_MARCA not in msg:
        ag["parameters"]["options"]["systemMessage"] = msg.rstrip("\n") + EXTRA_PROMPT

    # 8) Credenciais por nome
    for n in w["nodes"]:
        t = n["type"]
        if t == "n8n-nodes-base.redis":
            cred(n, "redis")
        elif "postgres" in t.lower() and "tool" not in t.lower():
            cred(n, "postgres")
        elif t in ("n8n-nodes-base.supabase", "n8n-nodes-base.supabaseTool",
                   "@n8n/n8n-nodes-langchain.vectorStoreSupabase"):
            cred(n, "supabase")

    # 9) Nós novos de proteção contra "eco" do próprio bot
    marca = {
        "parameters": {"operation": "set",
                       "key": "={{ $('Set Data').first().json.bot_name }}_{{ $('Set Data').first().json.message.phone }}_botsent",
                       "value": "1", "keyType": "string", "expire": True, "ttl": 30},
        "type": "n8n-nodes-base.redis", "typeVersion": 1, "position": [5800, 848],
        "id": "b0000000-0000-4000-8000-0000000000b1", "name": "Marca Bot Enviando",
        "notes": "Anota por 30s que o bot está falando com este contato.",
    }
    cred(marca, "redis")
    le_marca = {
        "parameters": {"operation": "get", "propertyName": "botSent",
                       "key": "={{ $('Set Data').first().json.bot_name }}_{{ $('Set Data').first().json.message.phone }}_botsent",
                       "options": {}},
        "type": "n8n-nodes-base.redis", "typeVersion": 1, "position": [1312, 336],
        "id": "b0000000-0000-4000-8000-0000000000b2", "name": "Le Marca Bot", "alwaysOutputData": True,
    }
    cred(le_marca, "redis")
    foi_bot = {
        "parameters": {"conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
            "conditions": [{"id": "b0000000-0000-4000-8000-0000000000c1",
                            "leftValue": "={{ !!$json.botSent }}", "rightValue": "",
                            "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
            "combinator": "and"}, "looseTypeValidation": True, "options": {}},
        "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [1408, 336],
        "id": "b0000000-0000-4000-8000-0000000000b3", "name": "Foi o Proprio Bot",
        "notes": "Se o bot acabou de responder, a mensagem 'minha' é o eco dele: ignora (não é humano assumindo).",
    }
    w["nodes"] += [marca, le_marca, foi_bot]

    # ---- Ligações ----
    con = w["connections"]

    def renomeia(velho, novo):
        if velho in con:
            con[novo] = con.pop(velho)
        for tipos in con.values():
            for saidas in tipos.values():
                for s in saidas:
                    for x in s or []:
                        if x["node"] == velho:
                            x["node"] = novo

    renomeia(antigo, "Groq Chat Model")

    con["Webhook"] = {"main": [[{"node": "So Conversa 1 a 1", "type": "main", "index": 0}]]}
    con["So Conversa 1 a 1"] = {"main": [[{"node": "Redis - Get Buf", "type": "main", "index": 0}], []]}

    con["Content Type"] = {"main": [
        [{"node": "Aviso So Texto", "type": "main", "index": 0}],
        [{"node": "Set Message Array", "type": "main", "index": 0}],
        [{"node": "Aviso So Texto", "type": "main", "index": 0}],
        [{"node": "Aviso So Texto", "type": "main", "index": 0}],
    ]}
    con["Aviso So Texto"] = {"main": [[{"node": "Split Messages", "type": "main", "index": 0}]]}

    con["Loop Over Items"]["main"][1] = [{"node": "Marca Bot Enviando", "type": "main", "index": 0}]
    con["Marca Bot Enviando"] = {"main": [[{"node": "Send Text Message", "type": "main", "index": 0}]]}

    con["Is From Me?"]["main"][0] = [{"node": "Le Marca Bot", "type": "main", "index": 0}]
    con["Le Marca Bot"] = {"main": [[{"node": "Foi o Proprio Bot", "type": "main", "index": 0}]]}
    con["Foi o Proprio Bot"] = {"main": [[], [{"node": "Set Timeout", "type": "main", "index": 0}]]}

    w["name"] = "SDR Vertice MVP (Groq, so texto)"
    for k in ("id", "versionId", "meta", "tags", "pinData"):
        w.pop(k, None)
    w["active"] = False

    nomes = {n["name"] for n in w["nodes"]}
    assert len(nomes) == len(w["nodes"]), "nome de nó repetido"
    for o, t in con.items():
        assert o in nomes, o
        for s in t.values():
            for lst in s:
                for x in lst or []:
                    assert x["node"] in nomes, x

    json.dump(w, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"ok: {len(w['nodes'])} nós -> {saida}")
    for a in avisos:
        print("aviso:", a)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
