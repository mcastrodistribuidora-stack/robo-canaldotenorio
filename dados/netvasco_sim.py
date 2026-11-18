# Dados copiados do NETVASCO em 18/11/2026 (só para a simulação; o robô baixa sozinho).
T = {}
T[2026] = """Competições|J|V|E|D|GP|MGP|GC|MGC|S|%
Total|65|27|18|20|89|1.37|73|1.12|16|51
#
Jogador|J|G|MG|CA|CV|Tit|Sub|Ent|V|E|D|%
Adson|39|5|0.13|3|0|20|20|19|18|10|11|55
Andrés Gómez|52|8|0.15|17|1|46|19|6|24|13|15|54
Barros|38|3|0.08|10|2|31|8|7|12|15|11|45
Brenner|38|5|0.13|2|0|16|15|22|14|11|13|46
Bruno Duarte|15|5|0.33|0|0|11|9|4|9|1|5|62
David|46|6|0.13|1|0|21|21|25|16|16|14|46
Léo Jardim|62|0|0.00|2|0|62|0|0|25|17|20|49
Lucas Piton|41|0|0.00|3|1|31|21|10|17|12|12|51
Nuno Moreira|45|2|0.04|5|0|28|25|17|15|15|15|44
Paulo Henrique|42|0|0.00|5|0|31|14|11|19|10|13|53
Philippe Coutinho|7|3|0.43|1|0|7|6|0|2|2|3|38
Puma Rodríguez|50|10|0.20|2|0|33|5|17|22|15|13|54
Robert Renan|55|2|0.04|7|0|55|4|0|24|14|17|52
Saldivia|34|0|0.00|6|1|31|0|3|16|10|8|57
Spinelli|37|7|0.19|3|0|18|11|19|12|13|12|44
Tchê Tchê|44|2|0.05|5|0|30|20|14|21|10|13|55
Thiago Mendes|52|8|0.15|15|1|48|15|4|24|11|17|53
Vegetti|1|0|0.00|0|0|0|0|1|1|0|0|100
#
Jogador|J|CA|CV|V|E|D|%
Pedro Emanuel|30|0|0|15|7|8|58
Renato Gaúcho|18|0|0|7|5|6|48
Fernando Diniz|11|2|0|3|4|4|39
Marcelo Salles|3|0|1|1|1|1|44"""
T[2025] = """Competições|J|V|E|D|GP|MGP|GC|MGC|S|%
Total|71|23|20|28|94|1.32|94|1.32|0|42
#
Jogador|J|G|MG|CA|CV|Tit|Sub|Ent|V|E|D|%
Andrés Gómez|20|1|0.05|2|0|14|9|6|8|3|9|45
David|31|2|0.06|3|1|7|7|24|9|9|13|39
Hugo Moura|61|1|0.02|12|3|51|14|10|21|16|24|43
Léo Jardim|66|0|0.00|4|1|66|0|0|23|17|26|43
Lucas Piton|55|1|0.02|8|1|53|9|2|20|12|23|44
Nuno Moreira|56|11|0.20|5|0|54|52|2|18|15|23|41
Paulo Henrique|58|4|0.07|13|1|57|14|1|21|18|19|47
Philippe Coutinho|56|11|0.20|5|1|55|42|1|22|13|21|47
Puma Rodríguez|43|2|0.05|0|0|21|3|22|16|8|19|43
Rayan|57|20|0.35|5|0|52|23|5|17|15|25|39
Robert Renan|20|0|0.00|3|0|19|2|1|7|4|9|42
Tchê Tchê|50|2|0.04|4|0|41|29|9|17|10|23|41
Thiago Mendes|15|0|0.00|3|0|7|5|8|4|4|7|36
Vegetti|65|27|0.42|10|0|53|16|12|21|17|27|41
#
Jogador|J|CA|CV|V|E|D|%
Fernando Diniz|43|5|0|14|11|18|41
Fábio Carille|21|0|0|9|5|7|51"""
T[2024] = """Competições|J|V|E|D|GP|MGP|GC|MGC|S|%
Total|63|25|18|20|82|1.30|82|1.30|0|49
#
Jogador|J|G|MG|CA|CV|Tit|Sub|Ent|V|E|D|%
Adson|34|4|0.12|1|0|22|19|12|15|11|8|55
David|42|7|0.17|7|1|33|23|9|16|13|13|48
Léo Jardim|61|0|0.00|1|0|61|0|0|24|17|20|49
Lucas Piton|54|6|0.11|8|1|52|13|2|20|15|19|46
Paulo Henrique|55|1|0.02|13|0|47|22|8|21|14|20|47
Payet|43|6|0.14|10|0|30|23|13|17|14|12|50
Philippe Coutinho|18|3|0.17|0|0|10|9|8|3|7|8|30
Puma Rodríguez|34|2|0.06|3|0|16|8|18|11|11|12|43
Rayan|35|2|0.06|2|1|13|10|22|12|9|14|43
Vegetti|56|23|0.41|12|0|54|9|2|21|16|19|47
#
Jogador|J|CA|CV|V|E|D|%
Rafael Paiva|35|0|0|13|10|12|47
Ramón Díaz|19|2|0|9|5|5|56"""


def dados():
    from estatisticas import organizar
    return {a: organizar([[l.split("|") for l in b.strip().splitlines()] for b in txt.split("#")]) for a, txt in T.items()}
