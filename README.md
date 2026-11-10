# I.A. para vendas

Ambiente para demonstrar automações de vendas para clientes B2B, usando **n8n** (montador de fluxos visual) e **bots em Python**.

## 📁 Onde fica cada coisa

| Pasta | O que guardar lá |
|---|---|
| `bots/` | Os bots escritos em Python (ex.: bot do Telegram, bot que usa o Gemini) |
| `n8n-fluxos/` | Os fluxos do n8n exportados em arquivo `.json` (backup e demonstração) |
| `docs/` | Anotações, roteiros de demonstração, materiais para clientes |
| `start-n8n.sh` | Script que liga o n8n |
| `stop-n8n.sh` | Script que desliga o n8n |

## ▶️ Como ligar o n8n

1. No terminal (parte de baixo da tela), digite:
   ```bash
   ./start-n8n.sh
   ```
2. Espere aparecer a frase `n8n ligado, abra o link` (na 1ª vez pode levar de 5 a 10 minutos, porque ele baixa o n8n).
3. Abra a aba **PORTAS** (ao lado de TERMINAL). Se a porta **5678** não aparecer, clique em **Adicionar porta** e digite `5678`.
4. Clique com o botão direito na 5678 → **Visibilidade da porta** → **Público**.
5. Clique no ícone de globo 🌐 da linha 5678 (ou abra o link que o script mostrou).

Para **desligar** o n8n:
```bash
./stop-n8n.sh
```

> 💡 O n8n roda em segundo plano: você pode fechar o terminal ou usá-lo para outras coisas que ele continua ligado.
> Se der problema, veja o que aconteceu com: `tail -n 30 /tmp/n8n.log`
>
> Seus fluxos e contas do n8n ficam em `/workspaces/.n8n-dados`, fora do projeto. Por isso eles **não** vão para o GitHub; para guardar um fluxo, exporte-o (veja abaixo).

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
