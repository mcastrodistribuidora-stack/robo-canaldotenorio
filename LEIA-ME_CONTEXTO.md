# Robô de Notícias do Vasco: @canaldotenorio (Instagram)

> **Para continuar em outra conversa com o Claude:** anexe o zip do repositório e cole a frase:
> "Este é o meu robô de notícias do Vasco para Instagram (@canaldotenorio). Leia o LEIA-ME_CONTEXTO.md e vamos continuar."

## Situação atual (etapa 5)
- Perfil: **CANAL DO TENÓRIO / @canaldotenorio**. **Só Vasco** (Palmeiras saiu).
- Roda **de hora em hora, das 8h às 23h** (16 vezes por dia), 1 post por vez, cada um com o story logo em seguida.
- **12h e 19h = ESTATÍSTICA** (dados do NETVASCO, ver abaixo). Nos outros horários, **NOTÍCIA**.

### Notícias
- Fontes: Google Notícias com "Vasco" e também dentro de ge, UOL, ESPN, Lance!, Terra, SuperVasco e NETVASCO (`buscar_nos_sites`), mais o **feed RSS do NETVASCO** (`feeds_diretos`). Prioridade: ge, UOL e NETVASCO → setoristas (`fontes_time`) → outros conhecidos.
- Descarta páginas de placar ao vivo, apostas e "onde assistir", e outros "Vasco" (Vasco Rossi, Ponte Vasco da Gama...).
- **Não repete o mesmo fato**, mesmo quando veículos diferentes o dão com palavras diferentes (`estado.json → titulos`).
- **resumo.py** (IA: `GEMINI_API_KEY`, grátis, ou `ANTHROPIC_API_KEY`): título da arte, linha fina, notícia escrita com palavras próprias para a legenda, pergunta ao vascaíno e selo (MERCADO DA BOLA, PÓS-JOGO...). Sem a chave, usa o plano B.
- **fotos.py**: foto real com licença livre do jogador citado (Wikimedia Commons e, com `FLICKR_API_KEY`, Flickr). Se não achar, usa São Januário. Se não achar nada, sai a arte só com texto. Crédito do fotógrafo na arte e na legenda.
- X/Twitter não entra (não há leitura automática gratuita).

### Estatísticas (estatisticas.py)
- Baixa as tabelas do NETVASCO (`netvasco.com/futebol/estatisticas/index17.shtml?ano=AAAA`) das temporadas do config (2024, 2025, 2026).
- 7 modelos: Léo Jardim nas 3 temporadas ("Qual é a melhor versão?"), evolução de gols dos 3 artilheiros do ano, artilheiro de cada temporada, top 5 artilheiros, cartões, aproveitamento dos técnicos e o Vasco nas 3 temporadas. Todos terminam com uma pergunta ao torcedor.
- O mesmo modelo só volta depois de `dias_entre_repeticoes` (10), já com números atualizados. O NETVASCO não publica assistências.
- `dados/netvasco_sim.py` = dados de exemplo para teste sem internet (`python postar.py --teste --exemplo --estatistica`).

### Visual
- Fundo escuro, manchete grande com traço vermelho, **Cruz de Malta** ao lado do nome e como marca d'água (`assets/cruz.png`).
- Selo duplo VASCO + ASSUNTO, "SIGA" com YouTube/Instagram/TikTok e @canaldotenorio (ícones oficiais opcionais em `icones/`).
- Designs: `noticia`/`story` (só texto), `noticia_foto`/`story_foto` (foto ao fundo), `estatistica`/`estatistica_story`.

## Regras importantes (direitos autorais)
- Não copia texto das matérias: reescreve com palavras próprias e dá crédito ao veículo.
- **Não usa fotos de sites de notícia nem de agências** (Getty, AGIF etc.). Dar crédito não dá permissão (Lei 9.610/98), e o Instagram derruba posts e desativa contas com denúncias repetidas. Só fotos com licença livre, com crédito.

## Configurar (config.json)
| Campo | Para quê |
|---|---|
| `nome_pagina` / `nome_legenda` / `arroba` / `redes` | nome, @ e redes na arte e na legenda |
| `times` / `palavras_time` | time e apelidos que precisam estar no título |
| `buscar_nos_sites` / `feeds_diretos` | sites pesquisados no Google Notícias / feeds RSS diretos |
| `fontes_prioritarias` / `fontes_time` / `fontes_preferidas` / `so_fontes_conhecidas` | ordem de preferência das fontes |
| `max_por_execucao` / `horas_maximas_da_noticia` / `postar_story` | ritmo e idade máxima da notícia |
| `cores` | fundo, destaque, detalhe (vermelho), texto, suave (cinza) |
| `hashtags` | hashtags fixas |
| `resumo_ia` | `usar` e `modelo` (Claude) |
| `fotos` | `usar`, `fontes`, `aceitar_nao_comercial`, `fotos_time` |
| `estatisticas` | `usar`, `horas` (12 e 19), `temporadas`, `dias_entre_repeticoes` |

## Secrets do GitHub
`META_PAGE_ID`, `META_IG_USER_ID`, `META_PAGE_TOKEN` (obrigatórios); `GEMINI_API_KEY` ou `ANTHROPIC_API_KEY` (resumo com IA); `FLICKR_API_KEY` (mais fotos). Nunca mande senha nem token no chat.

## Testar
- GitHub: **Actions → Notícias de futebol → Run workflow** com "teste" marcado (padrão): gera as artes e a legenda sem postar. Baixe em **Artifacts → artes-teste**.
- Computador: `python postar.py --teste`, `python postar.py --teste --estatistica`, `python postar.py --teste --exemplo`.

## Ideias para a próxima etapa
- Pasta de fotos próprias do Canal do Tenório (prints dos vídeos, fotos no estádio), usada antes do Wikimedia.
- Mais modelos de estatística (mais titular, mais vezes saindo do banco, aproveitamento com/sem jogador).
- Carrossel e posts de resultado/próximo jogo.
