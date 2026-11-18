#!/usr/bin/env python3
"""
Robô de notícias de futebol: só Instagram.

A cada execução:
  1. busca notícias recentes dos times do config.json (Google Notícias);
  2. pula as que já foram postadas (estado.json);
  3. gera a arte (1080x1350) e, se ligado, o story (1080x1920);
  4. publica no Instagram com legenda e crédito do veículo.

Uso:
  python postar.py            -> posta
  python postar.py --teste    -> só gera as artes em teste/, sem postar
Secrets: META_PAGE_ID, META_IG_USER_ID, META_PAGE_TOKEN
(A página do Facebook só serve para hospedar a imagem por um instante: nada é publicado no Facebook.)
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

from noticias import escolher

PASTA = Path(__file__).resolve().parent
CONFIG = json.loads((PASTA / "config.json").read_text(encoding="utf-8"))
ESTADO = PASTA / "estado.json"
FUSO = ZoneInfo("America/Sao_Paulo")


def carregar_estado():
    if ESTADO.exists():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {"ids": [], "palavras": []}


def salvar_estado(est):
    est["ids"] = est["ids"][-800:]          # guarda só os mais recentes
    est["palavras"] = est["palavras"][-400:]
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


def _rodape():
    tags = " ".join(CONFIG.get("hashtags", []))
    return (f"Siga {CONFIG['arroba']} no YouTube, Instagram e TikTok e fique por dentro de tudo do Vasco 💢\n\n{tags}")


def legenda(n):
    foto = f"\n📷 {n['credito_foto']}" if n.get("credito_foto") else ""
    return f"{n['titulo']}\n\n📰 Fonte: {n['fonte']}{foto}\n\n{_rodape()}"


def legenda_estat(p):
    return f"{p['titulo']} 📊\n\n{p['pergunta']} Comenta aqui 👇\n\n📊 Dados: NETVASCO\n\n{_rodape()}"


def hora_de_estatistica(agora):
    return agora.hour in CONFIG.get("horas_estatistica", [12, 19])


def escolher_estatistica(est, exemplo=False):
    """Um post de estatística que não saiu nos últimos dias (os números mudam a cada rodada)."""
    from datetime import date
    if exemplo:
        sys.path.insert(0, str(PASTA / "dados"))
        from netvasco_sim import dados as sim
        dados = sim()
    else:
        import estatisticas
        anos = CONFIG.get("temporadas_estatistica", [])
        dados = {}
        for a in anos:
            try:
                dados[a] = estatisticas.temporada(a)
            except Exception as ex:
                print(f"  [aviso] estatísticas {a}: {ex}")
        if len(dados) < 2:
            return None
    from estatisticas import ideias
    feitos = est.setdefault("estat", {})
    hoje = date.today()
    intervalo = CONFIG.get("dias_entre_repeticoes", 10)
    for p in sorted(ideias(dados), key=lambda p: feitos.get(p["id"], "0000")):
        ultima = feitos.get(p["id"])
        if not ultima or (hoje - date.fromisoformat(ultima)).days >= intervalo:
            return p
    return None


class Meta:
    def __init__(self):
        import requests
        self.rq = requests
        self.base = f"https://graph.facebook.com/{os.environ.get('GRAPH_VERSION', 'v27.0')}"
        self.page = os.environ["META_PAGE_ID"]
        self.ig = os.environ["META_IG_USER_ID"]
        self.token = os.environ["META_PAGE_TOKEN"]

    def _ok(self, r):
        try:
            d = r.json()
        except ValueError:
            raise RuntimeError(f"resposta inesperada ({r.status_code}): {r.text[:200]}")
        if isinstance(d, dict) and "error" in d:
            raise RuntimeError(d["error"].get("message", str(d["error"])))
        return d

    def url_publica(self, caminho):
        """Sobe a foto NÃO publicada na página do Facebook só para ter um link público para o Instagram."""
        with open(caminho, "rb") as f:
            r = self.rq.post(f"{self.base}/{self.page}/photos", data={"published": "false", "access_token": self.token},
                             files={"source": (Path(caminho).name, f, "image/jpeg")}, timeout=120)
        pid = self._ok(r)["id"]
        r = self.rq.get(f"{self.base}/{pid}", params={"fields": "images", "access_token": self.token}, timeout=30)
        return max(self._ok(r)["images"], key=lambda i: i["width"])["source"]

    def _esperar(self, cid):
        for _ in range(40):
            s = self._ok(self.rq.get(f"{self.base}/{cid}", params={"fields": "status_code", "access_token": self.token}, timeout=30))
            if s.get("status_code") == "FINISHED":
                return
            if s.get("status_code") in ("ERROR", "EXPIRED"):
                raise RuntimeError(f"Instagram recusou a mídia ({s.get('status_code')}).")
            time.sleep(3)
        raise RuntimeError("Instagram demorou demais para processar a mídia.")

    def publicar(self, caminho, texto=None, story=False):
        dados = {"image_url": self.url_publica(caminho), "access_token": self.token}
        if story:
            dados["media_type"] = "STORIES"
        else:
            dados["caption"] = texto
        cid = self._ok(self.rq.post(f"{self.base}/{self.ig}/media", data=dados, timeout=60))["id"]
        self._esperar(cid)
        return self._ok(self.rq.post(f"{self.base}/{self.ig}/media_publish",
                                     data={"creation_id": cid, "access_token": self.token}, timeout=60))["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teste", action="store_true")
    ap.add_argument("--exemplo", action="store_true", help="usa notícias de exemplo (sem internet)")
    ap.add_argument("--estatistica", action="store_true", help="força um post de estatística agora")
    args = ap.parse_args()

    est = carregar_estado()
    agora_br = datetime.now(FUSO)
    from artes import Renderizador
    meta = None if args.teste else Meta()
    saida = PASTA / ("teste" if args.teste else "saida")

    # ---------- horário de ESTATÍSTICA (12h e 19h por padrão)
    if args.estatistica or (not args.exemplo and hora_de_estatistica(agora_br)):
        p = escolher_estatistica(est, exemplo=args.exemplo)
        if p:
            with Renderizador() as r:
                campos = {**CONFIG, **p}
                print(f"• estatística: {p['titulo']}")
                feed = r.gerar("estatistica", campos, saida / "estat_feed.jpg")
                story = r.gerar("estatistica_story", campos, saida / "estat_story.jpg") if CONFIG.get("postar_story") else None
                if args.teste:
                    print("   artes:", feed.name, story.name if story else "")
                    return
                print("   ✔ feed", meta.publicar(feed, legenda_estat(p)))
                if story:
                    try:
                        print("   ✔ story", meta.publicar(story, story=True))
                    except Exception as ex:
                        print("   ✖ story:", ex)
                est["estat"][p["id"]] = agora_br.date().isoformat()
                salvar_estado(est)
            return
        print("Sem estatística nova; segue com notícia.")

    # ---------- NOTÍCIA
    if args.exemplo:
        agora = datetime.now(timezone.utc)
        fila = [{"id": "ex1", "titulo": "Vasco acerta compra de Robert Renan e traça plano para zagueiro chegar à Seleção Brasileira",
                 "fonte": "NETVASCO", "quando": agora, "link": "", "palavras": []}]
    else:
        fila = escolher(CONFIG, est)
    fila = fila[: CONFIG.get("max_por_execucao", 1)]
    if not fila:
        print("Nenhuma notícia nova agora.")
        return

    import fotos
    erro = False
    with Renderizador() as r:
        for k, n in enumerate(fila):
            print(f"• {n['titulo']} ({n['fonte']})")
            if CONFIG.get("usar_fotos", True) and not args.exemplo:
                arq = saida / f"foto_{k}.jpg"
                cred = fotos.baixar_foto(n["titulo"], arq)
                if cred:
                    n["foto"], n["credito_foto"] = arq.resolve().as_uri(), cred
                    print("   📷", cred)
            campos = {**CONFIG, **n}
            feed = r.gerar("noticia", campos, saida / f"{k}_feed.jpg")
            story = r.gerar("story", campos, saida / f"{k}_story.jpg") if CONFIG.get("postar_story") else None
            if args.teste:
                print("   artes:", feed.name, story.name if story else "")
                continue
            try:
                print("   ✔ feed", meta.publicar(feed, legenda(n)))
                if story:
                    try:
                        print("   ✔ story", meta.publicar(story, story=True))
                    except Exception as ex:
                        print("   ✖ story:", ex)
                est["ids"].append(n["id"])
                est["palavras"].append(n["palavras"])
                salvar_estado(est)
            except Exception as ex:
                print("   ✖ feed:", ex)
                erro = True
            time.sleep(10)
        if r.problemas:
            print("Aviso de layout:", r.problemas)
    if erro:
        sys.exit("Houve erro ao postar (veja acima).")


if __name__ == "__main__":
    main()
