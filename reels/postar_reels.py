#!/usr/bin/env python3
"""
Robô de REELS do Canal do Tenório: edita e posta os vídeos de reação no Instagram.

Como usar: coloque na pasta reels/entrada/
  - o vídeo do lance/notícia (.mp4 ou .mov), por exemplo  abel.mp4
  - um arquivo de texto com o MESMO nome e o título,     abel.txt
(Se não houver .txt, o título é o nome do arquivo.)

Para cada vídeo, o robô:
  1. monta o Reels 9:16 no modelo de reação (editor.py: seu vídeo base + lance no topo + título);
  2. ouve o áudio do lance (IA Gemini, secret GEMINI_API_KEY) e escreve a legenda: o que foi dito,
     com palavras próprias, uma pergunta para os torcedores comentarem e o convite para seguir o canal;
  3. posta como Reels no Instagram (também aparece no feed) e apaga o vídeo da entrada;
  4. registra em reels/postados.json.

Uso:  python reels/postar_reels.py            -> edita e posta
      python reels/postar_reels.py --teste    -> só edita e escreve a legenda (em reels/saida/), sem postar
Secrets: META_IG_USER_ID, META_PAGE_TOKEN, META_PAGE_ID; GEMINI_API_KEY (legenda pelo áudio).
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parent
ENTRADA = PASTA / "entrada"
SAIDA = PASTA / "saida"
LOG = PASTA / "postados.json"
sys.path.insert(0, str(PASTA))
import editor  # noqa: E402

CONFIG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8")) if (RAIZ / "config.json").exists() else {}
CANAL = CONFIG.get("nome_legenda", "Canal do Tenório")
ARROBA = CONFIG.get("arroba", "@canaldotenorio")
HASHTAGS = "#futebol #futebolbrasileiro #canaldotenorio #reels"
GRAPH = f"https://graph.facebook.com/{os.environ.get('GRAPH_VERSION', 'v27.0')}"

PROMPT = """Você escreve a legenda de um Reels do Instagram do "{canal}" ({arroba}), um canal de um torcedor
que grava vídeos reagindo a notícias de futebol. O áudio anexado é o do vídeo da notícia/entrevista.
Título do vídeo: "{titulo}"

1. Ouça o áudio e entenda o que foi dito, QUEM falou e de QUAL time ele é / sobre qual time falou.
   ATENÇÃO: o canal comenta futebol em geral. Fale SÓ dos times e pessoas que aparecem no áudio ou no título.
   NUNCA cite um time que não foi mencionado (não presuma que o assunto é o Vasco).
2. Escreva a legenda em português do Brasil, com palavras próprias (não transcreva o áudio inteiro):
   - 1ª linha: uma chamada forte sobre o assunto, com o time certo (pode usar 1 emoji);
   - um parágrafo curto (2 a 4 frases) contando o que a pessoa falou, atribuindo a fala a ela
     ("disse que...", "afirmou que..."). Use o nome que aparece no título. Use SÓ o que foi dito no áudio:
     não invente números, datas nem declarações;
   - uma pergunta direta para os torcedores darem a opinião nos comentários, ligada ao que foi dito
     (ex.: "E aí, você concorda com ele? Comenta aí 👇");
   - um convite para seguir: "Siga o {canal} ({arroba}) no Instagram, YouTube e TikTok ⚽";
   - no fim, estas hashtags: {hashtags}, mais 3 ou 4 hashtags do assunto (SÓ os times e pessoas citados no vídeo)
3. Tom de conversa de torcedor, sem ofender ninguém. Máximo de 1.500 caracteres.

Responda SÓ com um JSON: {{"o_que_foi_dito": "resumo do áudio em 1 frase", "legenda": "a legenda completa"}}"""


def legenda_reserva(titulo):
    return (f"🔥 {titulo}\n\nAssiste até o fim e me fala: você concorda? Comenta aí 👇\n\n"
            f"Siga o {CANAL} ({ARROBA}) no Instagram, YouTube e TikTok ⚽\n\n{HASHTAGS}")


def legenda_por_audio(lance, titulo):
    """Extrai o áudio do lance e pede à IA (Gemini) a legenda baseada no que foi falado."""
    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        print("  [aviso] sem GEMINI_API_KEY: legenda padrão")
        return legenda_reserva(titulo), ""
    import requests
    mp3 = SAIDA / "audio_lance.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(lance), "-vn", "-ac", "1", "-ar", "16000",
                    "-b:a", "32k", str(mp3)], check=True)
    audio = base64.b64encode(mp3.read_bytes()).decode()
    prompt = PROMPT.format(canal=CANAL, arroba=ARROBA, titulo=titulo, hashtags=HASHTAGS)
    for modelo in ("gemini-flash-latest", "gemini-flash-lite-latest"):
        for tentativa in (1, 2, 3):
            try:
                r = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                    headers={"x-goog-api-key": chave, "content-type": "application/json"},
                    json={"contents": [{"parts": [{"inline_data": {"mime_type": "audio/mp3", "data": audio}},
                                                  {"text": prompt}]}],
                          "generationConfig": {"temperature": 0.5, "responseMimeType": "application/json"}},
                    timeout=180)
                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code} {r.text[:200]}")
                txt = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])
                d = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
                leg = str(d.get("legenda", "")).strip()
                if len(leg) > 40:
                    return leg[:2100], str(d.get("o_que_foi_dito", ""))
            except Exception as ex:
                print(f"  [aviso] Gemini {modelo} (tentativa {tentativa}): {str(ex)[:160]}")
                time.sleep(15 * tentativa)
    return legenda_reserva(titulo), ""


# ---------------------------------------------------------------- Instagram (Reels)
def _ok(r):
    try:
        d = r.json()
    except ValueError:
        raise RuntimeError(f"resposta inesperada ({r.status_code}): {r.text[:200]}")
    if isinstance(d, dict) and "error" in d:
        raise RuntimeError(d["error"].get("message", str(d["error"])))
    return d


PENDENTE = PASTA / "pendente.json"


def _esperar_e_publicar(cid, minutos=20):
    """Espera o Instagram processar o vídeo (mostra o andamento) e publica. None se ainda não terminou."""
    import requests
    ig, token = os.environ["META_IG_USER_ID"], os.environ["META_PAGE_TOKEN"]
    inicio, ultimo_aviso = time.time(), 0
    while time.time() - inicio < minutos * 60:
        s = _ok(requests.get(f"{GRAPH}/{cid}", params={"fields": "status_code,status", "access_token": token}, timeout=30))
        if s.get("status_code") == "FINISHED":
            return _ok(requests.post(f"{GRAPH}/{ig}/media_publish", data={"creation_id": cid, "access_token": token},
                                     timeout=60))["id"]
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram recusou o vídeo: {s.get('status')}")
        if time.time() - ultimo_aviso > 60:
            print(f"  ... Instagram processando ({int((time.time() - inicio) / 60)} min): {s.get('status_code')} {s.get('status', '')}")
            ultimo_aviso = time.time()
        time.sleep(10)
    return None


def hospedar_no_github(caminho):
    """Publica o vídeo num ramo separado ('midia', sempre só com o arquivo atual, para o repositório não crescer)
    e devolve o link público raw.githubusercontent.com, que o Instagram baixa."""
    import requests
    import shutil
    import tempfile
    repo = os.environ["GITHUB_REPOSITORY"]
    cab = subprocess.run(["git", "config", "--get", "http.https://github.com/.extraheader"],
                         cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    nome = f"{int(time.time())}_{Path(caminho).name}"
    pasta = Path(tempfile.mkdtemp())
    shutil.copy(caminho, pasta / nome)

    def git(*args):
        extra = ["-c", f"http.https://github.com/.extraheader={cab}"] if cab else []
        subprocess.run(["git", *extra, *args], cwd=pasta, check=True, capture_output=True, text=True)

    git("init", "-q")
    git("checkout", "-q", "-b", "midia")
    git("config", "user.name", "robo-reels")
    git("config", "user.email", "robo-reels@users.noreply.github.com")
    git("add", nome)
    git("commit", "-q", "-m", "video do reels")
    git("push", "-q", "-f", f"https://github.com/{repo}.git", "midia")
    shutil.rmtree(pasta, ignore_errors=True)
    url = f"https://raw.githubusercontent.com/{repo}/midia/{nome}"
    for _ in range(24):
        try:
            if requests.head(url, timeout=20).status_code == 200:
                break
        except Exception:
            pass
        time.sleep(5)
    print("  vídeo hospedado:", url)
    return url


def postar_reels(video, legenda, nome):
    """Publica como Reels: o Instagram baixa o vídeo de um link público (mais estável que o envio direto)."""
    import requests
    ig, token = os.environ["META_IG_USER_ID"], os.environ["META_PAGE_TOKEN"]
    url = hospedar_no_github(video)
    cid = _ok(requests.post(f"{GRAPH}/{ig}/media", data={
        "media_type": "REELS", "video_url": url, "caption": legenda,
        "share_to_feed": "true", "access_token": token}, timeout=60))["id"]
    mid = _esperar_e_publicar(cid)
    if mid is None:  # guarda para publicar na próxima rodada, sem enviar de novo
        PENDENTE.write_text(json.dumps({"cid": cid, "arquivo": nome, "desde": time.time()}), encoding="utf-8")
        raise RuntimeError("o Instagram ainda está processando; o robô publica na próxima rodada (sem reenviar)")
    return mid


# ---------------------------------------------------------------- principal
def pendentes():
    for v in sorted(ENTRADA.glob("*")):
        if v.suffix.lower() in (".mp4", ".mov", ".m4v"):
            txt = v.with_suffix(".txt")
            titulo = txt.read_text(encoding="utf-8").strip() if txt.exists() else v.stem.replace("_", " ")
            yield v, txt, titulo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teste", action="store_true")
    args = ap.parse_args()
    SAIDA.mkdir(exist_ok=True)
    log = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    erro = False
    pend = json.loads(PENDENTE.read_text()) if PENDENTE.exists() else None
    if pend and not args.teste:  # vídeo já enviado numa rodada anterior: só publica
        print(f"• publicando o que ficou pendente: {pend['arquivo']}")
        try:
            mid = _esperar_e_publicar(pend["cid"], minutos=15)
            if mid:
                print("  ✔ Reels publicado:", mid)
                PENDENTE.unlink()
                log.append({"quando": datetime.now().isoformat(timespec="minutes"), "arquivo": pend["arquivo"],
                            "instagram_id": mid})
                LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
                for f in ENTRADA.glob(Path(pend["arquivo"]).stem + ".*"):
                    if f.name != "LEIA.txt":
                        f.unlink()
            else:
                sys.exit("O Instagram ainda não terminou de processar o vídeo pendente. Rode de novo mais tarde.")
        except RuntimeError as ex:
            print("  ✖ o vídeo pendente falhou; vai enviar de novo:", ex)
            PENDENTE.unlink()
    for lance, txt, titulo in pendentes():
        print(f"• {lance.name}: {titulo}")
        try:
            reels = editor.montar(lance, titulo, SAIDA / f"{lance.stem}_reels.mp4")
            fixa = lance.with_suffix(".legenda.txt")  # legenda pronta (opcional): usa ela no lugar da IA
            if fixa.exists():
                legenda, dito = fixa.read_text(encoding="utf-8").strip(), "legenda pronta"
            else:
                legenda, dito = legenda_por_audio(lance, titulo)
            (SAIDA / f"{lance.stem}_legenda.txt").write_text(legenda, encoding="utf-8")
            print("  legenda:\n" + "\n".join("    " + l for l in legenda.splitlines()))
            if args.teste:
                continue
            mid = postar_reels(reels, legenda, lance.name)
            print("  ✔ Reels publicado:", mid)
            log.append({"quando": datetime.now().isoformat(timespec="minutes"), "titulo": titulo,
                        "arquivo": lance.name, "o_que_foi_dito": dito, "instagram_id": mid})
            LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
            lance.unlink()  # sai da fila (o repositório não cresce)
            txt.unlink(missing_ok=True)
            lance.with_suffix(".legenda.txt").unlink(missing_ok=True)
        except Exception as ex:
            print("  ✖ erro:", ex)
            erro = True
    if erro:
        sys.exit("Houve erro (veja acima). Os vídeos com erro continuam na pasta entrada para tentar de novo.")


if __name__ == "__main__":
    main()
