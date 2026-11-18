"""
Fotos automáticas com LICENÇA LIVRE (Wikimedia Commons, o banco de imagens da Wikipédia).

1. Procura nomes próprios na manchete (ex.: "Robert Renan", "Andrés Gómez") e busca a foto da pessoa.
2. Se não achar, usa uma foto de São Januário.
3. Sempre devolve o crédito exigido pela licença (autor + licença).
Se nada der certo, a arte sai no modelo só com texto.
"""
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "robo-noticias-vasco/1.0 (Instagram; contato via GitHub)"}
LICENCAS_OK = ("cc0", "cc by", "cc-by", "public domain", "domínio público", "pd")
NAO_NOMES = {"Vasco", "Gama", "Brasileirão", "Brasileiro", "Copa", "Série", "Sul", "Americana", "Libertadores", "Seleção",
             "Brasileira", "Rio", "Janeiro", "Carioca", "São", "Januário", "Sub", "Veja", "Após", "Saiba", "Entenda", "Cruz", "Malta"}


def _get(params):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.loads(r.read())


def nomes_da_manchete(titulo):
    """Sequências de 2-3 palavras com inicial maiúscula (sem a primeira palavra da frase)."""
    palavras = titulo.split()
    achados, atual = [], []
    for i, w in enumerate(palavras):
        limpo = re.sub(r"[^\wÀ-ÿ'-]", "", w)
        if i > 0 and limpo[:1].isupper() and limpo not in NAO_NOMES and len(limpo) > 1:
            atual.append(limpo)
        else:
            if len(atual) >= 2:
                achados.append(" ".join(atual[:3]))
            atual = []
        if w.endswith((",", ":", ";", ".")) and len(atual) >= 2:
            achados.append(" ".join(atual[:3]))
            atual = []
    if len(atual) >= 2:
        achados.append(" ".join(atual[:3]))
    return list(dict.fromkeys(achados))


def _sem_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def _procurar(busca, exigir=None):
    d = _get({"action": "query", "generator": "search", "gsrsearch": f"{busca} filetype:bitmap", "gsrnamespace": 6,
              "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1600})
    paginas = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    for p in paginas:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        lic = _sem_tags(meta.get("LicenseShortName", {}).get("value", ""))
        if not any(l in lic.lower() for l in LICENCAS_OK):
            continue
        if info.get("width", 0) < 800:
            continue
        if exigir and not all(w.lower() in p["title"].lower() for w in exigir.split()[:2]):
            continue
        autor = _sem_tags(meta.get("Artist", {}).get("value", ""))[:60] or "Wikimedia Commons"
        return {"url": info.get("thumburl") or info["url"], "credito": f"Foto: {autor} / Wikimedia Commons ({lic})"}
    return None


def baixar_foto(titulo, destino, plano_b="Estádio São Januário"):
    """Salva a foto em destino e devolve o crédito; None se não achar."""
    tentativas = [(n, n) for n in nomes_da_manchete(titulo)] + [(plano_b, None)]
    for busca, exigir in tentativas:
        try:
            achou = _procurar(busca, exigir)
            if not achou:
                continue
            req = urllib.request.Request(achou["url"], headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                Path(destino).parent.mkdir(parents=True, exist_ok=True)
                Path(destino).write_bytes(r.read())
            return achou["credito"]
        except Exception as e:
            print(f"  [aviso] foto '{busca}': {e}")
    return None
