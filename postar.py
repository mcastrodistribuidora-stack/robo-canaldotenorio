#!/usr/bin/env python3
"""
Robô de notícias de futebol: só Instagram.

A cada execução:
  1. busca notícias recentes dos times do config.json (Google Notícias);
  2. pula as que já foram postadas (estado.json);
  3. escreve título/linha fina/legenda com palavras próprias (resumo.py; IA opcional);
  4. procura uma FOTO REAL COM LICENÇA LIVRE do jogador/estádio (fotos.py);
  5. gera a arte com a foto (ou só com texto, se não achar foto) e o story;
  6. publica no Instagram com legenda e créditos do veículo e do fotógrafo.

Uso:
  python postar.py            -> posta
  python postar.py --teste    -> só gera as artes em teste/, sem postar
Secrets: META_PAGE_ID, META_IG_USER_ID, META_PAGE_TOKEN
Opcionais: ANTHROPIC_API_KEY (resumo com IA), FLICKR_API_KEY (busca fotos também no Flickr)
(A página do Facebook só serve para hospedar a imagem por um instante: nada é publicado no Facebook.)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import fotos as fotos_mod
import resumo
from noticias import chave_parecida, escolher, mais_manchetes

PASTA = Path(__file__).resolve().parent
CONFIG = json.loads((PASTA / "config.json").read_text(encoding="utf-8"))
ESTADO = PASTA / "estado.json"


def carregar_estado():
    if ESTADO.exists():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {"postados": [], "fotos_usadas": []}


def salvar_estado(est):
    est["postados"] = est["postados"][-600:]  # guarda só os mais recentes
    est["fotos_usadas"] = est.get("fotos_usadas", [])[-300:]
    est["titulos"] = est.get("titulos", [])[-60:]  # ~3 dias de títulos, para não repetir o mesmo fato
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


def legenda(n, info, foto=None):
    tags = " ".join(CONFIG.get("hashtags", []))
    time_tag = "#" + n["termo"].lower().replace(" ", "")
    site = f" ({n['site']})" if n.get("site") else ""
    partes = [f"⚽ {n['termo'].upper()} | {info['selo']}", info["texto"], f"💬 {info['pergunta']}",
              f"📰 Fonte da informação: {n['fonte'] or 'imprensa'}{site}"]
    if foto:
        partes[-1] += f"\n📸 Foto: {fotos_mod.credito(foto)}"
    redes = CONFIG.get("redes", {})
    if redes:
        partes.append("👉 Siga o " + CONFIG.get("nome_legenda", CONFIG["nome_pagina"]) + ": " +
                      " | ".join(f"{ {'youtube': 'YouTube', 'tiktok': 'TikTok'}.get(k, k.capitalize())} {v}" for k, v in redes.items()))
    else:
        partes.append(f"Siga {CONFIG['arroba']} para mais notícias ⚽")
    partes.append(f"{time_tag} {tags}")
    return "\n\n".join(partes)


def url_github(caminho):
    """Publica a imagem num ramo separado do repositório ('midia', sempre só com a imagem atual,
    para o repositório não crescer) e devolve o link público raw.githubusercontent.com."""
    import requests
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("sem GITHUB_REPOSITORY: a hospedagem pelo GitHub só funciona dentro do GitHub Actions")
    remoto = os.environ.get("MIDIA_REMOTO", f"https://github.com/{repo}.git")
    cabecalho = subprocess.run(["git", "config", "--get", "http.https://github.com/.extraheader"],
                               cwd=PASTA, capture_output=True, text=True).stdout.strip()
    nome = f"{int(time.time())}_{Path(caminho).name}"
    pasta = Path(tempfile.mkdtemp())
    shutil.copy(caminho, pasta / nome)

    def git(*args):
        extra = ["-c", f"http.https://github.com/.extraheader={cabecalho}"] if cabecalho else []
        subprocess.run(["git", *extra, *args], cwd=pasta, check=True, capture_output=True, text=True)

    git("init", "-q")
    git("checkout", "-q", "-b", "midia")
    git("config", "user.name", "robo-noticias")
    git("config", "user.email", "robo-noticias@users.noreply.github.com")
    git("add", nome)
    git("commit", "-q", "-m", "imagem do post")
    git("push", "-q", "-f", remoto, "midia")
    shutil.rmtree(pasta, ignore_errors=True)
    url = f"https://raw.githubusercontent.com/{repo}/midia/{nome}"
    for _ in range(12):  # espera o link ficar no ar (alguns segundos)
        try:
            if requests.head(url, timeout=15).status_code == 200:
                break
        except Exception:
            pass
        time.sleep(5)
    print("   imagem hospedada:", url)
    return url


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
        """Link público da imagem para o Instagram buscar.
        1º tenta pela Página (foto NÃO publicada); se o app não tiver essa permissão, hospeda no GitHub."""
        if not getattr(self, "_pagina_recusou", False):
            try:
                return self._url_pela_pagina(caminho)
            except Exception as ex:
                print("   [aviso] a Página não aceitou hospedar a imagem; usando o GitHub:", str(ex)[:120])
                self._pagina_recusou = True
        return url_github(caminho)

    def _url_pela_pagina(self, caminho):
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
    args = ap.parse_args()

    est = carregar_estado()
    if args.exemplo:
        agora = datetime.now(timezone.utc)
        fila = [{"id": "ex1", "titulo": "Vasco acerta a contratação de reforço para o meio-campo e jogador chega nesta semana",
                 "fonte": "ge", "site": "ge.globo.com", "termo": "Vasco", "quando": agora, "link": ""},
                {"id": "ex2", "titulo": "Palmeiras divulga relacionados para o clássico e tem retorno no ataque",
                 "fonte": "UOL", "site": "uol.com.br", "termo": "Palmeiras", "quando": agora, "link": ""}]
    else:
        fila = escolher(CONFIG, est["postados"], est.get("titulos", []), est.get("ultimo_time"))
    fila = fila[: (len(fila) if args.exemplo else CONFIG.get("max_por_execucao", 1))]
    if not fila:
        print("Nenhuma notícia nova agora.")
        return

    from artes import Renderizador
    meta = None if args.teste else Meta()
    saida = PASTA / ("teste" if args.teste else "saida")
    erro = False
    with Renderizador() as r:
        for i, n in enumerate(fila):
            print(f"• {n['titulo']} ({n['fonte']})")
            num = len(est["postados"]) + (i if args.teste else 0)
            if not args.exemplo:
                try:  # junta manchetes de outros veículos sobre o mesmo fato, para o resumo ficar completo
                    extras = mais_manchetes(n)
                    n["relacionadas"] = list(dict.fromkeys(n.get("relacionadas", []) + extras))
                except Exception as ex:
                    print("  [aviso] não consegui buscar mais manchetes:", ex)
            info = resumo.gerar(n, CONFIG)
            print(f"  texto {'(IA)' if info['por_ia'] else '(plano B)'}: {info['titulo_arte']}")
            if args.exemplo:
                foto = {"id": "exemplo", "arquivo": PASTA / "exemplo" / "foto_provisoria.jpg",
                        "autor": "Nome do Fotógrafo", "origem": "Wikimedia Commons", "licenca": "CC BY-SA 4.0",
                        "licenca_url": "https://creativecommons.org/licenses/by-sa/4.0"}
            else:
                foto = fotos_mod.escolher_foto(info["pessoas"], n, CONFIG, est.get("fotos_usadas", []))
                if foto:
                    try:
                        foto["arquivo"] = fotos_mod.baixar(foto["url"], saida / f"{num}_foto_original.jpg")
                    except Exception as ex:
                        print("  [aviso] não consegui baixar a foto, vai só texto:", ex)
                        foto = None
            campos = {**CONFIG, **n, "titulo": info["titulo_arte"], "resumo_curto": info["linha_fina"],
                      "selo": info["selo"]}
            if foto:
                campos.update(foto_arquivo=Path(foto["arquivo"]).resolve().as_uri(),
                              foto_autor=f"{foto['autor']} / {foto['origem']}",
                              foto_licenca=f"{foto['licenca']} (editada)")
                d_feed, d_story = "noticia_foto", "story_foto"
            else:
                d_feed, d_story = "noticia", "story"
            feed = r.gerar(d_feed, campos, saida / f"{num}_feed.jpg")
            story = r.gerar(d_story, campos, saida / f"{num}_story.jpg") if CONFIG.get("postar_story") else None
            texto = legenda(n, info, foto)
            if args.teste:
                (saida / f"{num}_legenda.txt").write_text(texto, encoding="utf-8")
                print("   artes:", feed.name, story.name if story else "", f"| legenda: {num}_legenda.txt")
                continue
            try:
                print("   ✔ feed", meta.publicar(feed, texto))
                if story:  # story automático logo depois do feed (tenta 2 vezes)
                    for tentativa in (1, 2):
                        try:
                            print("   ✔ story", meta.publicar(story, story=True))
                            break
                        except Exception as ex:
                            print(f"   ✖ story (tentativa {tentativa}):", ex)
                            time.sleep(20)
                est["postados"] += [n["id"], chave_parecida(n["titulo"])]
                est.setdefault("titulos", []).append(n["titulo"])
                est["ultimo_time"] = n["termo"]
                if foto:
                    est.setdefault("fotos_usadas", []).append(foto["id"])
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
