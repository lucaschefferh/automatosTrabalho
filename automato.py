"""Núcleo teórico: AFND -> AFD (construção de subconjuntos), AFND -> ER
(eliminação de estados) e simuladores. Não depende de interface gráfica."""
import re

EPS = "ε"


# ---------------------------------------------------------------- AFND
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


def aceita_afnd(afnd, palavra):
    atuais = fecho_epsilon(afnd, {afnd["inicial"]})
    for c in palavra:
        atuais = fecho_epsilon(afnd, _mover(afnd, atuais, c))
    return bool(atuais & set(afnd["finais"]))


# ------------------------------------------------- AFND -> AFD (subconjuntos)
def nome_conjunto(afnd, conj):
    ordem = {s: i for i, s in enumerate(afnd["estados"])}
    return "{" + ",".join(sorted(conj, key=ordem.get)) + "}" if conj else "∅"


def tabela_fecho(afnd):
    return {s: nome_conjunto(afnd, fecho_epsilon(afnd, {s})) for s in afnd["estados"]}


def construir_afd(afnd):
    """Construção de subconjuntos. O estado vazio (∅) não é criado: a ausência de
    transição já significa rejeição."""
    ordem = {s: i for i, s in enumerate(afnd["estados"])}
    ordenar = lambda conj: sorted(conj, key=ordem.get)

    def nome(conj):
        return nome_conjunto(afnd, conj)

    inicial = frozenset(fecho_epsilon(afnd, {afnd["inicial"]}))
    fila, vistos, delta, passos, estados = [inicial], {inicial}, {}, [], [nome(inicial)]
    while fila:
        S = fila.pop(0)
        for a in afnd["alfabeto"]:
            mov = _mover(afnd, S, a)
            T = frozenset(fecho_epsilon(afnd, mov))
            if not T:
                continue
            delta[(nome(S), a)] = nome(T)
            passos.append({"origem": nome(S), "simbolo": a,
                           "mover": nome(mov), "destino": nome(T),
                           "novo": T not in vistos,
                           "origem_conj": ordenar(S), "mover_conj": ordenar(mov),
                           "destino_conj": ordenar(T)})
            if T not in vistos:
                vistos.add(T)
                fila.append(T)
                estados.append(nome(T))

    finais_nfa = set(afnd["finais"])
    finais = [s for s in estados if set(s.strip("{}").split(",")) & finais_nfa]
    return {"estados": estados, "alfabeto": list(afnd["alfabeto"]),
            "inicial": nome(inicial), "finais": finais,
            "delta": delta, "passos": passos}


def simular(afd, palavra):
    """Retorna (passos, aceita). Cada passo = (origem, símbolo, destino);
    destino None indica ausência de transição (rejeição imediata)."""
    atual, passos = afd["inicial"], []
    for c in palavra:
        destino = afd["delta"].get((atual, c))
        passos.append((atual, c, destino))
        if destino is None:
            return passos, False
        atual = destino
    return passos, atual in afd["finais"]


# --------------------------------------------- AFND -> ER (eliminação de estados)
# Operadores: união "+", concatenação (justaposição), estrela "*" e parênteses.
# None = ∅ (sem caminho); EPS = palavra vazia.
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
        if ch == "+" and prof == 0:
            return True
    return False


def _uniao(a, b):
    if a is None:
        return b
    if b is None or a == b:
        return a
    return f"{a}+{b}"


def _cat(a, b):
    if a is None or b is None:
        return None
    if a == EPS:
        return b
    if b == EPS:
        return a
    par = lambda r: f"({r})" if _tem_uniao(r) else r
    return par(a) + par(b)


def _estrela(r):
    if r is None or r == EPS:
        return EPS
    if r.endswith("*") and _atomo(r[:-1]):
        return r
    return r + "*" if _atomo(r) else f"({r})*"


def _alcancaveis(inicios, adj):
    vis, pilha = set(inicios), list(inicios)
    while pilha:
        for t in adj.get(pilha.pop(), []):
            if t not in vis:
                vis.add(t)
                pilha.append(t)
    return vis


IN, OUT = "«início»", "«fim»"


def afnd_para_regex(afnd):
    """ER obtida do AFND por eliminação de estados ('∅' = linguagem vazia)."""
    inicial, finais = afnd["inicial"], afnd["finais"]
    arestas = [(s, a, t) for s, trans in afnd["transicoes"].items()
               for a, destinos in trans.items() for t in destinos]
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

    add(IN, inicial, EPS)
    for f in finais:
        if f in uteis:
            add(f, OUT, EPS)
    for s, r, t in arestas:
        if s in uteis and t in uteis:
            add(s, t, r)

    restantes = [s for s in afnd["estados"] if s in uteis]
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


def aceita_regex(regex, palavra):
    """Traduz a notação (+ * ε) para a sintaxe do módulo re e testa a palavra."""
    if regex == "∅":
        return False
    padrao = regex.replace("+", "|").replace(EPS, "()")
    return re.fullmatch(padrao, palavra) is not None
