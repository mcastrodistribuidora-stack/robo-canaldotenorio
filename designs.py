"""Designs das artes (HTML -> imagem pelo artes.py). Cores e nome vêm do config.json.

- noticia / story ............ notícia só com texto (modelo limpo, Cruz de Malta como marca d'água)
- noticia_foto / story_foto .. notícia com foto livre (Wikimedia/Flickr) ao fundo
- estatistica / estatistica_story .. posts de estatística (dados do NETVASCO) com pergunta ao torcedor
"""
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
CRUZ = (PASTA / "assets" / "cruz.png").as_uri()

FONTES = """
@font-face{{font-family:D;src:url("../fontes/InterDisplay-Black.otf");font-weight:900}}
@font-face{{font-family:D;src:url("../fontes/InterDisplay-ExtraBold.otf");font-weight:800}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Regular.ttf");font-weight:400}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Medium.ttf");font-weight:500}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Bold.ttf");font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
"""


def _chip(c):
    """Selo duplo: nome do time + assunto (ex.: VASCO | MERCADO DA BOLA)."""
    time_ = c.get("termo", "")
    selo = c.get("selo", "Notícia")
    tam = 24 if len(time_) + len(selo) <= 22 else 20
    return (f'<div class="chip" style="font-size:{tam}px">'
            f'<span class="chip-time">{e(time_)}</span><span class="chip-selo">{e(selo)}</span></div>')


def _marca(c):
    """Nome da página com a Cruz de Malta ao lado."""
    return f'<div class="marca"><img src="{CRUZ}">{e(c["nome_pagina"])}</div>'


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
.marca{{display:flex;align-items:center;gap:16px;font:900 32px D;letter-spacing:1px;text-transform:uppercase;text-shadow:0 2px 12px rgba(0,0,0,.5)}}
.marca img{{width:46px;height:46px;filter:drop-shadow(0 2px 6px rgba(0,0,0,.5))}}
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
.cruz-fundo{{position:absolute;width:640px;opacity:.06;pointer-events:none}}
"""


def _pagina(c, altura):
    """Notícia só com texto: limpa, manchete grande, Cruz de Malta discreta no fundo."""
    cor = c["cores"]
    story = altura == 1920
    topo_titulo = 330 if story else 250
    alt_titulo = 900 if story else 700
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{FONTES.format()}
body{{width:1080px;height:{altura}px;overflow:hidden;background:{cor['fundo']};color:{cor['texto']};font-family:P,sans-serif;position:relative}}
.topo{{position:absolute;left:80px;right:70px;top:{110 if story else 70}px;display:flex;justify-content:space-between;align-items:center}}
{CSS_COMUM.format(detalhe=cor['detalhe'])}
.traco{{width:72px;height:8px;background:{cor['detalhe']};margin-bottom:40px}}
.titulo{{font-family:D;font-weight:800;line-height:1.06;letter-spacing:-1.5px;color:{cor['destaque']};text-wrap:balance}}
.rodape{{position:absolute;left:80px;right:80px;bottom:{150 if story else 70}px;display:flex;justify-content:space-between;align-items:flex-end;
        border-top:1px solid rgba(255,255,255,.2);padding-top:26px}}
.fonte{{font:500 26px P;opacity:.8}}
.fonte b{{font-weight:700;opacity:1}}
</style></head><body>
<img class="cruz-fundo" src="{CRUZ}" style="right:-170px;bottom:{-120 if story else -170}px">
<div class="topo">{_marca(c)}{_chip(c)}</div>
<div style="position:absolute;left:80px;right:80px;top:{topo_titulo}px">
<div class="traco"></div>
<div class="titulo" data-fit="{106 if story else 92}" data-min="40" data-maxh="{alt_titulo - (150 if c.get('resumo_curto') else 0)}">{e(c['titulo'])}</div>
{f'<div style="font:500 34px/1.35 P;opacity:.85;margin-top:30px">{e(c["resumo_curto"])}</div>' if c.get('resumo_curto') else ''}
</div>
<div class="rodape"><div class="fonte">Fonte: <b>{e(c['fonte'] or 'imprensa')}</b>{(' · ' + e(c['site'])) if c.get('site') else ''}</div>{_siga(c)}</div>
<style>.feed-aviso{{position:absolute;left:0;right:0;bottom:70px;text-align:center;font:700 26px P;letter-spacing:3px;color:#fff;opacity:.9}}</style>
{'<div class="feed-aviso">LEIA A NOTÍCIA COMPLETA NO FEED ↑</div>' if story else ''}
{FIT}</body></html>"""


def _pagina_foto(c, altura):
    """Arte com foto livre (Wikimedia/Flickr) ao fundo, título, linha fina e créditos."""
    cor = c["cores"]
    story = altura == 1920
    foto = c.get("foto_arquivo", "")
    base = 230 if story else 90
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{FONTES.format()}
body{{width:1080px;height:{altura}px;overflow:hidden;background:{cor['fundo']};color:{cor['texto']};font-family:P,sans-serif;position:relative}}
.foto{{position:absolute;left:0;top:0;width:100%;height:{1450 if story else 960}px;object-fit:cover;object-position:center {c.get('foto_foco', '22%')}}}
.sombra{{position:absolute;inset:0;background:
  linear-gradient(180deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,0) 16%),
  linear-gradient(180deg,rgba(0,0,0,0) {48 if story else 38}%,{cor['fundo']} {72 if story else 70}%)}}
.topo{{position:absolute;left:70px;right:60px;top:{110 if story else 56}px;display:flex;justify-content:space-between;align-items:center}}
{CSS_COMUM.format(detalhe=cor['detalhe'])}
.bloco{{position:absolute;left:70px;right:70px;bottom:{base}px}}
.traco{{width:72px;height:8px;background:{cor['detalhe']};margin-bottom:28px}}
.titulo{{font-family:D;font-weight:800;line-height:1.04;letter-spacing:-1.5px;color:{cor['destaque']};max-height:{560 if story else 330}px;text-wrap:balance}}
.fina{{font:500 33px/1.35 P;margin-top:24px;opacity:.9;max-height:{230 if story else 140}px}}
.rodape{{display:flex;justify-content:space-between;align-items:flex-end;border-top:1px solid rgba(255,255,255,.25);padding-top:20px;margin-top:34px;gap:30px}}
.creditos{{font:500 21px/1.45 P;opacity:.8}}
.creditos b{{font-weight:700}}
</style></head><body>
<img class="foto" src="{e(foto)}">
<div class="sombra"></div>
<div class="topo">{_marca(c)}{_chip(c)}</div>
<div class="bloco">
  <div class="traco"></div>
  <div class="titulo" data-fit="{104 if story else 84}" data-min="44" data-maxh="{560 if story else 330}">{e(c['titulo'])}</div>
  {f'<div class="fina" data-fit="34" data-min="24" data-maxh="{230 if story else 140}">{e(c["resumo_curto"])}</div>' if c.get('resumo_curto') else ''}
  <div class="rodape"><div class="creditos">Fonte: <b>{e(c['fonte'] or 'imprensa')}</b>{(' · ' + e(c['site'])) if c.get('site') else ''}<br>Foto: <b>{e(c.get('foto_autor', ''))}</b> · {e(c.get('foto_licenca', ''))}</div>{_siga(c)}</div>
</div>
<style>.feed-aviso{{position:absolute;left:0;right:0;bottom:70px;text-align:center;font:700 26px P;letter-spacing:3px;color:#fff;opacity:.9}}</style>
{'<div class="feed-aviso">LEIA A NOTÍCIA COMPLETA NO FEED ↑</div>' if story else ''}
{FIT}</body></html>"""


def _estat(c, altura):
    """Post de estatística: comparativo (colunas por temporada) ou ranking (barras), com pergunta ao torcedor."""
    cor = c["cores"]
    suave = cor.get("suave", "#9A9A9A")
    story = altura == 1920
    if c["tipo"] == "comparativo":
        maior = max(col["grande"] for col in c["colunas"])
        miolo = '<div class="cols">' + "".join(
            f'''<div class="col{' top' if col['grande'] == maior else ''}"><div class="ano">{col['ano']}</div>
            <div class="num">{col['grande']}{'%' if col.get('pct') else ''}</div><div class="rot">{e(col['rotulo'])}</div>
            <div class="lin">{''.join(f'<p>{e(str(l))}</p>' for l in col['linhas'])}</div></div>''' for col in c["colunas"]) + "</div>"
    else:
        maior = max(i["valor"] for i in c["itens"]) or 1
        miolo = '<div class="rank">' + "".join(
            f'''<div class="item"><div class="pos">{k + 1}</div><div class="info"><div class="nome">{e(i['nome'])}<span>{e(i['extra'])}</span></div>
            <div class="barra"><i style="width:{max(6, 100 * i['valor'] / maior):.0f}%"></i></div></div>
            <div class="val">{i['valor']}<small>{e(c['unidade'])}</small></div></div>''' for k, i in enumerate(c["itens"])) + "</div>"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{FONTES.format()}
body{{position:relative;width:1080px;height:{altura}px;overflow:hidden;background:{cor['fundo']};color:{cor['texto']};font-family:P,sans-serif;
     display:flex;flex-direction:column;padding:{150 if story else 70}px 80px}}
{CSS_COMUM.format(detalhe=cor['detalhe'])}
.topo{{display:flex;justify-content:space-between;align-items:center}}
.topo,h1,.meio,.pergunta,.base{{position:relative}}
h1{{margin-top:{90 if story else 52}px;font:800 66px/1.06 D;letter-spacing:-1px;text-wrap:balance}}
.meio{{flex:1;display:flex;flex-direction:column;justify-content:center}}
.cols{{display:grid;grid-template-columns:repeat({len(c.get('colunas', [])) or 1},1fr);gap:22px}}
.col{{border:1px solid rgba(255,255,255,.16);padding:34px 26px;display:flex;flex-direction:column;gap:6px}}
.col.top{{border-color:{cor['detalhe']};background:rgba(210,31,43,.08)}}
.ano{{font:700 26px P;color:{suave};letter-spacing:3px}}
.num{{font:900 {150 if story else 128}px/1 D;letter-spacing:-4px;margin-top:10px}}
.rot{{font:500 24px P;color:{suave};text-transform:uppercase;letter-spacing:2px}}
.lin{{margin-top:22px;border-top:1px solid rgba(255,255,255,.12);padding-top:18px;font:400 25px/1.6 P;color:#d6d6d6}}
.rank{{display:flex;flex-direction:column;gap:{34 if story else 26}px}}
.item{{display:grid;grid-template-columns:56px 1fr 150px;align-items:center;gap:20px}}
.pos{{font:900 44px D;color:{suave}}}
.item:first-child .pos{{color:{cor['detalhe']}}}
.nome{{font:700 34px P;display:flex;justify-content:space-between;align-items:baseline}}
.nome span{{font:400 22px P;color:{suave}}}
.barra{{height:12px;background:rgba(255,255,255,.1);margin-top:12px}} .barra i{{display:block;height:100%;background:#fff}}
.item:first-child .barra i{{background:{cor['detalhe']}}}
.val{{font:900 62px/1 D;text-align:right}} .val small{{display:block;font:500 18px P;color:{suave};letter-spacing:1px;margin-top:6px}}
.pergunta{{margin-top:{70 if story else 40}px;font:800 44px/1.15 D;display:flex;gap:22px;align-items:flex-start}}
.pergunta:before{{content:"";flex:none;width:10px;align-self:stretch;background:{cor['detalhe']}}}
.base{{margin-top:{60 if story else 34}px;display:flex;justify-content:space-between;align-items:flex-end;font:500 24px P;color:{suave};
      border-top:1px solid rgba(255,255,255,.2);padding-top:22px}}
.base b{{color:{cor['texto']};font-weight:700}} .base .siga{{color:{cor['texto']}}}
</style></head><body>
<img class="cruz-fundo" src="{CRUZ}" style="right:-190px;top:-190px;width:560px">
<div class="topo">{_marca(c)}<div class="chip" style="font-size:22px"><span class="chip-time">Vasco</span><span class="chip-selo">{e(c['selo'])}</span></div></div>
<h1>{e(c['titulo'])}</h1>
<div class="meio">{miolo}</div>
<div class="pergunta">{e(c['pergunta'])}</div>
<div class="base"><div>Dados: <b>NETVASCO</b></div>{_siga(c)}</div>
<script>document.fonts.ready.then(()=>{{window.problemas=document.body.scrollHeight>{altura}+2?['estourou']:[];window.pronto=true}})</script>
</body></html>"""


DESIGNS = {
    "noticia": lambda c: _pagina(c, 1350),
    "story": lambda c: _pagina(c, 1920),
    "noticia_foto": lambda c: _pagina_foto(c, 1350),
    "story_foto": lambda c: _pagina_foto(c, 1920),
    "estatistica": lambda c: _estat(c, 1350),
    "estatistica_story": lambda c: _estat(c, 1920),
}
