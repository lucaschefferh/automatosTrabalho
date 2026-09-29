"""Uso:
    python main.py                      # abre a interface gráfica
    python main.py --cli                # imprime a construção passo a passo no terminal
    python main.py --afnd x.json --entrada y.txt
"""
import argparse

from automato import (carregar_afnd, construir_afd, afd_para_regex,
                      verificar_equivalencia, ler_sentencas, simular, aceita_regex)


def imprimir_construcao(afnd, afd, regex):
    print("=== Construção de subconjuntos (AFND → AFD) ===")
    print(f"{'Estado AFD':<16}{'Símbolo':<9}{'mover':<16}{'ε-fecho = destino':<20}{'novo?'}")
    for p in afd["passos"]:
        print(f"{p['origem']:<16}{p['simbolo']:<9}{p['mover']:<16}{p['destino']:<20}"
              f"{'sim' if p['novo'] else ''}")
    print(f"\nInicial: {afd['inicial']}")
    print(f"Finais : {', '.join(afd['finais'])}")
    print(f"\n=== Expressão regular ===\n{regex or 'ε'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--afnd", default="afnd.json")
    ap.add_argument("--entrada", default="entrada.txt")
    ap.add_argument("--cli", action="store_true")
    args = ap.parse_args()

    afnd = carregar_afnd(args.afnd)
    afd = construir_afd(afnd)
    # Se o grupo derivou a ER à mão, coloque-a em "regex" no JSON para usá-la aqui.
    regex = afnd.get("regex") or afd_para_regex(afd)

    if args.cli:
        imprimir_construcao(afnd, afd, regex)
        dif = verificar_equivalencia(afnd, afd, regex)
        print(f"\nVerificação AFND × AFD × ER (palavras até tamanho 8): "
              f"{'OK, sem divergências' if not dif else f'{len(dif)} DIVERGÊNCIAS'}")
        for w in ler_sentencas(args.entrada):
            print(f"  {w or 'ε':<10} AFD={'aceita' if simular(afd, w)[1] else 'rejeita':<8}"
                  f"ER={'aceita' if aceita_regex(regex, w) else 'rejeita'}")
    else:
        from gui import iniciar
        iniciar(afd, regex, args.entrada)


if __name__ == "__main__":
    main()
