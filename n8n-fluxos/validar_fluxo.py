#!/usr/bin/env python3
"""Confere um fluxo do n8n (arquivo .json) e avisa o que está quebrado.

Uso:   python3 n8n-fluxos/validar_fluxo.py n8n-fluxos/MEU_FLUXO.json

O que ele confere:
  1. O arquivo é um JSON válido e os nomes dos nós não se repetem.
  2. Todo tipo de nó existe no n8n instalado (e a versão do nó é aceita).
  3. Toda ligação aponta para um nó que existe, numa saída que existe.
  4. Nós "soltos" (sem entrada) - podem ser de propósito, vira aviso.
  5. Expressões como $('Nome do nó') que apontam para um nó inexistente.
  6. Credenciais de outra pessoa gravadas no arquivo.
"""
import glob
import json
import os
import re
import sys

ERROS, AVISOS = [], []


def catalogo():
    """Lê a lista de nós do n8n instalado (rodando `npx n8n` pelo menos uma vez)."""
    cat = {}
    raizes = glob.glob("/workspaces/.n8n-app/node_modules")
    raizes += glob.glob(os.path.expanduser("~/.npm/_npx/*/node_modules"))
    raizes += glob.glob("/usr/lib/node_modules") + glob.glob("/usr/local/lib/node_modules")
    RAIZES.extend(raizes)
    pacotes = [
        ("n8n-nodes-base", "n8n-nodes-base/dist/types/nodes.json"),
        ("@n8n/n8n-nodes-langchain", "@n8n/n8n-nodes-langchain/dist/types/nodes.json"),
    ]
    for raiz in raizes:
        for prefixo, rel in pacotes:
            arq = os.path.join(raiz, rel)
            if os.path.exists(arq):
                for n in json.load(open(arq)):
                    cat[f"{prefixo}.{n['name']}"] = n
    return cat


RAIZES = []


def versoes_do_nó(tipo, def_catalogo):
    """Versões aceitas. Usa a pasta 'node-definitions' (um arquivo por versão: v34 = 3.4)."""
    prefixo, nome = tipo.rsplit(".", 1)
    pasta_pkg = {"n8n-nodes-base": "n8n-nodes-base", "@n8n/n8n-nodes-langchain": "@n8n/n8n-nodes-langchain"}[prefixo]
    sub = prefixo.split("/")[-1]
    for raiz in RAIZES:
        pasta = os.path.join(raiz, pasta_pkg, "dist", "node-definitions", "nodes", sub, nome)
        if os.path.isdir(pasta):
            achadas = set()
            for item in os.listdir(pasta):
                m = re.match(r"^v(\d+)(?:\.schema\.js|\.ts)?$", item)
                if m:
                    d = m.group(1)
                    achadas.add(float(d) if len(d) == 1 else float(d[0] + "." + d[1:]))
            if achadas:
                return sorted(achadas)
    v = def_catalogo.get("version")
    return [float(x) for x in (v if isinstance(v, list) else [v])]


def num_saidas(no, def_catalogo):
    t, p = no["type"], no.get("parameters", {})
    if t.endswith(".if"):
        return 2
    if t.endswith(".switch"):
        regras = p.get("rules", {}).get("values", [])
        extra = 1 if p.get("options", {}).get("fallbackOutput") == "extra" else 0
        return max(len(regras) + extra, 1)
    if t.endswith(".splitInBatches"):
        return 2
    saidas = def_catalogo.get("outputs") if def_catalogo else None
    return len(saidas) if isinstance(saidas, list) else 1


def main(caminho):
    try:
        d = json.load(open(caminho, encoding="utf-8"))
    except Exception as e:
        print(f"❌ Não consegui ler o arquivo: {e}")
        return 1
    cat = catalogo()
    if not cat:
        AVISOS.append("Catálogo de nós do n8n não encontrado (rode ./start-n8n.sh uma vez). Pulei a checagem de tipos.")
    nos = d.get("nodes", [])
    por_nome = {}
    for n in nos:
        if n["name"] in por_nome:
            ERROS.append(f"Nome de nó repetido: '{n['name']}'")
        por_nome[n["name"]] = n

    # 2) tipos e versões
    for n in nos:
        t = n["type"]
        # "xxxTool" = versão do nó usada como ferramenta de IA (o n8n gera sozinho)
        base_t = t[:-4] if t.endswith("Tool") and t[:-4] in cat else t
        if cat and base_t not in cat:
            if t.startswith(("n8n-nodes-base.", "@n8n/n8n-nodes-langchain.")):
                ERROS.append(f"'{n['name']}': tipo de nó não existe nesta versão do n8n ({t})")
            else:
                AVISOS.append(f"'{n['name']}': nó de COMUNIDADE ({t}). Precisa ser instalado no n8n antes de usar.")
        elif cat and float(n["typeVersion"]) not in versoes_do_nó(base_t, cat[base_t]):
            ERROS.append(f"'{n['name']}': versão {n['typeVersion']} do nó não existe (aceitas: {versoes_do_nó(base_t, cat[base_t])})")

    # 3) ligações
    tem_entrada, tem_saida = set(), set()
    for origem, tipos in d.get("connections", {}).items():
        if origem not in por_nome:
            ERROS.append(f"Ligação sai de um nó que não existe: '{origem}'")
            continue
        for tipo, saidas in tipos.items():
            limite = num_saidas(por_nome[origem], cat.get(por_nome[origem]["type"])) if tipo == "main" else 1
            for i, destinos in enumerate(saidas):
                if tipo == "main" and i >= limite and destinos:
                    ERROS.append(f"'{origem}' não tem a saída número {i} (só {limite}), mas há ligação nela")
                for x in destinos or []:
                    if x["node"] not in por_nome:
                        ERROS.append(f"'{origem}' liga em '{x['node']}', que não existe")
                    else:
                        tem_entrada.add(x["node"])
                        tem_saida.add(origem)

    # 4) nós soltos
    for n in nos:
        nome, t = n["name"], n["type"]
        if t.endswith("stickyNote") or "webhook" in t.lower() or "trigger" in t.lower():
            continue
        if nome not in tem_entrada:
            if nome in tem_saida:
                AVISOS.append(f"'{nome}' não recebe nada de ninguém (só manda). Normal para ferramentas/modelos de IA; se não for, está solto.")
            else:
                AVISOS.append(f"'{nome}' está totalmente solto (sem ligações).")

    # 5) expressões que citam nós inexistentes
    for n in nos:
        texto = json.dumps(n.get("parameters", {}), ensure_ascii=False)
        for citado in set(re.findall(r"\$\(\\?['\"]([^'\"\\]+)\\?['\"]\)", texto)):
            if citado not in por_nome:
                ERROS.append(f"'{n['name']}' usa $('{citado}'), mas esse nó não existe")

    # 6) credenciais embutidas
    for n in nos:
        for tipo, c in n.get("credentials", {}).items():
            if str(c.get("id", "")).startswith("sdr"):
                continue  # credenciais com os nomes padrão deste projeto (ex.: "Redis SDR")
            AVISOS.append(f"'{n['name']}' traz a credencial '{c.get('name')}' de outro n8n. Escolha a sua dentro do nó.")

    print(f"Arquivo: {caminho}  |  {len(nos)} nós")
    for e in ERROS:
        print("❌", e)
    for a in AVISOS:
        print("⚠️ ", a)
    if not ERROS:
        print("✅ Nenhum erro de estrutura encontrado.")
    return 1 if ERROS else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
