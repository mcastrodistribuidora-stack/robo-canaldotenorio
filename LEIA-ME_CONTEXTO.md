# Robô de Notícias do Vasco: só Instagram

> **Para continuar em outra conversa com o Claude:** anexe este zip e cole a frase:
> "Este é o meu robô de notícias do Vasco para Instagram. Leia o LEIA-ME_CONTEXTO.md e vamos continuar."

## O que já está pronto
- **Só notícias do Vasco.** O robô busca o máximo de notícias no Google Notícias (ge/Globo, ESPN, Lance!, Terra, SUPERVASCO, UOL e qualquer outro veículo) e também no feed RSS do NETVASCO.
- **Sem repetidas.** Quando vários sites dão a mesma notícia (ex.: "Vasco compra Robert Renan" no ge e no Lance!), ela sai uma vez só. O robô compara as palavras principais das manchetes, inclusive com o que já foi postado antes.
- **Arte limpa:** fundo escuro, manchete grande, um traço vermelho, data no topo e "Fonte: veículo" no rodapé. Feed 1080x1350 e story 1080x1920 (veja `exemplo/`).
- **Horários:** roda de hora em hora, das 8h às 23h (horário de Brasília). Posta 1 notícia por vez, sempre a mais recente que ainda não saiu, o que dá até 16 por dia.
- **Estatísticas (NETVASCO):** às **12h e às 19h**, no lugar da notícia, sai um post de estatística com dados reais de 2024, 2025 e 2026. São 7 modelos: Léo Jardim nas 3 temporadas, evolução de gols de jogador, artilheiro de cada temporada, top 5 artilheiros, cartões, aproveitamento dos técnicos e comparação das temporadas. Todos terminam com uma pergunta para o público comentar. O mesmo modelo só volta depois de 10 dias, já com números atualizados. O NETVASCO não publica assistências.
- **Fotos:** o robô procura no Wikimedia Commons (licença livre) a foto do jogador citado na manchete. Se não achar, usa São Januário. A foto entra no topo da arte, com o crédito do fotógrafo na arte e na legenda. Sem foto, sai o modelo limpo só com texto.
- **Cruz de Malta:** aparece ao lado do nome da página em todas as artes e como marca d'água discreta (arquivo `assets/cruz.png`).
- **Seus canais:** @canaldotenorio (YouTube · Instagram · TikTok) no rodapé de todas as artes e na legenda.
- **X/Twitter:** fica de fora, porque bloqueia robôs e a API oficial é paga. Um post exclusivo do X pode ser feito manualmente com o Claude, a partir de um link ou print.

## Regras importantes (direitos autorais)
- O robô usa **só o título** da notícia e **dá crédito** ao veículo. Não copia o texto da matéria.
- **Não usa fotos** de sites de notícia nem de jogadores (têm dono). Se quiser imagens, os caminhos seguros são: escudo/arte própria, fotos com licença livre ou fotos que você mesmo tenha.

## Configurar (o que muda no config.json)
| Campo | Para quê |
|---|---|
| `nome_pagina` / `arroba` | nome e @ que aparecem na arte e na legenda |
| `buscas_google` | o que o robô procura no Google Notícias |
| `feeds_diretos` | feeds RSS de sites (hoje: NETVASCO) |
| `ignorar_se_tiver` | descarta manchetes com esses nomes (ex.: "Vasco Rossi", que não é o clube) |
| `max_por_execucao` | quantas notícias por hora (1 = até 16 por dia) |
| `horas_maximas_da_noticia` | ignora notícias mais velhas que isso |
| `postar_story` | true/false |
| `usar_fotos` | true/false: buscar foto no Wikimedia |
| `horas_estatistica` | horários dos posts de estatística (padrão 12 e 19) |
| `temporadas_estatistica` | temporadas comparadas (ex.: [2024, 2025, 2026]) |
| `dias_entre_repeticoes` | dias até o mesmo modelo de estatística voltar |
| `redes` | texto embaixo do @ (YouTube · Instagram · TikTok) |
| `cores` | fundo, texto, suave (cinza) e detalhe (traço vermelho) |
| `hashtags` | hashtags fixas da legenda |

## Passo a passo para ligar (aprendido no robô da MCastro)
1. **Instagram precisa ser conta Profissional** (Criador ou Empresa) e **ligado a uma Página do Facebook**. A página não publica nada: só serve para a Meta liberar a API e hospedar a imagem por um instante.
2. **GitHub**: crie um repositório novo (ex.: `robo-futebol`) e suba todos os arquivos do zip.
   - O upload pelo site **ignora a pasta `.github`**. Crie o arquivo à mão em `Add file → Create new file`, com o nome `.github/workflows/postar.yml`, e cole o conteúdo.
3. **Meta (developers.facebook.com)**: um app com as permissões `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement` e `business_management`. A última foi necessária, porque sem ela `me/accounts` voltava vazio.
4. Gere o **token da Página**: estenda o token de usuário em "Estender token" e pegue o token da página em `me/accounts`. No depurador de token, ele deve mostrar **"Expira: Nunca"**. O acesso a dados vence em cerca de 3 meses sem uso, e aí é preciso renovar.
5. No repositório: **Settings → Secrets and variables → Actions** → crie `META_PAGE_ID`, `META_IG_USER_ID` e `META_PAGE_TOKEN`.
6. **Actions → Notícias do Vasco → Run workflow** para testar.
- ⚠️ Nunca mande senha nem token no chat. Eles ficam só nos Secrets do GitHub.

## Testar no computador (opcional)
```
pip install -r requirements.txt
python -m playwright install chromium
python postar.py --teste --exemplo     # arte de exemplo, sem internet
python postar.py --teste               # busca notícias reais e só gera as artes
python postar.py --teste --estatistica # gera um post de estatística com dados reais
```

## Ideias para a próxima etapa
- Design com a identidade do perfil (logo, cores do time, selos "URGENTE", "OFICIAL", "MERCADO DA BOLA").
- Tipos de post: resultado de jogo com placar, próximos jogos, tabela, enquete nos stories.
- Carrossel (título + resumo escrito com palavras próprias).
- Limite do Instagram: 50 posts por 24h pela API. O robô usa no máximo 16 por dia (32 com story).
