"""
Posts de ESTATÍSTICA do Vasco com dados do NETVASCO (temporadas 2024, 2025 e 2026).

O robô baixa a página de estatísticas de cada temporada, lê as tabelas
(competições, jogadores e técnicos) e monta posts que puxam comentário:
comparação entre temporadas, rankings e uma pergunta para o público.
Crédito sempre: "Dados: NETVASCO". (O NETVASCO não publica assistências.)
"""
import html
import re
import urllib.request

URL = "https://netvasco.com/futebol/estatisticas/index17.shtml?ano={ano}"
COLS_JOG = ["J", "G", "MG", "CA", "CV", "Tit", "Sub", "Ent", "V", "E", "D", "%"]


def _num(s):
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        return s


def ler_tabelas(pagina_html):
    tabelas = []
    for t in re.findall(r"<table.*?</table>", pagina_html, re.S | re.I):
        linhas = []
        for tr in re.findall(r"<tr.*?</tr>", t, re.S | re.I):
            cel = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
            if cel:
                linhas.append(cel)
        tabelas.append(linhas)
    return tabelas


def temporada(ano):
    req = urllib.request.Request(URL.format(ano=ano), headers={"User-Agent": "Mozilla/5.0 (robo-noticias-vasco)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return organizar(ler_tabelas(r.read().decode("utf-8", "replace")))


def organizar(tabelas):
    d = {"competicoes": {}, "jogadores": {}, "tecnicos": {}}
    for t in tabelas:
        if not t:
            continue
        cab = t[0]
        if cab[0].startswith("Competi"):
            for l in t[1:]:
                d["competicoes"][l[0]] = dict(zip(cab[1:], map(_num, l[1:])))
        elif cab[:3] == ["Jogador", "J", "G"]:
            for l in t[1:]:
                d["jogadores"][l[0]] = dict(zip(cab[1:], map(_num, l[1:])))
        elif cab[:3] == ["Jogador", "J", "CA"]:
            for l in t[1:]:
                d["tecnicos"][l[0]] = dict(zip(cab[1:], map(_num, l[1:])))
    return d


# ---------------------------------------------------------------- ideias de post
def _linha(valor, chave, nome):
    if chave == "%":
        return f"{valor}% de {nome}"
    if valor == 1 and nome.endswith("ões"):
        nome = nome[:-3] + "ão"
    elif valor == 1 and nome.endswith("s"):
        nome = nome[:-1]
    return f"{valor} {nome}"


def ideias(dados):
    """Lista de posts prontos (dicts para o design 'estatistica'). dados = {ano: temporada}."""
    anos = sorted(dados)
    atual = anos[-1]
    J = {a: dados[a]["jogadores"] for a in anos}
    posts = []

    def comparar(nome, titulo, metricas, pergunta, destaque="J"):
        if not all(nome in J[a] for a in anos):
            return
        cols = []
        for a in anos:
            p = J[a][nome]
            cols.append({"ano": a, "grande": p[destaque], "rotulo": metricas[destaque],
                         "linhas": [_linha(p[k], k, v) for k, v in metricas.items() if k != destaque]})
        posts.append({"id": f"cmp-{nome}-{destaque}-{atual}", "tipo": "comparativo", "selo": "Comparativo",
                      "titulo": titulo, "colunas": cols, "pergunta": pergunta, "jogador": nome})

    # 1) goleiro titular: jogos e aproveitamento
    comparar("Léo Jardim", "Léo Jardim nas últimas 3 temporadas",
             {"J": "jogos", "V": "vitórias", "%": "aproveitamento", "CA": "cartões"},
             "Qual é a melhor versão de Léo Jardim?")
    # 2) quem mais cresceu em gols
    for nome in sorted(J[atual], key=lambda n: -J[atual][n]["G"])[:3]:
        comparar(nome, f"{nome}: gols por temporada", {"G": "gols", "J": "jogos", "Tit": "como titular"},
                 f"{nome} já é o homem-gol do Vasco?", destaque="G")
    # 3) artilheiro de cada temporada
    cols = []
    for a in anos:
        nome, p = max(J[a].items(), key=lambda kv: kv[1]["G"])
        cols.append({"ano": a, "grande": p["G"], "rotulo": "gols", "linhas": [nome, f"{p['J']} jogos"]})
    posts.append({"id": f"artilheiros-{atual}", "tipo": "comparativo", "selo": "Artilharia",
                  "titulo": "O artilheiro do Vasco em cada temporada", "colunas": cols,
                  "pergunta": "O Vasco sente falta de um artilheiro como o Vegetti?"
                  if cols[-1]["linhas"][0] != "Vegetti" else "Vegetti é o maior artilheiro da sua geração?"})
    # 4) ranking de gols da temporada atual
    top = sorted(J[atual].items(), key=lambda kv: (-kv[1]["G"], kv[1]["J"]))[:5]
    posts.append({"id": f"top-gols-{atual}", "tipo": "ranking", "selo": f"Artilharia {atual}",
                  "titulo": f"Artilheiros do Vasco em {atual}",
                  "itens": [{"nome": n, "valor": p["G"], "extra": f"{p['J']} jogos"} for n, p in top],
                  "unidade": "gols", "pergunta": "Quem vai terminar o ano como artilheiro?"})
    # 5) ranking de cartões
    top = sorted(J[atual].items(), key=lambda kv: (-kv[1]["CA"], kv[1]["J"]))[:5]
    posts.append({"id": f"top-cartoes-{atual}", "tipo": "ranking", "selo": f"Disciplina {atual}",
                  "titulo": f"Quem mais levou amarelo em {atual}",
                  "itens": [{"nome": n, "valor": p["CA"], "extra": f"{p['CV']} vermelho(s)"} for n, p in top],
                  "unidade": "amarelos", "pergunta": "Raça ou falta de controle?"})
    # 6) técnicos da temporada
    tec = sorted([kv for kv in dados[atual]["tecnicos"].items() if kv[1]["J"] >= 5], key=lambda kv: -kv[1]["%"])[:4]
    posts.append({"id": f"tecnicos-{atual}", "tipo": "ranking", "selo": f"Técnicos {atual}",
                  "titulo": f"Aproveitamento dos técnicos em {atual}",
                  "itens": [{"nome": n, "valor": t["%"], "extra": f"{t['J']} jogos · {t['V']}V {t['E']}E {t['D']}D"} for n, t in tec],
                  "unidade": "%", "pergunta": "Quem foi o melhor técnico do Vasco no ano?"})
    # 7) temporada do time
    cols = []
    for a in anos:
        t = dados[a]["competicoes"].get("Total", {})
        if t:
            cols.append({"ano": a, "grande": t["%"], "rotulo": "aproveitamento", "pct": True,
                         "linhas": [f"{t['J']} jogos", f"{t['V']}V {t['E']}E {t['D']}D", f"saldo {t['S']:+d}"]})
    posts.append({"id": f"temporadas-{atual}", "tipo": "comparativo", "selo": "Temporadas",
                  "titulo": "O Vasco nas últimas 3 temporadas", "colunas": cols,
                  "pergunta": f"{atual} foi o melhor ano dos três?"})
    return posts
