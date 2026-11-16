# Robô de Notícias de Futebol: @canaldotenorio (Instagram)

## Situação atual (etapa 3)
- Perfil: **CANAL DO TENÓRIO / @canaldotenorio**. Times: **Vasco e Palmeiras**, alternando um post de cada.
- **16 execuções por dia** (de hora em hora, das 8h às 23h), 1 notícia por vez: pelo menos 10 posts por dia sempre que houver notícia nova. São 16 posts no feed e 16 stories, abaixo do limite de 50 por dia da API.
- **Fontes, como quem digita o nome do clube no Google Notícias**: busca "Vasco" e "Palmeiras" no Google Notícias e também dentro de ge.globo.com e uol.com.br. Prioridade: 1) ge e UOL, 2) sites de setoristas do clube (`fontes_time`: NETVASCO, SuperVasco, Nosso Palestra, Verdazzo...), 3) outros veículos conhecidos. Posts de setoristas no X/Twitter não entram, porque não há forma gratuita de ler automaticamente; entram as matérias que eles publicam nos sites.
- A **fonte** (veículo e site, ex.: "ge · ge.globo.com") aparece na arte e na legenda.
- **Selo duplo** no topo da arte: TIME + ASSUNTO (OFICIAL, MERCADO DA BOLA, PRÉ-JOGO, PÓS-JOGO, DESFALQUE, DECLAROU, BASTIDORES, TORCIDA, BASE, URGENTE, NOTÍCIA), escolhido pelo assunto da notícia. O título da arte sempre cita o time quando a IA está ligada.
- Faixa pequena **"SIGA"** com YouTube, Instagram e TikTok e o @, na arte e na legenda.
  - **Ícones oficiais**: baixe os ícones nas páginas de marca de cada rede e salve como `icones/youtube.png`, `icones/instagram.png` e `icones/tiktok.png` (PNG com fundo transparente). Sem esses arquivos, a arte mostra os nomes das redes em pequenas etiquetas.
- O robô não repete o mesmo fato, mesmo quando veículos diferentes o dão com palavras diferentes (`estado.json → titulos`).
- **Legenda** (etapa 4): selo (TIME | ASSUNTO) → **a notícia escrita**, resumida com palavras próprias, juntando os fatos das manchetes de vários veículos sobre o mesmo assunto (`mais_manchetes`) → **💬 pergunta ao torcedor** (vascaíno/palmeirense, config `torcedor`) para puxar conversa → fonte (veículo + site) → crédito da foto → "Siga" nas 3 redes → hashtags. O resumo é feito a partir das manchetes, não do texto das matérias (direitos autorais). Sem a chave da IA, a legenda fica só com o título e uma pergunta pronta conforme o assunto.
- **Story automático**: cada post do feed é seguido do story na hora (2 tentativas), com o aviso "LEIA A NOTÍCIA COMPLETA NO FEED". O story só sai se o feed sair.

> **Para continuar em outra conversa com o Claude:** anexe este zip e cole a frase:
> "Este é o meu robô de notícias de futebol para Instagram, feito a partir do robô da minha loja. Leia o LEIA-ME_CONTEXTO.md e vamos continuar."

## O que já está pronto
- **noticias.py**: busca notícias recentes dos times do `config.json` no Google Notícias (RSS público, sem chave), dá preferência às fontes confiáveis (ge, Lance!, ESPN, UOL…) e não repete notícias, nem a mesma notícia dada por veículos diferentes.
- **designs.py**: arte de notícia 1080x1350 (feed) e 1080x1920 (story). Tem só texto: título grande, nome do time, crédito "Fonte: veículo" e o @ do perfil. Cores e nome vêm do `config.json`.
- **artes.py**: transforma o design em imagem (Chromium/Playwright), o mesmo do robô da MCastro.
- **postar.py**: posta **só no Instagram** (feed + story opcional), com legenda, crédito e hashtags, e anota em `estado.json` o que já saiu.
- **.github/workflows/postar.yml**: roda sozinho na nuvem do GitHub de hora em hora, das 8h às 23h (horário de Brasília), com 1 notícia por vez. Tem também o botão Run workflow (com modo teste).
- **exemplo/**: como a arte fica hoje.

## NOVO: fotos reais e resumo automáticos (etapa 2)
- **fotos.py**: para cada notícia, procura sozinho uma **foto real com licença livre** do jogador citado no **Wikimedia Commons** (sem chave) e, se houver o secret `FLICKR_API_KEY`, também no **Flickr**. Se não achar foto do jogador, tenta as buscas de `fotos_time` (ex.: estádio São Januário). Se não achar nada, posta a arte só com texto, e o robô nunca para.
  - Aceita só CC0, domínio público, CC BY e CC BY-SA. Recusa "ND" (proíbe edição) e "NC" (proíbe uso comercial; para aceitar, mude `aceitar_nao_comercial`).
  - Confere se o nome do jogador está na descrição da foto, prefere fotos recentes e em pé e evita repetir a mesma foto (`estado.json → fotos_usadas`).
  - O crédito sai na arte (autor, site e licença) e na legenda (autor, site, licença com link e o aviso "foto editada"), como as licenças exigem.
- **resumo.py**: escreve título da arte, linha fina, legenda curta e selo (OFICIAL, MERCADO DA BOLA, PRÉ-JOGO, JOGO, DESFALQUE, URGENTE, NOTÍCIA) **com palavras próprias**, a partir das manchetes do Google Notícias. Com o secret `ANTHROPIC_API_KEY` usa IA (Claude Haiku), que só pode usar fatos das manchetes e também informa o nome completo do jogador para a busca da foto. Sem a chave, usa um plano B por palavras-chave, com o título original.
- **designs.py**: novos designs `noticia_foto` e `story_foto` (foto ao fundo, degradê, selo, time, título, linha fina e créditos). Veja `exemplo/1_feed_com_foto.jpg`.
- Limitação: foto livre de jogador costuma ser mais antiga (Seleção, clube anterior). Por isso o robô prefere as mais recentes.
- Recomendo a IA ligada: sem ela, o robô pode buscar só "Coutinho" e confundir jogadores com o mesmo nome. A IA passa "Philippe Coutinho".

## Regras importantes (direitos autorais)
- O robô **não copia o texto** das matérias: reescreve com palavras próprias e **dá crédito** ao veículo.
- **Não usa fotos de sites de notícia nem de agências** (Getty, AGIF etc.). Dar crédito não dá permissão (Lei 9.610/98), e o Instagram derruba posts e desativa contas com denúncias repetidas.
- Usa só fotos com licença livre, sempre com crédito ao fotógrafo. Se um fotógrafo ou clube autorizar por escrito, dá para incluir essa fonte.

## Configurar (o que muda no config.json)
| Campo | Para quê |
|---|---|
| `nome_pagina` / `nome_legenda` / `arroba` | nome e @ que aparecem na arte e na legenda |
| `redes` | @ do Instagram, YouTube e TikTok (aparecem no "Siga") |
| `times` | times para buscar notícias (ex.: ["Vasco", "Palmeiras"]) |
| `buscar_nos_sites` | sites onde ele também procura o nome do time (ex.: ge.globo.com, uol.com.br) |
| `fontes_prioritarias` / `fontes_time` / `fontes_preferidas` | ordem de preferência: ge/UOL → setoristas do clube → outros |
| `so_fontes_conhecidas` | true = só posta notícias das fontes das três listas |
| `busca_extra` | outros assuntos (ex.: "Brasileirão", "Seleção Brasileira") |
| `max_por_execucao` | quantas notícias por horário (recomendado: 1) |
| `horas_maximas_da_noticia` | ignora notícias mais velhas que isso |
| `postar_story` | true/false |
| `cores` | fundo, destaque, detalhe (faixa/tarja), texto |
| `hashtags` | hashtags fixas da legenda |
| `resumo_ia` | `usar` (true/false) e `modelo` da IA |
| `fotos` | `usar`, `fontes` (commons/flickr), `aceitar_nao_comercial`, `fotos_time` (buscas de reserva por time, com palavras obrigatórias) |

## Passo a passo para ligar (aprendido no robô da MCastro)
1. **Instagram precisa ser conta Profissional** (Criador ou Empresa) e **ligado a uma Página do Facebook**. A página não publica nada: só serve para a Meta liberar a API e hospedar a imagem por um instante.
2. **GitHub**: crie um repositório novo (ex.: `robo-futebol`) e suba todos os arquivos do zip.
   - O upload pelo site **ignora a pasta `.github`**. Crie o arquivo à mão em `Add file → Create new file`, com o nome `.github/workflows/postar.yml`, e cole o conteúdo.
3. **Meta (developers.facebook.com)**: um app com as permissões `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement` e `business_management`. A última foi necessária, porque sem ela `me/accounts` voltava vazio.
4. Gere o **token da Página**: estenda o token de usuário em "Estender token" e pegue o token da página em `me/accounts`. No depurador de token, ele deve mostrar **"Expira: Nunca"**. O acesso a dados vence em cerca de 3 meses sem uso, e aí é preciso renovar.
5. No repositório: **Settings → Secrets and variables → Actions** → crie `META_PAGE_ID`, `META_IG_USER_ID` e `META_PAGE_TOKEN`.
   - Opcional (recomendado): `ANTHROPIC_API_KEY`. Crie em console.anthropic.com → API Keys. É pago à parte, mas custa centavos por mês com 6 posts por dia.
   - Opcional: `FLICKR_API_KEY`, para ter mais fotos. É grátis em flickr.com/services/apps/create (escolha "Non-Commercial" se não for monetizar).
6. **Actions → Notícias de futebol → Run workflow**. Com a caixa "teste" marcada (padrão), ele só gera as artes e a legenda, sem postar. Baixe o resultado em **Artifacts → artes-teste**, no fim da execução. Para postar de verdade pelo botão, desmarque a caixa. Os horários automáticos sempre postam.
- ⚠️ Nunca mande senha nem token no chat. Eles ficam só nos Secrets do GitHub.

## Testar no computador (opcional)
```
pip install -r requirements.txt
python -m playwright install chromium
python postar.py --teste --exemplo     # arte de exemplo, sem internet
python postar.py --teste               # busca notícias reais e só gera as artes
```

## Ideias para a próxima etapa
- Primeiro teste real no GitHub (Run workflow com `--teste`, para ver as fotos que ele acha antes de postar).
- Logo do perfil na arte.
- Tipos de post: resultado de jogo com placar, próximos jogos, tabela, enquete nos stories.
- Carrossel (título + resumo escrito com palavras próprias).
- Limite do Instagram: 50 publicações por 24h pela API. O robô usa até 16 posts + 16 stories por dia.
