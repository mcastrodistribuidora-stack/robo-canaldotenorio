"""Designs das artes de notícia (HTML -> imagem pelo artes.py). Cores e nome vêm do config.json."""
import html
from pathlib import Path

e = html.escape

FIT = """<script>
document.fonts.ready.then(() => {
  window.problemas = [];
  document.querySelectorAll('[data-fit]').forEach(el => {
    let t = +el.dataset.fit, min = +(el.dataset.min || 30), maxH = +el.dataset.maxh;
    el.style.fontSize = t + 'px';
    while (t > min && el.scrollHeight > maxH) { t -= 2; el.style.fontSize = t + 'px'; }
    if (el.scrollHeight > maxH) window.problemas.push('texto grande demais');
  });
  window.pronto = true;
});
</script>"""


PASTA = Path(__file__).resolve().parent
REDES = [("youtube", "YouTube"), ("instagram", "Instagram"), ("tiktok", "TikTok")]


def _chip(c):
    """Selo duplo: nome do time + assunto (ex.: VASCO | MERCADO DA BOLA)."""
    time_ = c.get("termo", "")
    selo = c.get("selo", "Notícia")
    tam = 24 if len(time_) + len(selo) <= 22 else 20
    return (f'<div class="chip" style="font-size:{tam}px">'
            f'<span class="chip-time">{e(time_)}</span><span class="chip-selo">{e(selo)}</span></div>')


def _siga(c):
    """Bloco pequeno 'SIGA' + ícones das redes + @. Ícones oficiais: coloque PNGs em icones/ (ver LEIA-ME)."""
    itens = []
    for chave, nome in REDES:
        if chave not in c.get("redes", {"youtube": 1, "instagram": 1, "tiktok": 1}):
            continue
        arq = PASTA / "icones" / f"{chave}.png"
        if arq.exists():
            itens.append(f'<img class="ico" src="{arq.as_uri()}" alt="{nome}">')
        else:
            itens.append(f'<span class="rede">{nome}</span>')
    return (f'<div class="siga"><div class="siga-linha"><span class="siga-txt">SIGA</span>{"".join(itens)}</div>'
            f'<div class="arroba">{e(c["arroba"])}</div></div>')


CSS_COMUM = """
.chip{{display:flex;font-family:P;font-weight:700;letter-spacing:3px;text-transform:uppercase;white-space:nowrap}}
.chip span{{padding:10px 18px}}
.chip-time{{background:#fff;color:#0B0B0B}}
.chip-selo{{background:{detalhe};color:#fff}}
.siga{{text-align:right;white-space:nowrap}}
.siga-linha{{display:flex;align-items:center;justify-content:flex-end;gap:12px;margin-bottom:8px}}
.siga-txt{{font:700 18px P;letter-spacing:3px;opacity:.85}}
.ico{{height:30px;width:auto;display:block}}
.rede{{font:700 15px P;letter-spacing:1px;border:2px solid rgba(255,255,255,.55);border-radius:6px;padding:3px 8px;opacity:.9}}
.arroba{{font:800 32px D}}
"""


def _pagina(c, altura):
    cor = c["cores"]
    story = altura == 1920
    topo_titulo = 330 if story else 250
    alt_titulo = 900 if story else 700
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:D;src:url("../fontes/InterDisplay-Black.otf");font-weight:900}}
@font-face{{font-family:D;src:url("../fontes/InterDisplay-ExtraBold.otf");font-weight:800}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Medium.ttf");font-weight:500}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Bold.ttf");font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:{altura}px;overflow:hidden;background:{cor['fundo']};color:{cor['texto']};font-family:P,sans-serif}}
.listra{{position:absolute;left:0;top:0;bottom:0;width:22px;background:{cor['detalhe']}}}
.diag{{position:absolute;right:-220px;top:-160px;width:720px;height:720px;border:70px solid {cor['detalhe']};opacity:.16;transform:rotate(45deg)}}
.topo{{position:absolute;left:80px;right:70px;top:{110 if story else 70}px;display:flex;justify-content:space-between;align-items:center}}
.marca{{font:900 34px D;letter-spacing:1px;text-transform:uppercase}}
{CSS_COMUM.format(detalhe=cor['detalhe'])}
.titulo{{position:absolute;left:80px;right:80px;top:{topo_titulo}px;font-family:D;font-weight:900;line-height:1.04;letter-spacing:-1.5px;color:{cor['destaque']}}}
.rodape{{position:absolute;left:80px;right:80px;bottom:{150 if story else 70}px;display:flex;justify-content:space-between;align-items:flex-end;
        border-top:3px solid {cor['detalhe']};padding-top:26px}}
.fonte{{font:500 28px P;opacity:.85}}
.fonte b{{font-weight:700;opacity:1}}
</style></head><body>
<div class="listra"></div><div class="diag"></div>
<div class="topo"><div class="marca">{e(c['nome_pagina'])}</div>{_chip(c)}</div>
<div style="position:absolute;left:80px;right:80px;top:{topo_titulo}px">
<div class="titulo" style="position:static" data-fit="{110 if story else 96}" data-min="40" data-maxh="{alt_titulo - (150 if c.get('resumo_curto') else 0)}">{e(c['titulo'])}</div>
{f'<div style="font:500 34px/1.35 P;opacity:.9;margin-top:30px">{e(c["resumo_curto"])}</div>' if c.get('resumo_curto') else ''}
</div>
<div class="rodape"><div class="fonte">Fonte: <b>{e(c['fonte'] or 'imprensa')}</b>{(' · ' + e(c['site'])) if c.get('site') else ''}</div>{_siga(c)}</div>
<style>.feed-aviso{{position:absolute;left:0;right:0;bottom:70px;text-align:center;font:700 26px P;letter-spacing:3px;color:#fff;opacity:.9}}</style>
{'<div class="feed-aviso">LEIA A NOTÍCIA COMPLETA NO FEED ↑</div>' if story else ''}
{FIT}</body></html>"""


DESIGNS = {
    "noticia": lambda c: _pagina(c, 1350),
    "story": lambda c: _pagina(c, 1920),
}


def _pagina_foto(c, altura):
    """Arte com foto livre (Wikimedia/Flickr) ao fundo, título, linha fina e créditos."""
    cor = c["cores"]
    story = altura == 1920
    foto = c.get("foto_arquivo", "")
    base = 230 if story else 90
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:D;src:url("../fontes/InterDisplay-Black.otf");font-weight:900}}
@font-face{{font-family:D;src:url("../fontes/InterDisplay-ExtraBold.otf");font-weight:800}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Medium.ttf");font-weight:500}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Bold.ttf");font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:{altura}px;overflow:hidden;background:{cor['fundo']};color:{cor['texto']};font-family:P,sans-serif;position:relative}}
.foto{{position:absolute;left:0;top:0;width:100%;height:{1450 if story else 960}px;object-fit:cover;object-position:center {c.get('foto_foco', '22%')}}}
.sombra{{position:absolute;inset:0;background:
  linear-gradient(180deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,0) 16%),
  linear-gradient(180deg,rgba(0,0,0,0) {48 if story else 38}%,{cor['fundo']} {72 if story else 70}%)}}
.listra{{position:absolute;left:0;top:0;bottom:0;width:18px;background:{cor['detalhe']}}}
.topo{{position:absolute;left:70px;right:60px;top:{110 if story else 56}px;display:flex;justify-content:space-between;align-items:center}}
.marca{{font:900 32px D;letter-spacing:1px;text-transform:uppercase;text-shadow:0 2px 12px rgba(0,0,0,.6)}}
{CSS_COMUM.format(detalhe=cor['detalhe'])}
.bloco{{position:absolute;left:70px;right:70px;bottom:{base}px}}
.time{{display:inline-block;font:700 28px P;letter-spacing:3px;text-transform:uppercase;color:#fff;border-left:8px solid {cor['detalhe']};padding-left:16px;margin-bottom:22px}}
.titulo{{font-family:D;font-weight:900;line-height:1.02;letter-spacing:-1.5px;color:{cor['destaque']};max-height:{560 if story else 330}px}}
.fina{{font:500 33px/1.35 P;margin-top:24px;opacity:.92;max-height:{230 if story else 140}px}}
.rodape{{display:flex;justify-content:space-between;align-items:flex-end;border-top:3px solid {cor['detalhe']};padding-top:20px;margin-top:34px;gap:30px}}
.creditos{{font:500 21px/1.45 P;opacity:.8}}
.creditos b{{font-weight:700}}
</style></head><body>
<img class="foto" src="{e(foto)}">
<div class="sombra"></div><div class="listra"></div>
<div class="topo"><div class="marca">{e(c['nome_pagina'])}</div>{_chip(c)}</div>
<div class="bloco">
  <div class="titulo" data-fit="{104 if story else 84}" data-min="44" data-maxh="{560 if story else 330}">{e(c['titulo'])}</div>
  {f'<div class="fina" data-fit="34" data-min="24" data-maxh="{230 if story else 140}">{e(c["resumo_curto"])}</div>' if c.get('resumo_curto') else ''}
  <div class="rodape"><div class="creditos">Fonte: <b>{e(c['fonte'] or 'imprensa')}</b>{(' · ' + e(c['site'])) if c.get('site') else ''}<br>Foto: <b>{e(c.get('foto_autor', ''))}</b> · {e(c.get('foto_licenca', ''))}</div>{_siga(c)}</div>
</div>
<style>.feed-aviso{{position:absolute;left:0;right:0;bottom:70px;text-align:center;font:700 26px P;letter-spacing:3px;color:#fff;opacity:.9}}</style>
{'<div class="feed-aviso">LEIA A NOTÍCIA COMPLETA NO FEED ↑</div>' if story else ''}
{FIT}</body></html>"""


DESIGNS["noticia_foto"] = lambda c: _pagina_foto(c, 1350)
DESIGNS["story_foto"] = lambda c: _pagina_foto(c, 1920)
