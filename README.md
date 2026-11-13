# I.A. para vendas

Ambiente para demonstrar automações de vendas para clientes B2B: um **agente SDR de WhatsApp** feito com **n8n**, **Evolution API** (WhatsApp não oficial) e **IA grátis da Groq**.

👉 **Comece por aqui:** [`docs/PASSO-A-PASSO.md`](docs/PASSO-A-PASSO.md) (ligar tudo, conectar o chip pelo QR Code, Supabase, Groq, teste e o que fazer se der erro).

## 📁 Onde fica cada coisa

| Caminho | O que é |
|---|---|
| `n8n-fluxos/SDR_Vertice_MVP_Groq_Texto.json` | **O fluxo do MVP** (só texto, agente na Groq). É este que você importa/usa. |
| `n8n-fluxos/Template_SDR_EVO_v2_Vertice.json` | Base com o prompt da Vértice (não alterar). |
| `n8n-fluxos/Template_SDR_EVO_v2__1_.json` | Template original do Victor (não alterar). |
| `n8n-fluxos/SDR_Clinica_Aurora_Gemini_Groq.json` | Cópia de teste com uma clínica fictícia. |
| `n8n-fluxos/gerar_mvp.py` | Gera o fluxo do MVP a partir de uma base. |
| `n8n-fluxos/validar_fluxo.py` | Confere se um fluxo está com a estrutura certa. |
| `docs/` | Guias e o SQL da tabela do Supabase. |
| `bots/` | Bots em Python (ainda vazio). |
| `docker-compose.yml` | Evolution API + Redis + Postgres. |
| `start-evolution.sh` / `stop-evolution.sh` | Liga / desliga a Evolution. |
| `start-n8n.sh` / `stop-n8n.sh` | Liga / desliga o n8n. |

## ▶️ Ligar e desligar

```bash
./start-evolution.sh   # Evolution API, Redis e Postgres (Docker)
./start-n8n.sh         # n8n

./stop-n8n.sh          # desligar
./stop-evolution.sh
```

Telas: n8n na porta **5678**, painel da Evolution na porta **8080** (aba **PORTAS** do VS Code, ícone de globo 🌐).
Registro do n8n: `tail -n 30 /tmp/n8n.log`. Registro da Evolution: `docker compose logs --tail 30 evolution`.

## 🛠️ Gerar e conferir o fluxo

```bash
python3 n8n-fluxos/gerar_mvp.py n8n-fluxos/Template_SDR_EVO_v2_Vertice.json n8n-fluxos/SDR_Vertice_MVP_Groq_Texto.json
python3 n8n-fluxos/validar_fluxo.py n8n-fluxos/SDR_Vertice_MVP_Groq_Texto.json
```

## 🔑 Chaves e senhas (nunca no código)

- **Senhas da Evolution, Redis e Postgres:** geradas sozinhas no arquivo `.env` (já está no `.gitignore`).
- **Chaves da Groq e do Supabase:** coladas direto nas credenciais do n8n (veja o guia).
- **Chaves para bots em Python:** [Codespaces Secrets](https://github.com/settings/codespaces) → **New secret** (nome como `GEMINI_API_KEY`), escolha este repositório e reinicie o Codespace. No Python: `os.environ["GEMINI_API_KEY"]`.

## 💾 Salvar no GitHub (commit e push)

```bash
git add .
git commit -m "Descreva o que mudou"
git push
```

## ⏱️ Economizando as horas grátis do Codespace

Quando terminar, rode os dois `stop` e pare o Codespace em https://github.com/codespaces → `...` → **Stop codespace**. Em https://github.com/settings/codespaces deixe o *idle timeout* em 5 minutos.
