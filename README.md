# I.A. para vendas

Ambiente para demonstrar automações de vendas para clientes B2B, usando **n8n** (montador de fluxos visual) e **bots em Python**.

## 📁 Onde fica cada coisa

| Pasta | O que guardar lá |
|---|---|
| `bots/` | Os bots escritos em Python (ex.: bot do Telegram, bot que usa o Gemini) |
| `n8n-fluxos/` | Os fluxos do n8n exportados em arquivo `.json` (backup e demonstração) |
| `docs/` | Anotações, roteiros de demonstração, materiais para clientes |
| `start-n8n.sh` | Script que liga o n8n |

## ▶️ Como ligar o n8n

1. No terminal (parte de baixo da tela), digite:
   ```bash
   ./start-n8n.sh
   ```
2. Espere aparecer a mensagem `Editor is now accessible via` (na 1ª vez pode levar alguns minutos).
3. Abra a aba **PORTAS** (ao lado de TERMINAL), procure a porta **5678** e clique no ícone de globo 🌐 para abrir no navegador.
4. Para **desligar**, volte ao terminal e aperte `Ctrl + C`.

> 💡 Deixe o terminal do n8n aberto. Para digitar outros comandos, abra um terminal novo no botão `+`.

### Salvando seus fluxos no projeto
No n8n, abra o fluxo → menu `...` (canto superior direito) → **Download**. Arraste o arquivo baixado para a pasta `n8n-fluxos/`.

## 🔑 Chaves de API (Gemini, Telegram etc.)

**Nunca** escreva chaves dentro do código. Guarde-as nos **Codespaces Secrets**:

1. Acesse https://github.com/settings/codespaces
2. Em **Secrets**, clique em **New secret**.
3. Nome: por exemplo `GEMINI_API_KEY` ou `TELEGRAM_BOT_TOKEN`. Valor: cole a chave.
4. Em **Repository access**, escolha este repositório.
5. Reinicie o Codespace (ou feche e abra de novo). A chave vira uma "variável de ambiente".

No Python, leia assim:
```python
import os
chave = os.environ["GEMINI_API_KEY"]
```

No n8n, prefira cadastrar a chave em **Credentials** (fica guardada no próprio n8n, fora do Git).

## 💾 Como salvar no GitHub (commit e push)

No terminal:
```bash
git add .
git commit -m "Descreva aqui o que você mudou"
git push
```

- `git add .` → separa todos os arquivos alterados
- `git commit -m "..."` → tira uma "foto" das mudanças com uma descrição
- `git push` → envia essa foto para o GitHub

## ⏱️ Economizando horas do Codespace

O plano grátis tem limite de horas. Quando terminar, pare o Codespace em https://github.com/codespaces → `...` → **Stop codespace**.
