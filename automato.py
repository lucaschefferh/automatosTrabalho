"""Núcleo teórico: AFND -> AFD (construção de subconjuntos), AFD -> ER
(eliminação de estados) e simuladores. Não depende de interface gráfica."""
import json
import re

EPS = "ε"


# ---------------------------------------------------------------- AFND
def carregar_afnd(caminho):
    with open(caminho, encoding="utf-8") as f:
        afnd = json.load(f)
    for a in afnd["alfabeto"]:
        if len(a) != 1 or not a.isalnum():
            raise ValueError(f"Símbolo inválido '{a}': use um caractere alfanumérico.")
    return afnd


def _mover(afnd, conjunto, simbolo):
    destino = set()
    for s in conjunto:
        destino.update(afnd["transicoes"].get(s, {}).get(simbolo, []))
    return destino


def fecho_epsilon(afnd, conjunto):
    fecho, pilha = set(conjunto), list(conjunto)
    while pilha:
        for t in afnd["transicoes"].get(pilha.pop(), {}).get(EPS, []):
            if t not in fecho:
                fecho.add(t)
                pilha.append(t)
    return fecho


# ------------------------------------------------- AFND -> AFD (subconjuntos)
def nome_conjunto(afnd, conj):
    ordem = {s: i for i, s in enumerate(afnd["estados"])}
    return "{" + ",".join(sorted(conj, key=ordem.get)) + "}" if conj else "∅"


def construir_afd(afnd):
    ordem = {s: i for i, s in enumerate(afnd["estados"])}
    ordenar = lambda conj: sorted(conj, key=ordem.get)

    def nome(conj):
        return nome_conjunto(afnd, conj)

    inicial = frozenset(fecho_epsilon(afnd, {afnd["inicial"]}))
    fila, vistos, delta, passos = [inicial], {inicial}, {}, []
    while fila:
        S = fila.pop(0)
        for a in afnd["alfabeto"]:
            mov = _mover(afnd, S, a)
            T = frozenset(fecho_epsilon(afnd, mov))
            delta[(nome(S), a)] = nome(T)
            passos.append({"origem": nome(S), "simbolo": a,
                           "mover": nome(mov), "destino": nome(T),
                           "novo": T not in vistos,
                           "origem_conj": ordenar(S), "mover_conj": ordenar(mov),
                           "destino_conj": ordenar(T)})
            if T not in vistos:
                vistos.add(T)
                fila.append(T)

    estados = []
    for (s, _a) in delta:
        if s not in estados:
            estados.append(s)
    finais_nfa = set(afnd["finais"])
    finais = [s for s in estados
              if s != "∅" and set(s.strip("{}").split(",")) & finais_nfa]
    return {"estados": estados, "alfabeto": list(afnd["alfabeto"]),
            "inicial": nome(inicial), "finais": finais,
            "delta": delta, "passos": passos}


def simular(afd, palavra):
    """Retorna (passos, aceita). Cada passo = (origem, símbolo, destino);
    destino None indica símbolo fora do alfabeto (rejeição imediata)."""
    atual, passos = afd["inicial"], []
    for c in palavra:
        destino = afd["delta"].get((atual, c))
        passos.append((atual, c, destino))
        if destino is None:
            return passos, False
        atual = destino
    return passos, atual in afd["finais"]


# --------------------------------------------- AFD -> ER (eliminação de estados)
def _atomo(r):
    if len(r) == 1:
        return True
    if r[0] != "(":
        return False
    prof = 0
    for i, ch in enumerate(r):
        prof += (ch == "(") - (ch == ")")
        if prof == 0:
            return i == len(r) - 1
    return False


def _tem_uniao(r):
    prof = 0
    for ch in r:
        prof += (ch == "(") - (ch == ")")
        if ch == "|" and prof == 0:
            return True
    return False


def _uniao(a, b):
    if a is None:
        return b
    if b is None or a == b:
        return a
    if a == "":
        return b + "?" if _atomo(b) else f"({b})?"
    if b == "":
        return a + "?" if _atomo(a) else f"({a})?"
    return f"{a}|{b}"


def _cat(a, b):
    if a is None or b is None:
        return None
    par = lambda r: f"({r})" if _tem_uniao(r) else r
    return par(a) + par(b)


def _estrela(r):
    if not r:
        return ""
    if _atomo(r) or (r.endswith("*") and _atomo(r[:-1])):
        return r + "*"
    return f"({r})*"


def _alcancaveis(inicios, adj):
    vis, pilha = set(inicios), list(inicios)
    while pilha:
        for t in adj.get(pilha.pop(), []):
            if t not in vis:
                vis.add(t)
                pilha.append(t)
    return vis


IN, OUT = "«início»", "«fim»"


def automato_para_regex(estados, inicial, finais, arestas):
    """Gera a expressão regular por eliminação de estados; '' representa ε."""
    frente, tras = {}, {}
    for s, _r, t in arestas:
        frente.setdefault(s, []).append(t)
        tras.setdefault(t, []).append(s)
    uteis = _alcancaveis([inicial], frente) & _alcancaveis(finais, tras)
    if inicial not in uteis:
        return "∅"
    R = {}

    def add(i, j, r):
        R[(i, j)] = _uniao(R.get((i, j)), r)

    add(IN, inicial, "")
    for f in finais:
        if f in uteis:
            add(f, OUT, "")
    for s, r, t in arestas:
        if s in uteis and t in uteis:
            add(s, t, r)

    restantes = [s for s in estados if s in uteis]
    nos = [IN] + restantes + [OUT]
    for q in restantes:
        nos.remove(q)
        laco = _estrela(R.pop((q, q), None))
        entradas = [(i, R.pop((i, q))) for i in nos if (i, q) in R]
        saidas = [(j, R.pop((q, j))) for j in nos if (q, j) in R]
        for i, ri in entradas:
            for j, rj in saidas:
                add(i, j, _cat(_cat(ri, laco), rj))
    r = R.get((IN, OUT))
    return "∅" if r is None else r


def afd_para_regex(afd):
    """Retorna a ER como string compatível com re.fullmatch ('∅' = linguagem vazia)."""
    arestas = [(s, a, t) for (s, a), t in afd["delta"].items()]
    return automato_para_regex(afd["estados"], afd["inicial"], afd["finais"], arestas)


def aceita_regex(regex, palavra):
    return regex != "∅" and re.fullmatch(regex, palavra) is not None


def ler_sentencas(caminho):
    """Uma sentença por linha; 'ε' representa a palavra vazia."""
    with open(caminho, encoding="utf-8") as f:
        linhas = [l.strip() for l in f if l.strip()]
    return ["" if l == EPS else l for l in linhas]
