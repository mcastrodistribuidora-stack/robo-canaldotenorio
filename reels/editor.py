#!/usr/bin/env python3
"""
Editor automático de REELS DE REAÇÃO (9:16) do Canal do Tenório.

Entradas:
  - 1 vídeo de lance/notícia (o que vai no topo)
  - 1 título
  - biblioteca de vídeos base (você reagindo, câmera fixa) na pasta base/

Regras do modelo:
  - Saída 1080x1920, 30 fps, H.264 >= 8 Mbps, AAC 192k, -14 LUFS.
  - Vídeo base em tela cheia (sem bordas pretas), cortado na duração do lance.
  - Usa um base com duração >= lance; alterna os bases (não repete o último); começa num trecho parado.
  - Lance no topo, centralizado, 88% da largura, topo em y=210, proporção original.
  - Título logo abaixo (2% de espaço), caixa alta, extra-negrito, preto sobre faixa branca em CADA linha,
    no máximo 2 linhas, ~60 px. Fixo do início ao fim.
  - Áudio: o som do base (sua voz) em volume cheio + o som do lance junto. Nada é silenciado.

Uso:
  python reels/editor.py lance.mp4 "TÍTULO DO VÍDEO" saida.mp4
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PASTA = Path(__file__).resolve().parent          # pasta reels/
RAIZ = PASTA.parent
BASES = PASTA / "base"
ESTADO = PASTA / "base_estado.json"
FONTE = next((p for p in [RAIZ / "fontes" / "Montserrat-ExtraBold.ttf",
                          RAIZ / "fontes" / "InterDisplay-Black.otf",
                          RAIZ.parent / "futebol" / "fontes" / "InterDisplay-Black.otf"] if p.exists()), None)

W, H = 1080, 1920
LANCE_W = round(W * 0.88 / 2) * 2   # 950
LANCE_Y = round(H * 0.06)           # 115 (um pouco mais para cima, para não cobrir o rosto)
ESPACO = -18                        # o título encosta um pouquinho na borda de baixo do lance
FONTE_PX = 60
FAIXA_PAD_X, FAIXA_PAD_Y, ENTRE_LINHAS = 22, 12, 8


def info(arq):
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                   "format=duration:stream=codec_type,width,height", "-of", "json", str(arq)],
                                  capture_output=True, text=True, check=True).stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), {})
    return {"dur": float(d["format"]["duration"]), "w": v.get("width"), "h": v.get("height"),
            "audio": any(s["codec_type"] == "audio" for s in d["streams"])}


# ---------------------------------------------------------------- escolha do base
def escolher_base(dur):
    bases = sorted(p for p in BASES.iterdir() if p.suffix.lower() in (".mp4", ".mov", ".m4v"))
    servem = [b for b in bases if info(b)["dur"] >= dur + 0.2]
    if not servem:  # nenhum é longo o bastante: usa o mais longo (o vídeo final fica com a duração dele)
        servem = [max(bases, key=lambda b: info(b)["dur"])]
    ultimo = json.loads(ESTADO.read_text())["ultimo"] if ESTADO.exists() else None
    candidatos = [b for b in servem if b.name != ultimo] or servem
    # alterna em ordem: o próximo depois do último usado
    if ultimo and ultimo in [b.name for b in bases]:
        ordem = bases[bases.index(next(b for b in bases if b.name == ultimo)) + 1:] + bases
        candidatos = [b for b in ordem if b in candidatos] or candidatos
    escolhido = candidatos[0]
    ESTADO.write_text(json.dumps({"ultimo": escolhido.name}))
    return escolhido


def inicio_natural(base, dur):
    """Procura o começo mais 'parado' (sem gesto no meio) entre 0 e o último ponto possível."""
    import cv2
    total = info(base)["dur"]
    folga = max(0.0, total - dur - 0.2)
    if folga < 0.5:
        return 0.0
    cap = cv2.VideoCapture(str(base))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    passo = max(1, int(fps / 4))  # 4 amostras por segundo
    movimento, ant, i = [], None, 0
    while True:
        ok = cap.grab()
        if not ok or i / fps > folga + 0.5:
            break
        if i % passo == 0:
            _, f = cap.retrieve()
            g = cv2.cvtColor(cv2.resize(f, (96, 170)), cv2.COLOR_BGR2GRAY).astype("float32")
            movimento.append((i / fps, 0.0 if ant is None else float(abs(g - ant).mean())))
            ant = g
        i += 1
    cap.release()
    if len(movimento) < 3:
        return 0.0
    # nota = movimento na janela de ~0,5 s em volta; leve preferência pelo começo do vídeo
    melhor, nota_melhor = 0.0, None
    for k in range(1, len(movimento)):
        t = movimento[k][0]
        if t > folga:
            break
        janela = [m for tt, m in movimento[max(1, k - 1):k + 2]]
        nota = sum(janela) / len(janela) + 0.02 * t
        if nota_melhor is None or nota < nota_melhor:
            melhor, nota_melhor = t, nota
    return round(melhor, 2)


# ---------------------------------------------------------------- título
def quebrar(texto, fonte, largura_max):
    palavras = texto.upper().split()
    linhas, atual = [], ""
    for p in palavras:
        teste = (atual + " " + p).strip()
        if fonte.getlength(teste) + 2 * FAIXA_PAD_X <= largura_max or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    linhas.append(atual)
    return linhas


def imagem_titulo(texto, destino):
    """PNG transparente 1080 de largura com as faixas brancas e o texto preto.
    Título nunca é cortado: diminui a fonte até caber em 2 linhas (mín. 40 px);
    se for muito longo, usa 3 linhas e segue diminuindo (mín. 30 px), e só então 4 linhas."""
    for max_linhas, minimo in ((2, 40), (3, 30), (4, 30)):
        tam = FONTE_PX
        while True:
            fonte = ImageFont.truetype(str(FONTE), tam)
            linhas = quebrar(texto, fonte, W - 80)
            if len(linhas) <= max_linhas or tam <= minimo:
                break
            tam -= 2
        if len(linhas) <= max_linhas:
            break
    sobe, desce = fonte.getmetrics()
    alt_linha = sobe + desce + 2 * FAIXA_PAD_Y
    altura = len(linhas) * alt_linha + (len(linhas) - 1) * ENTRE_LINHAS
    img = Image.new("RGBA", (W, altura), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 0
    for l in linhas:
        larg = fonte.getlength(l)
        x0 = (W - larg) / 2 - FAIXA_PAD_X
        d.rectangle([x0, y, x0 + larg + 2 * FAIXA_PAD_X, y + alt_linha], fill=(255, 255, 255, 255))
        d.text((W / 2, y + FAIXA_PAD_Y), l, font=fonte, fill=(0, 0, 0, 255), anchor="mt")
        y += alt_linha + ENTRE_LINHAS
    img.save(destino)
    return altura


# ---------------------------------------------------------------- montagem
def montar(lance, titulo, saida):
    lance = Path(lance)
    li = info(lance)
    base = escolher_base(li["dur"])
    bi = info(base)
    dur = li["dur"]
    ini = inicio_natural(base, dur)
    lance_h = round(LANCE_W * li["h"] / li["w"] / 2) * 2
    titulo_y = LANCE_Y + lance_h + ESPACO
    tmp = Path(tempfile.mkdtemp())
    png = tmp / "titulo.png"
    imagem_titulo(titulo, png)
    print(f"lance {li['w']}x{li['h']} {li['dur']:.1f}s | base {base.name} ({bi['w']}x{bi['h']}) a partir de {ini}s | "
          f"vídeo final {dur:.2f}s")

    emendar = bi["dur"] - ini < dur  # base curto demais: emenda com ele mesmo (transição suave)
    X = 0.6  # duração da transição da emenda
    filtro = []
    if emendar:
        ini = 0.0
        off = bi["dur"] - X
        # 1ª passada do base esticada (último quadro congelado) + 2ª passada por cima, entrando em fade
        filtro += [f"[0:v]fps=30,scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,"
                   f"tpad=stop_mode=clone:stop_duration={dur:.3f}[b1]",
                   f"[3:v]fps=30,scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,"
                   f"format=yuva420p,fade=t=in:st=0:d={X}:alpha=1,setpts=PTS-STARTPTS+{off:.3f}/TB[b2]",
                   f"[b1][b2]overlay=eof_action=pass:format=auto,trim=0:{dur:.3f}[fundo]"]
        print(f"  base mais curto que o lance: emendado com transição em {off:.1f}s")
    else:
        filtro.append(f"[0:v]fps=30,scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1[fundo]")
    filtro += [
        f"[1:v]fps=30,scale={LANCE_W}:{lance_h}:flags=lanczos,setsar=1[lance]",
        f"[fundo][lance]overlay=x=(W-w)/2:y={LANCE_Y}:eof_action=pass[v1]",
        f"[v1][2:v]overlay=x=0:y={titulo_y}:format=auto,format=yuv420p[v]",
    ]
    abase = "[0:a]"
    if emendar and bi["audio"]:
        ms = int(off * 1000)
        filtro += [f"[0:a]afade=t=out:st={off:.3f}:d={X}[a1]",
                   f"[3:a]afade=t=in:st=0:d={X},adelay={ms}|{ms}[a2]",
                   f"[a1][a2]amix=inputs=2:duration=longest:normalize=0[abase]"]
        abase = "[abase]"
    if li["audio"] and bi["audio"]:
        # normalize=0: nenhum dos dois é abaixado; depois tudo vai para -14 LUFS
        filtro.append(f"{abase}[1:a]amix=inputs=2:duration=longest:normalize=0,atrim=0:{dur:.3f},"
                      "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
    elif bi["audio"] or li["audio"]:
        filtro.append(f"{abase if bi['audio'] else '[1:a]'}loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
    tem_audio = bi["audio"] or li["audio"]

    temp_saida = Path(saida).with_suffix(".parcial.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y",
           *([] if bi["dur"] - ini < dur else ["-ss", str(ini), "-t", f"{dur:.3f}"]), "-i", str(base),
           "-t", f"{dur:.3f}", "-i", str(lance),
           "-loop", "1", "-t", f"{dur:.3f}", "-i", str(png),
           *(["-t", f"{dur - (bi['dur'] - X) + 0.1:.3f}", "-i", str(base)] if bi["dur"] - ini < dur else []),
           "-filter_complex", ";".join(filtro), "-map", "[v]"]
    if tem_audio:
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    cmd += ["-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-r", "30",
            "-movflags", "+faststart", str(temp_saida)]
    subprocess.run(cmd, check=True)
    temp_saida.replace(saida)
    return Path(saida)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    print("pronto:", montar(sys.argv[1], sys.argv[2], sys.argv[3]))
