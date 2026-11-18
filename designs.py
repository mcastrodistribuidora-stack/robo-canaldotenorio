"""Arte de notícia limpa: fundo escuro, manchete grande, crédito discreto. Cores e nome no config.json."""
import html

e = html.escape
MESES = "JAN FEV MAR ABR MAI JUN JUL AGO SET OUT NOV DEZ".split()

FIT = """<script>
document.fonts.ready.then(() => {
  window.problemas = [];
  document.querySelectorAll('[data-fit]').forEach(el => {
    let t = +el.dataset.fit, min = +(el.dataset.min || 40), maxH = +el.dataset.maxh;
    el.style.fontSize = t + 'px';
    while (t > min && el.scrollHeight > maxH) { t -= 2; el.style.fontSize = t + 'px'; }
    if (el.scrollHeight > maxH) window.problemas.push('manchete grande demais');
  });
  window.pronto = true;
});
</script>"""


CRUZ = "../assets/cruz.png"


def _pagina(c, altura):
    cor = c["cores"]
    story = altura == 1920
    q = c.get("quando")
    data = f"{q.day:02d} {MESES[q.month - 1]} {q.year}" if q else ""
    mv = 150 if story else 90
    foto = c.get("foto")
    if foto:  # foto em cima, manchete embaixo
        alt_foto = 1060 if story else 700
        bloco = f"""<div class="foto" style="height:{alt_foto}px;background-image:url('{foto}')"></div>
<div class="sombra" style="top:{alt_foto - 240}px"></div>
<div class="credito" style="top:{alt_foto - 34}px">{e(c.get('credito_foto', ''))}</div>"""
        meio = f'''<div class="meio comfoto" style="padding-top:{alt_foto - mv - 10}px"><div class="traco"></div>
  <div class="titulo" data-fit="{88 if story else 72}" data-min="40" data-maxh="{520 if story else 300}">{e(c['titulo'])}</div></div>'''
        marca = ""
    else:
        bloco = ""
        meio = f'''<div class="meio"><div class="traco"></div>
  <div class="titulo" data-fit="{104 if story else 92}" data-min="44" data-maxh="{1100 if story else 760}">{e(c['titulo'])}</div></div>'''
        marca = '<img class="marca" src="' + CRUZ + '">'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:D;src:url("../fontes/InterDisplay-ExtraBold.otf");font-weight:800}}
@font-face{{font-family:D;src:url("../fontes/InterDisplay-Black.otf");font-weight:900}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Regular.ttf");font-weight:400}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Medium.ttf");font-weight:500}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Bold.ttf");font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{position:relative;width:1080px;height:{altura}px;overflow:hidden;background:{cor['fundo']};color:{cor['texto']};font-family:P,sans-serif;
     display:flex;flex-direction:column;padding:{mv}px 90px}}
.foto{{position:absolute;left:0;top:0;width:1080px;background-size:cover;background-position:center 30%}}
.sombra{{position:absolute;left:0;right:0;height:250px;background:linear-gradient(rgba(10,10,10,0),{cor['fundo']})}}
.foto:before{{content:"";position:absolute;left:0;right:0;top:0;height:220px;background:linear-gradient(rgba(0,0,0,.55),rgba(0,0,0,0))}}
.credito{{position:absolute;right:30px;font:400 17px P;color:rgba(255,255,255,.75);text-shadow:0 1px 3px #000;max-width:760px;text-align:right;
         white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.marca{{position:absolute;right:-150px;bottom:-150px;width:620px;opacity:.07}}
.topo,.meio,.base{{position:relative}}
.topo{{display:flex;justify-content:space-between;align-items:center;font:700 26px P;letter-spacing:5px;text-transform:uppercase;text-shadow:0 1px 8px rgba(0,0,0,.6)}}
.topo .nome{{display:flex;align-items:center;gap:16px}} .topo img{{width:40px;height:40px}}
.topo span{{color:{cor['suave']};font-weight:500;letter-spacing:3px}}
.comfoto ~ .base, .comfoto{{}} .foto ~ .topo span{{color:#fff}}
.meio{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:44px}}
.meio.comfoto{{justify-content:flex-start;gap:30px}}
.traco{{width:72px;height:8px;background:{cor['detalhe']}}}
.titulo{{font-family:D;font-weight:800;line-height:1.08;letter-spacing:-1.5px;text-wrap:balance}}
.base{{display:flex;justify-content:space-between;align-items:center;font:400 26px P;color:{cor['suave']};
      border-top:1px solid rgba(255,255,255,.18);padding-top:30px}}
.base b{{color:{cor['texto']};font-weight:700}}
.canal{{text-align:right;line-height:1.25}} .canal small{{display:block;font-size:19px;letter-spacing:1px}}
</style></head><body>
{bloco}{marca}
<div class="topo"><div class="nome"><img src="{CRUZ}">{e(c['nome_pagina'])}</div><span>{data}</span></div>
{meio}
<div class="base"><div>Fonte: <b>{e(c['fonte'])}</b></div><div class="canal"><b>{e(c['arroba'])}</b><small>{e(c.get('redes',''))}</small></div></div>
{FIT}</body></html>"""


def _estat(c, altura):
    cor = c["cores"]
    story = altura == 1920
    if c["tipo"] == "comparativo":
        n = len(c["colunas"])
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
@font-face{{font-family:D;src:url("../fontes/InterDisplay-ExtraBold.otf");font-weight:800}}
@font-face{{font-family:D;src:url("../fontes/InterDisplay-Black.otf");font-weight:900}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Regular.ttf");font-weight:400}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Medium.ttf");font-weight:500}}
@font-face{{font-family:P;src:url("../fontes/Poppins-Bold.ttf");font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:{altura}px;overflow:hidden;background:{cor['fundo']};color:{cor['texto']};font-family:P,sans-serif;
     display:flex;flex-direction:column;padding:{150 if story else 80}px 80px}}
.topo{{display:flex;justify-content:space-between;align-items:center;font:700 26px P;letter-spacing:5px;text-transform:uppercase}}
.topo span{{color:{cor['detalhe']};letter-spacing:4px}}
.topo .nome{{display:flex;align-items:center;gap:16px}} .topo img{{width:40px;height:40px}}
body{{position:relative}} .marca{{position:absolute;right:-170px;top:-170px;width:560px;opacity:.06}}
.topo,h1,.meio,.pergunta,.base{{position:relative}}
h1{{margin-top:{90 if story else 56}px;font:800 66px/1.06 D;letter-spacing:-1px;text-wrap:balance}}
.meio{{flex:1;display:flex;flex-direction:column;justify-content:center}}
.cols{{display:grid;grid-template-columns:repeat({len(c.get('colunas', [])) or 1},1fr);gap:22px}}
.col{{border:1px solid rgba(255,255,255,.16);padding:34px 26px;display:flex;flex-direction:column;gap:6px}}
.col.top{{border-color:{cor['detalhe']};background:rgba(210,31,43,.08)}}
.ano{{font:700 26px P;color:{cor['suave']};letter-spacing:3px}}
.num{{font:900 {150 if story else 128}px/1 D;letter-spacing:-4px;margin-top:10px}}
.rot{{font:500 24px P;color:{cor['suave']};text-transform:uppercase;letter-spacing:2px}}
.lin{{margin-top:22px;border-top:1px solid rgba(255,255,255,.12);padding-top:18px;font:400 25px/1.6 P;color:#d6d6d6}}
.rank{{display:flex;flex-direction:column;gap:{34 if story else 26}px}}
.item{{display:grid;grid-template-columns:56px 1fr 150px;align-items:center;gap:20px}}
.pos{{font:900 44px D;color:{cor['suave']}}}
.item:first-child .pos{{color:{cor['detalhe']}}}
.nome{{font:700 34px P;display:flex;justify-content:space-between;align-items:baseline}}
.nome span{{font:400 22px P;color:{cor['suave']}}}
.barra{{height:12px;background:rgba(255,255,255,.1);margin-top:12px}} .barra i{{display:block;height:100%;background:#fff}}
.item:first-child .barra i{{background:{cor['detalhe']}}}
.val{{font:900 62px/1 D;text-align:right}} .val small{{display:block;font:500 18px P;color:{cor['suave']};letter-spacing:1px;margin-top:6px}}
.pergunta{{margin-top:{70 if story else 44}px;font:800 44px/1.15 D;display:flex;gap:22px;align-items:flex-start}}
.pergunta:before{{content:"";flex:none;width:10px;align-self:stretch;background:{cor['detalhe']}}}
.base{{margin-top:{60 if story else 40}px;display:flex;justify-content:space-between;align-items:center;font:400 24px P;color:{cor['suave']};
      border-top:1px solid rgba(255,255,255,.18);padding-top:26px}}
.base b{{color:{cor['texto']};font-weight:700}} .canal{{text-align:right;line-height:1.25}} .canal small{{display:block;font-size:19px;letter-spacing:1px}}
</style></head><body>
<img class="marca" src="{CRUZ}">
<div class="topo"><div class="nome"><img src="{CRUZ}">{e(c['nome_pagina'])}</div><span>{e(c['selo'])}</span></div>
<h1>{e(c['titulo'])}</h1>
<div class="meio">{miolo}</div>
<div class="pergunta">{e(c['pergunta'])}</div>
<div class="base"><div>Dados: <b>NETVASCO</b></div><div class="canal"><b>{e(c['arroba'])}</b><small>{e(c.get('redes',''))}</small></div></div>
<script>document.fonts.ready.then(()=>{{window.problemas=document.body.scrollHeight>{altura}+2?['estourou']:[];window.pronto=true}})</script>
</body></html>"""


DESIGNS = {"noticia": lambda c: _pagina(c, 1350), "story": lambda c: _pagina(c, 1920),
           "estatistica": lambda c: _estat(c, 1350), "estatistica_story": lambda c: _estat(c, 1920)}
