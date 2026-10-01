"""Funções compartilhadas pelas páginas da interface."""
import json

from automato import construir_afd, ler_sentencas


def carregar_dados():
    with open("afnd.json", encoding="utf-8") as arquivo:
        afnd = json.load(arquivo)
    return construir_afd(afnd), ler_sentencas("entrada.txt")


def diagrama(afd, atual, aresta_ativa=None):
    """Gera o diagrama do AFD e destaca o estado e a transição atuais."""
    linhas = [
        "digraph AFD {",
        "rankdir=LR;",
        'node [shape=circle, style=filled, fillcolor="white"];',
        '__inicio [shape=point, width=0.12];',
        f'__inicio -> "{afd["inicial"]}";',
    ]
    for estado in afd["estados"]:
        forma = "doublecircle" if estado in afd["finais"] else "circle"
        cor = "#ffe066" if estado == atual else "white"
        linhas.append(f'"{estado}" [shape={forma}, fillcolor="{cor}"];')

    grupos = {}
    for (origem, simbolo), destino in afd["delta"].items():
        grupos.setdefault((origem, destino), []).append(simbolo)
    for (origem, destino), simbolos in grupos.items():
        ativa = aresta_ativa == (origem, destino)
        cor = "#d62828" if ativa else "black"
        largura = 3 if ativa else 1
        rotulo = ",".join(simbolos)
        linhas.append(
            f'"{origem}" -> "{destino}" [label="{rotulo}", '
            f'color="{cor}", fontcolor="{cor}", penwidth={largura}];'
        )
    linhas.append("}")
    return "\n".join(linhas)
