"""
Busca notícias de futebol no Google Notícias (RSS público, sem chave), do mesmo jeito que
alguém que digita o nome do clube no Google e abre a aba "Notícias".

Para cada time faz várias buscas:
  - o nome do time (tudo o que o Google Notícias mostra);
  - o nome do time dentro dos sites prioritários (ex.: ge.globo.com, uol.com.br).

Ordem de preferência: fontes prioritárias (ge, UOL), depois os sites de setoristas do clube
(config "fontes_time") e depois as demais fontes conhecidas. Entre fontes do mesmo nível, ganha a mais recente.
Alterna os times (um post do Vasco, outro do Palmeiras...) e não repete a mesma notícia,
nem quando veículos diferentes dão o mesmo fato com palavras diferentes.

Só usa o TÍTULO, o nome e o site do VEÍCULO. O texto do post é reescrito (resumo.py) e o veículo é creditado.
"""
import email.utils
import html
import re
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

RSS = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"


def _baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (robo-noticias)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _dominio(url):
    d = urllib.parse.urlparse(url or "").netloc.lower()
    return d[4:] if d.startswith("www.") else d


def buscar(termo, horas=8, site=None):
    """Lista de dicts: id, titulo, fonte, site, link, quando (UTC), termo, relacionadas."""
    consulta = f"{termo} site:{site}" if site else termo
    url = RSS.format(q=urllib.parse.quote(f"{consulta} when:1d"))
    raiz = ET.fromstring(_baixar(url))
    limite = datetime.now(timezone.utc) - timedelta(hours=horas)
    saida = []
    for it in raiz.iter("item"):
        titulo = html.unescape(it.findtext("title", "")).strip()
        fonte_el = it.find("source")
        fonte = (fonte_el.text if fonte_el is not None else "").strip()
        site_fonte = _dominio(fonte_el.get("url") if fonte_el is not None else "")
        # o Google coloca " - Veículo" no fim do título
        if fonte and titulo.endswith(f" - {fonte}"):
            titulo = titulo[: -len(fonte) - 3].strip()
        try:
            quando = email.utils.parsedate_to_datetime(it.findtext("pubDate", ""))
        except (TypeError, ValueError):
            continue
        if quando < limite or len(titulo) < 25:
            continue
        # o Google lista na descrição outras manchetes do mesmo fato: ajudam o resumo
        relacionadas = [html.unescape(re.sub(r"<[^>]+>", "", a)).strip()
                        for a in re.findall(r"<a [^>]*>(.*?)</a>", it.findtext("description", "") or "")]
        relacionadas = [r for r in relacionadas if r and r != titulo]
        saida.append({"id": it.findtext("guid", "") or it.findtext("link", ""), "titulo": titulo, "fonte": fonte,
                      "site": site_fonte, "link": it.findtext("link", ""), "quando": quando, "termo": termo,
                      "relacionadas": relacionadas})
    return saida


def _palavras(titulo):
    t = unicodedata.normalize("NFKD", titulo.lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return {w for w in re.findall(r"[a-z0-9]+", t) if len(w) > 3}


def chave_parecida(titulo):
    """Normaliza o título para não postar a mesma notícia de dois veículos."""
    return " ".join(sorted(_palavras(titulo))[:8])


def parecida(titulo, titulos_recentes, limite=0.6):
    """True se o título fala do mesmo fato que algum título já postado (palavras em comum)."""
    a = _palavras(titulo)
    for t in titulos_recentes:
        b = _palavras(t)
        comuns = len(a & b)
        if a and b and comuns >= 3 and comuns / min(len(a), len(b)) >= limite:
            return True
    return False


NAO_E_NOTICIA = re.compile(
    r"ao vivo|tempo real|minuto a minuto|siga o placar|siga placar|acompanhe o jogo|acompanhe a partida"
    r"|placar ao vivo|lance a lance|onde assistir|que horas [ée]|qual canal|palpite|odds|aposta"
    r"|voc[êe] escala|monte (o|a|seu|sua)|escale (o|seu)|quiz|teste seus|enquete|vote |vote:|vota[çc][ãa]o"
    r"|cartola|fantasy|bol[ãa]o", re.I)
SITES_BLOQUEADOS = ("placar.uol.com.br",)


def e_noticia(n):
    """Descarta páginas de placar/transmissão ao vivo, 'onde assistir' e apostas: não são notícia."""
    if NAO_E_NOTICIA.search(n["titulo"]):
        return False
    return not any(n.get("site", "").endswith(b) for b in SITES_BLOQUEADOS)


def fala_do_time(n, config):
    """True se o TÍTULO cita o time ou um apelido dele (evita notícia que só menciona o clube no meio)."""
    termos = config.get("palavras_time", {}).get(n["termo"], []) + [n["termo"]]
    tit = unicodedata.normalize("NFKD", n["titulo"].lower())
    tit = "".join(ch for ch in tit if not unicodedata.combining(ch))
    for termo in termos:
        k = unicodedata.normalize("NFKD", termo.lower())
        k = "".join(ch for ch in k if not unicodedata.combining(ch))
        if re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", tit):
            return True
    return False


def _nivel_fonte(n, config):
    """0 = ge/UOL, 1 = setoristas do clube, 2 = outras conhecidas, 3 = demais."""
    nome, site = n["fonte"].lower(), n.get("site", "")
    listas = [config.get("fontes_prioritarias", []),
              config.get("fontes_time", {}).get(n["termo"], []),
              config.get("fontes_preferidas", [])]
    for nivel, lista in enumerate(listas):
        for f in lista:
            f = f.lower()
            if nome == f or nome.startswith(f + " ") or (len(f) > 3 and f in nome) or (site and f in site):
                return nivel
    return len(listas)


def escolher(config, ja_postados, titulos_recentes=(), ultimo_time=None):
    horas = config.get("horas_maximas_da_noticia", 8)
    candidatos = []
    for termo in config["times"] + config.get("busca_extra", []):
        for site in [None] + config.get("buscar_nos_sites", []):
            try:
                candidatos += buscar(termo, horas, site)
            except Exception as e:
                print(f"  [aviso] não consegui buscar '{termo}' {site or ''}: {e}")
    antes = len(candidatos)
    candidatos = [n for n in candidatos if fala_do_time(n, config) and e_noticia(n)]
    print(f"  {len(candidatos)} de {antes} notícias encontradas são notícia de verdade sobre os times")
    if config.get("so_fontes_conhecidas"):
        candidatos = [n for n in candidatos if _nivel_fonte(n, config) < 3]

    def nota(n):  # alterna os times; depois fonte prioritária; depois a mais recente
        return (n["termo"] == ultimo_time, _nivel_fonte(n, config), -n["quando"].timestamp())

    vistos, saida, titulos = set(ja_postados), [], list(titulos_recentes)
    for n in sorted(candidatos, key=nota):
        k = chave_parecida(n["titulo"])
        if n["id"] in vistos or k in vistos or parecida(n["titulo"], titulos):
            continue
        vistos.update({n["id"], k})
        titulos.append(n["titulo"])
        saida.append(n)
    return saida


def mais_manchetes(n, horas=36):
    """Procura o MESMO fato em outros veículos (mais fatos para o resumo da legenda)."""
    palavras = sorted(_palavras(n["titulo"]) - _palavras(n["termo"]), key=len, reverse=True)[:4]
    if not palavras:
        return []
    achadas = buscar(f'{n["termo"]} {" ".join(palavras)}', horas)
    saida, base = [], _palavras(n["titulo"])
    for x in achadas:
        if x["titulo"] == n["titulo"] or len(_palavras(x["titulo"]) & base) < 2:
            continue
        saida.append(f'{x["titulo"]} ({x["fonte"]})')
    return saida[:10]
