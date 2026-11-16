"""
Busca FOTOS REAIS COM LICENÇA LIVRE para a notícia, sozinho.

Fontes:
  - Wikimedia Commons (não precisa de chave)
  - Flickr (opcional: só se existir o secret FLICKR_API_KEY)

Regras de segurança (direitos autorais):
  - Só aceita licenças que permitem uso e edição: CC0, domínio público, CC BY e CC BY-SA.
  - Recusa "ND" (proíbe editar, e a arte edita a foto).
  - Recusa "NC" (proíbe uso comercial), a não ser que config.json diga "aceitar_nao_comercial": true.
  - Guarda o nome do autor, a licença e o link, para o crédito na arte e na legenda.
  - Confere se o nome do jogador/estádio aparece na descrição da foto, para não pegar foto errada.
"""
import html
import json
import os
import re
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

UA = "RoboNoticiasFutebol/1.0 (robo de noticias de futebol para Instagram; uso com credito)"
COMMONS = "https://commons.wikimedia.org/w/api.php"
FLICKR = "https://api.flickr.com/services/rest/"


# ---------------------------------------------------------------- utilidades
def _get_json(url, params):
    req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def baixar(url, destino):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        destino.write_bytes(r.read())
    return destino


def sem_acento(t):
    t = unicodedata.normalize("NFKD", t or "")
    return "".join(ch for ch in t if not unicodedata.combining(ch)).lower()


def limpar_html(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def licenca_ok(nome, aceitar_nc=False):
    """True se a licença permite usar e editar a foto (com crédito)."""
    s = sem_acento(nome)
    tok = set(re.split(r"[^a-z0-9]+", s))
    if "nd" in tok or "noderivs" in s or "no derivatives" in s:
        return False
    if ("nc" in tok or "noncommercial" in s or "non-commercial" in s) and not aceitar_nc:
        return False
    if "cc0" in tok or "public domain" in s or "dominio publico" in s or s.startswith("pd") or "no known copyright" in s:
        return True
    if ("cc" in tok and "by" in tok) or "attribution" in s:
        return True
    return False  # licença desconhecida ou "uso justo": não usa


def _tem_palavras(texto, exigir):
    t = sem_acento(texto)
    return all(sem_acento(p) in t for p in exigir)


def _ano(t):
    m = re.search(r"(19|20)\d\d", t or "")
    return int(m.group(0)) if m else 0


# ---------------------------------------------------------------- Wikimedia
def buscar_commons(busca, exigir, aceitar_nc=False, limite=40):
    dados = _get_json(COMMONS, {
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": f"{busca} filetype:bitmap", "gsrlimit": limite,
        "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 1600,
    })
    saida = []
    for p in (dados.get("query") or {}).get("pages", {}).values():
        info = (p.get("imageinfo") or [{}])[0]
        meta = {k: (v or {}).get("value", "") for k, v in (info.get("extmetadata") or {}).items()}
        if info.get("mime") not in ("image/jpeg", "image/png") or min(info.get("width", 0), info.get("height", 0)) < 700:
            continue
        if str(meta.get("NonFree", "")).lower() == "true":
            continue
        lic = meta.get("LicenseShortName") or meta.get("License", "")
        if not licenca_ok(lic, aceitar_nc):
            continue
        texto = " ".join([p.get("title", ""), limpar_html(meta.get("ImageDescription")),
                          limpar_html(meta.get("ObjectName")), meta.get("Categories", "")])
        if not _tem_palavras(texto, exigir):
            continue
        autor = limpar_html(meta.get("Artist")) or "autor desconhecido"
        autor = re.sub(r"\s*\(talk\)|\s*\(discussão\)", "", autor)[:70]
        saida.append({
            "id": p.get("title", ""), "url": info.get("thumburl") or info.get("url"),
            "autor": autor, "licenca": lic, "licenca_url": meta.get("LicenseUrl", ""),
            "pagina": info.get("descriptionurl", ""), "origem": "Wikimedia Commons",
            "ano": _ano(meta.get("DateTimeOriginal") or meta.get("DateTime")),
            "retrato": info.get("height", 0) >= info.get("width", 1),
        })
    return saida


# ---------------------------------------------------------------- Flickr
_flickr_lic = None


def _licencas_flickr(chave, aceitar_nc):
    global _flickr_lic
    if _flickr_lic is None:
        d = _get_json(FLICKR, {"method": "flickr.photos.licenses.getInfo", "api_key": chave,
                               "format": "json", "nojsoncallback": 1})
        _flickr_lic = {str(l["id"]): l for l in d["licenses"]["license"]}
    return {i: l for i, l in _flickr_lic.items() if licenca_ok(l["name"], aceitar_nc)}


def buscar_flickr(busca, exigir, aceitar_nc=False, limite=40):
    chave = os.environ.get("FLICKR_API_KEY")
    if not chave:
        return []
    lic = _licencas_flickr(chave, aceitar_nc)
    d = _get_json(FLICKR, {
        "method": "flickr.photos.search", "api_key": chave, "text": busca, "license": ",".join(lic),
        "sort": "relevance", "content_type": 1, "media": "photos", "per_page": limite,
        "extras": "owner_name,license,url_l,url_c,date_taken,description,tags",
        "format": "json", "nojsoncallback": 1,
    })
    saida = []
    for f in d.get("photos", {}).get("photo", []):
        url = f.get("url_l") or f.get("url_c")
        l = lic.get(str(f.get("license")))
        if not url or not l:
            continue
        texto = " ".join([f.get("title", ""), (f.get("description") or {}).get("_content", ""), f.get("tags", "")])
        if not _tem_palavras(texto, exigir):
            continue
        w, h = int(f.get("width_l") or f.get("width_c") or 0), int(f.get("height_l") or f.get("height_c") or 0)
        saida.append({
            "id": f"flickr:{f['id']}", "url": url, "autor": (f.get("ownername") or "autor no Flickr")[:70],
            "licenca": l["name"], "licenca_url": l.get("url", ""),
            "pagina": f"https://www.flickr.com/photos/{f['owner']}/{f['id']}", "origem": "Flickr",
            "ano": _ano(f.get("datetaken")), "retrato": h >= w,
        })
    return saida


# ---------------------------------------------------------------- escolha
def buscas_para(pessoas, noticia, config):
    """Lista de (busca, palavras obrigatórias), da mais específica para a mais genérica."""
    lista = []
    for nome in pessoas:
        partes = nome.split()
        sobrenome = partes[-1] if partes else nome
        lista.append((nome, [sobrenome] if len(partes) == 1 else [partes[0], sobrenome]))
    for item in (config.get("fotos", {}).get("fotos_time", {}).get(noticia.get("termo", ""), [])):
        lista.append((item["busca"], item.get("exigir", [])))
    return lista


def escolher_foto(pessoas, noticia, config, usadas=()):
    cf = config.get("fotos", {})
    if not cf.get("usar", True):
        return None
    nc = cf.get("aceitar_nao_comercial", False)
    fontes = cf.get("fontes", ["commons", "flickr"])
    usadas = set(usadas)
    for busca, exigir in buscas_para(pessoas, noticia, config):
        achadas = []
        for fonte, func in (("commons", buscar_commons), ("flickr", buscar_flickr)):
            if fonte not in fontes:
                continue
            try:
                achadas += func(busca, exigir, nc)
            except Exception as ex:
                print(f"  [aviso] busca de foto em {fonte} falhou ({busca}): {ex}")
        if not achadas:
            continue
        # prefere: foto ainda não usada, mais recente, em pé (encaixa melhor no 4:5)
        achadas.sort(key=lambda f: (f["id"] in usadas, -f["ano"], not f["retrato"]))
        escolhida = achadas[0]
        print(f"  📸 foto: {escolhida['id']} | {escolhida['autor']} | {escolhida['licenca']}")
        return escolhida
    print("  (nenhuma foto livre encontrada; vai a arte só com texto)")
    return None


def credito(foto):
    """Texto de crédito exigido pelas licenças CC: autor, onde está, licença e aviso de edição."""
    lic = foto["licenca"]
    extra = f" ({foto['licenca_url']})" if foto.get("licenca_url") else ""
    return f"{foto['autor']} / {foto['origem']}, {lic}{extra}. Foto editada (recorte e texto)."
