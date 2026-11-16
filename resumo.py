"""
Escreve, com PALAVRAS PRÓPRIAS, o texto do post a partir das manchetes da notícia.

- Com o secret ANTHROPIC_API_KEY: usa a IA (Claude) para criar título da arte, linha fina,
  a notícia escrita para a legenda (resumo), uma pergunta para o torcedor, o selo e os nomes
  das pessoas (usados para buscar a foto).
  Ela só pode usar fatos que estão nas manchetes. Não inventa nada.
- Sem a chave (ou se a IA falhar): plano B simples, usando o título e regras de palavras-chave.
"""
import json
import os
import re

SELOS = ["URGENTE", "OFICIAL", "MERCADO DA BOLA", "PRÉ-JOGO", "PÓS-JOGO", "DESFALQUE", "DECLAROU",
         "BASTIDORES", "TORCIDA", "BASE", "NOTÍCIA"]
SELOS_AJUDA = """URGENTE (fato muito grande e repentino), OFICIAL (clube anunciou/confirmou), MERCADO DA BOLA (contratação,
saída, negociação, renovação), PRÉ-JOGO (escalação, relacionados, próximo jogo), PÓS-JOGO (resultado, gols, atuação),
DESFALQUE (lesão, suspensão, corte), DECLAROU (entrevista ou fala de alguém), BASTIDORES (diretoria, SAF, finanças,
política do clube), TORCIDA (ingressos, protestos, público), BASE (categorias de base), NOTÍCIA (nenhum dos outros)"""

PROMPT = """Você escreve posts de um perfil de notícias de futebol no Instagram, em português do Brasil.
Abaixo estão manchetes de vários veículos sobre UM mesmo fato. Escreva com PALAVRAS PRÓPRIAS (não copie frases das manchetes).

REGRAS:
- Use SOMENTE fatos que aparecem nas manchetes. Não invente placar, data, valor, contrato ou declaração.
- Se as manchetes falam em negociação/interesse, não escreva como se estivesse fechado.
- Tom jornalístico, sem opinião, sem clickbait, sem emoji no título.
- O título da arte TEM que conter o nome do time ({termo}).
- Escolha o selo pelo assunto: {selos_ajuda}
- "texto": conte a notícia como uma matéria curta, juntando TODOS os fatos que aparecem nas manchetes
  (quem, o quê, quando, contexto). Se houver poucos fatos, seja breve: não encha linguiça e não invente.
- "pergunta": uma pergunta para o torcedor ({torcedor}) dar a opinião nos comentários, ligada ao assunto,
  em tom de conversa (ex.: "E aí, {torcedor}, aprova essa contratação? Comenta aí 👇"). Não repita sempre a mesma.

Time/assunto: {termo}
Manchete principal ({fonte}): {titulo}
Outras manchetes do mesmo fato (veículo entre parênteses):
{outras}

Responda SÓ com um JSON neste formato:
{{"titulo_arte": "até 70 caracteres",
 "linha_fina": "até 110 caracteres, complementa o título com outro fato das manchetes (ou vazio)",
 "texto": "a notícia escrita, de 2 a 6 frases curtas",
 "pergunta": "pergunta para o torcedor comentar",
 "selo": "um destes: {selos}",
 "pessoas": ["nomes completos das pessoas principais, como aparecem nas manchetes, no máximo 2"]}}"""


def _selo_por_palavras(t):
    t = t.lower()
    regras = [
        ("URGENTE", r"\burgente\b"),
        ("DESFALQUE", r"\bles[ãa]o|lesionad|desfalque|cortado|suspenso|vetado|fora d[eo] jogo"),
        ("MERCADO DA BOLA", r"contrat|refor[çc]o|negoci|proposta|acerta|sondag|empr[ée]stimo|renova|venda|saída|deixa o"),
        ("OFICIAL", r"\boficial|anuncia|oficializa|confirma"),
        ("PÓS-JOGO", r"\bvence|empata|perde para|derrota|vit[óo]ria|goleia|\d+\s*(x|a)\s*\d+|atua[çc][ãa]o|notas"),
        ("PRÉ-JOGO", r"escala[çc][ãa]o|relacionad|enfrenta|encara|visita|recebe|pr[óo]ximo jogo|onde assistir|provável"),
        ("BASE", r"\bsub-?\d\d|\bbase\b|categorias de base"),
        ("TORCIDA", r"torcida|torcedor|ingresso|protesto|p[úu]blico"),
        ("BASTIDORES", r"\bsaf\b|diretoria|presidente|eleição|d[íi]vida|financ|balan[çc]o|conselho"),
        ("DECLAROU", r"\bdiz\b|afirma|declara|revela|desabafa|admite|garante|coletiva|entrevista"),
    ]
    for selo, padrao in regras:
        if re.search(padrao, t):
            return selo
    return "NOTÍCIA"


PALAVRAS_COMUNS = {"Brasileirão", "Copa", "Série", "Libertadores", "Sul-Americana", "Seleção", "Brasil",
                   "Campeonato", "Estadual", "Carioca", "Paulista", "Mundial", "Clube", "Técnico", "Veja",
                   "Confira", "Após", "Diretoria", "Torcida", "Torcedores", "Fifa", "CBF", "Conmebol"}
CLUBES = {"Flamengo", "Fluminense", "Botafogo", "Vasco", "Palmeiras", "Corinthians", "São Paulo", "Santos",
          "Grêmio", "Internacional", "Inter", "Cruzeiro", "Atlético", "Atlético-MG", "Galo", "Bahia", "Vitória",
          "Fortaleza", "Ceará", "Sport", "Athletico", "Athletico-PR", "Coritiba", "Bragantino", "Red Bull",
          "Juventude", "Mirassol", "Remo", "Paysandu", "Goiás", "Cuiabá", "Peixe", "Mengão", "Timão", "Verdão",
          "Tricolor", "Fogão", "Colorado", "Raposa", "Cruz-Maltino", "Gigante", "Chapecoense", "América-MG"}


def pessoas_por_regex(titulo, times):
    """Plano B: pega sequências de palavras com inicial maiúscula (ex.: 'Philippe Coutinho')."""
    ignorar = {t.lower() for t in times} | {p.lower() for p in PALAVRAS_COMUNS | CLUBES}
    palavras = re.findall(r"[A-ZÀ-Ý][\wÀ-ÿ'-]+(?:\s+(?:de|da|do|dos|das)?\s*[A-ZÀ-Ý][\wÀ-ÿ'-]+)*", titulo)
    achou = []
    for i, p in enumerate(palavras):
        if p.lower() in ignorar or any(w.lower() in ignorar for w in p.split()):
            continue
        if " " in p or len(p) >= 4:
            achou.append(p)
    return achou[:2]


PERGUNTAS = {
    "MERCADO DA BOLA": "E aí, {t}, aprova essa movimentação? Comenta aí 👇",
    "PRÉ-JOGO": "E aí, {t}, qual é o seu palpite para o jogo? Comenta aí 👇",
    "PÓS-JOGO": "E aí, {t}, o que achou da atuação do time? Comenta aí 👇",
    "DESFALQUE": "E aí, {t}, quem deve entrar no lugar? Comenta aí 👇",
    "DECLAROU": "E aí, {t}, concorda com essa fala? Comenta aí 👇",
    "BASTIDORES": "E aí, {t}, o que acha desse assunto? Comenta aí 👇",
    "TORCIDA": "E aí, {t}, você vai estar lá? Comenta aí 👇",
    "BASE": "E aí, {t}, acompanha a base? Quem você quer ver subir? Comenta aí 👇",
}


def torcedor(n, config):
    return config.get("torcedor", {}).get(n.get("termo", ""), "torcedor")


def pergunta_padrao(selo, n, config):
    return PERGUNTAS.get(selo, "E aí, {t}, qual é a sua opinião? Comenta aí 👇").format(t=torcedor(n, config))


def plano_b(n, config):
    selo = _selo_por_palavras(n["titulo"])
    return {
        "titulo_arte": n["titulo"],
        "linha_fina": "",
        "texto": n["titulo"] + ".",
        "pergunta": pergunta_padrao(selo, n, config),
        "selo": selo,
        "pessoas": pessoas_por_regex(n["titulo"], config.get("times", []) + [n.get("termo", "")]),
        "por_ia": False,
    }


def _chamar_ia(n, config):
    import requests
    outras = "\n".join(f"- {o}" for o in n.get("relacionadas", [])[:12]) or "- (nenhuma)"
    prompt = PROMPT.format(termo=n.get("termo", ""), fonte=n.get("fonte", ""), titulo=n["titulo"],
                           outras=outras, selos=", ".join(SELOS), selos_ajuda=SELOS_AJUDA,
                           torcedor=torcedor(n, config))
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=60, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
        "content-type": "application/json"}, json={
        "model": config.get("resumo_ia", {}).get("modelo", "claude-haiku-5-5"),
        "max_tokens": 1200, "messages": [{"role": "user", "content": prompt}]})
    r.raise_for_status()
    texto = "".join(b.get("text", "") for b in r.json().get("content", []))
    return json.loads(texto[texto.index("{"): texto.rindex("}") + 1])


def gerar(n, config):
    base = plano_b(n, config)
    if not os.environ.get("ANTHROPIC_API_KEY") or not config.get("resumo_ia", {}).get("usar", True):
        return base
    try:
        d = _chamar_ia(n, config)
        saida = {
            "titulo_arte": str(d.get("titulo_arte") or base["titulo_arte"]).strip()[:90],
            "linha_fina": str(d.get("linha_fina") or "").strip()[:130],
            "texto": str(d.get("texto") or base["texto"]).strip()[:1500],
            "selo": d.get("selo") if d.get("selo") in SELOS else base["selo"],
            "pessoas": [p for p in d.get("pessoas", []) if isinstance(p, str) and p.strip()][:2] or base["pessoas"],
            "por_ia": True,
        }
        saida["pergunta"] = str(d.get("pergunta") or "").strip()[:200] or pergunta_padrao(saida["selo"], n, config)
        return saida
    except Exception as ex:
        print(f"  [aviso] resumo por IA falhou, usando plano B: {ex}")
        return base
