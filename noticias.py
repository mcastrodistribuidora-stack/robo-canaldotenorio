"""
Notícias do Vasco: busca o máximo possível e não repete.

Fontes:
  1. Google Notícias (RSS público): todas as notícias sobre o Vasco, de qualquer veículo
     (ge/Globo, ESPN, Lance!, Terra, SUPERVASCO, UOL, CNN…)
  2. NETVASCO (feed RSS próprio do site)

Só usa o TÍTULO e o nome do VEÍCULO (com crédito na arte). Não copia texto nem fotos das matérias.
"""
import email.utils
import html
import re
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

GOOGLE = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
PALAVRAS_VAZIAS = set("""a o as os de da do das dos e em no na nos nas um uma uns umas para pra por com sem que se sua seu
suas seus ao aos à às mais mas como apos após sobre contra entre ate até ja já nao não sim vai vao vão tem ter foi sao são
esta está estao estão pelo pela pelos pelas diz diga veja video vídeo apos ser sera será""".split())


def _baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (robo-noticias-vasco)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _data(txt):
    try:
        d = email.utils.parsedate_to_datetime(txt)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _itens(xml_bytes, fonte_fixa=None):
    for it in ET.fromstring(xml_bytes).iter("item"):
        titulo = html.unescape(it.findtext("title", "")).strip()
        src = it.find("source")
        fonte = fonte_fixa or (src.text.strip() if src is not None and src.text else "")
        if fonte and titulo.endswith(f" - {fonte}"):  # o Google põe " - Veículo" no fim
            titulo = titulo[: -len(fonte) - 3].strip()
        quando = _data(it.findtext("pubDate", ""))
        if quando and len(titulo) >= 20:
            yield {"id": it.findtext("link", "") or titulo, "titulo": titulo, "fonte": fonte or "imprensa",
                   "link": it.findtext("link", ""), "quando": quando}


def buscar_todas(config):
    horas = config.get("horas_maximas_da_noticia", 12)
    limite = datetime.now(timezone.utc) - timedelta(hours=horas)
    todas = []
    for termo in config.get("buscas_google", ["Vasco"]):
        try:
            todas += _itens(_baixar(GOOGLE.format(q=urllib.parse.quote(f"{termo} when:1d"))))
        except Exception as e:
            print(f"  [aviso] Google Notícias '{termo}': {e}")
    for nome, url in config.get("feeds_diretos", {}).items():
        try:
            todas += _itens(_baixar(url), fonte_fixa=nome)
        except Exception as e:
            print(f"  [aviso] feed {nome}: {e}")
    return [n for n in todas if n["quando"] >= limite and not _fora_do_tema(n["titulo"], config)]


def _fora_do_tema(titulo, config):
    t = _sem_acento(titulo.lower())
    return any(p in t for p in config.get("ignorar_se_tiver", []))


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def palavras(titulo):
    t = re.sub(r"[^a-z0-9 ]", " ", _sem_acento(titulo.lower()))
    return {w for w in t.split() if len(w) > 2 and w not in PALAVRAS_VAZIAS and w != "vasco"}


def parecidas(a, b):
    """True se dois títulos contam a mesma notícia (mesmas palavras principais)."""
    if not a or not b:
        return False
    comum = len(a & b)
    return comum / len(a | b) >= 0.4 or comum / min(len(a), len(b)) >= 0.6


def escolher(config, estado):
    """Notícias novas, da mais recente para a mais antiga, sem repetidas."""
    ja = [set(p) for p in estado.get("palavras", [])]
    ids = set(estado.get("ids", []))
    saida = []
    for n in sorted(buscar_todas(config), key=lambda n: n["quando"], reverse=True):
        p = palavras(n["titulo"])
        if n["id"] in ids or any(parecidas(p, x) for x in ja):
            continue
        ja.append(p)
        n["palavras"] = sorted(p)
        saida.append(n)
    return saida
