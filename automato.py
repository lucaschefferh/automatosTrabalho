"""Núcleo teórico: AFND -> AFD (construção de subconjuntos), AFD -> ER
(eliminação de estados) e simuladores. Não depende de interface gráfica."""
import json
import re
from itertools import product

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


def trace_afnd(afnd, palavra):
    """Conjuntos de estados ativos do AFND antes de ler e após cada símbolo."""
    atuais = fecho_epsilon(afnd, {afnd["inicial"]})
    conjuntos = [atuais]
    for c in palavra:
        atuais = fecho_epsilon(afnd, _mover(afnd, atuais, c))
        conjuntos.append(atuais)
    return conjuntos


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
    """Eliminação de estados sobre um autômato generalizado.
    arestas: lista de (origem, rótulo, destino); rótulo '' = ε.
    Retorna (regex, passos); cada passo guarda o estado eliminado e a tabela R."""
    frente, tras = {}, {}
    for s, _r, t in arestas:
        frente.setdefault(s, []).append(t)
        tras.setdefault(t, []).append(s)
    uteis = _alcancaveis([inicial], frente) & _alcancaveis(finais, tras)
    if inicial not in uteis:
        return "∅", [{"titulo": "Nenhum estado final é alcançável: linguagem vazia (∅).",
                      "removido": None, "R": {}, "nos": []}]
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
    passos = [{"titulo": "Autômato generalizado: novo estado inicial e novo estado final, "
                         "transições paralelas unidas com |",
               "removido": None, "R": dict(R), "nos": list(nos)}]
    for q in restantes:
        nos.remove(q)
        laco = _estrela(R.pop((q, q), None))
        entradas = [(i, R.pop((i, q))) for i in nos if (i, q) in R]
        saidas = [(j, R.pop((q, j))) for j in nos if (q, j) in R]
        for i, ri in entradas:
            for j, rj in saidas:
                add(i, j, _cat(_cat(ri, laco), rj))
        passos.append({"titulo": f"Eliminando {q}: para cada entrada i→{q} e saída {q}→j, "
                                 f"cria i→j com  (i→{q})(laço de {q})*(({q}→j))",
                       "removido": q, "R": dict(R), "nos": list(nos)})
    r = R.get((IN, OUT))
    return ("∅" if r is None else r), passos


def afnd_para_regex(afnd):
    """ER obtida diretamente do AFND (ε vira rótulo vazio). Retorna (regex, passos)."""
    arestas = [(s, "" if a == EPS else a, t)
               for s, trans in afnd["transicoes"].items()
               for a, destinos in trans.items() for t in destinos]
    return automato_para_regex(afnd["estados"], afnd["inicial"], afnd["finais"], arestas)


def afd_para_regex(afd):
    """Retorna a ER como string compatível com re.fullmatch ('∅' = linguagem vazia)."""
    arestas = [(s, a, t) for (s, a), t in afd["delta"].items()]
    return automato_para_regex(afd["estados"], afd["inicial"], afd["finais"], arestas)[0]


def aceita_regex(regex, palavra):
    return regex != "∅" and re.fullmatch(regex, palavra) is not None


# ------------------------------------------------------------- verificação
def verificar_equivalencia(afnd, afd, regex, max_len=8):
    """Compara AFND, AFD e ER em todas as palavras até max_len. Retorna divergências."""
    divergentes = []
    for n in range(max_len + 1):
        for tupla in product(afnd["alfabeto"], repeat=n):
            w = "".join(tupla)
            r1, r2, r3 = (aceita_afnd(afnd, w), simular(afd, w)[1],
                          aceita_regex(regex, w))
            if not (r1 == r2 == r3):
                divergentes.append((w, r1, r2, r3))
    return divergentes


def verificar_regex(afnd, regex, max_len=8):
    """Palavras (até max_len) em que a ER e o AFND discordam."""
    divergentes = []
    for n in range(max_len + 1):
        for tupla in product(afnd["alfabeto"], repeat=n):
            w = "".join(tupla)
            esperado, obtido = aceita_afnd(afnd, w), aceita_regex(regex, w)
            if esperado != obtido:
                divergentes.append((w, esperado, obtido))
    return divergentes


def ler_sentencas(caminho):
    """Uma sentença por linha; 'ε' representa a palavra vazia."""
    with open(caminho, encoding="utf-8") as f:
        linhas = [l.strip() for l in f if l.strip()]
    return ["" if l == EPS else l for l in linhas]
