"""Ferramenta de AFND -> AFD e Expressão Regular.  Rodar com:  streamlit run app.py

Abas: 1) entrada do AFND  2) construção do AFD passo a passo
      3) comparação AFND × AFD  4) expressão regular"""
import json
import time

import pandas as pd
import streamlit as st

from automato import (EPS, construir_afd, afnd_para_regex, aceita_regex,
                      aceita_afnd, tabela_fecho, simular)

st.set_page_config(page_title="AFND → AFD & ER", layout="wide")

INTERVALO = 1.0  # segundos entre quadros da reprodução automática
C_ORIGEM, C_DESTINO, C_AMBOS, C_ARESTA = "#ffd43b", "#b2f2bb", "#ffa94d", "#e03131"

# ------------------------------------------------------------------ DOT
def _q(s):
    return '"' + str(s).replace('"', "'") + '"'


CABECALHO = ("digraph { rankdir=LR; bgcolor=transparent; node [fontname=Helvetica]; "
             "edge [fontname=Helvetica]; __i [shape=point width=0.1];")


def afnd_dot(afnd, origem=(), destino=(), ativas=()):
    linhas = [CABECALHO]
    for s in afnd["estados"]:
        forma = "doublecircle" if s in afnd["finais"] else "circle"
        cor = (C_AMBOS if s in origem and s in destino else C_ORIGEM if s in origem
               else C_DESTINO if s in destino else "white")
        linhas.append(f"{_q(s)} [shape={forma} style=filled fillcolor={_q(cor)}];")
    linhas.append(f"__i -> {_q(afnd['inicial'])};")
    grupos = {}
    for s, trans in afnd["transicoes"].items():
        for a, destinos in trans.items():
            for t in destinos:
                grupos.setdefault((s, t), []).append(a)
    for (s, t), simbolos in grupos.items():
        on = (s, t) in ativas
        linhas.append(f"{_q(s)} -> {_q(t)} [label={_q(','.join(simbolos))} "
                      f"color={_q(C_ARESTA if on else 'black')} "
                      f"fontcolor={_q(C_ARESTA if on else 'black')} penwidth={3 if on else 1}];")
    return "\n".join(linhas) + "}"


def afd_dot(afd, ativo=None, aresta=None, visiveis=None, novo=None):
    """visiveis=None desenha o AFD completo; senão só o já construído (lista de passos)."""
    passos = afd["passos"] if visiveis is None else visiveis
    nos = [afd["inicial"]] + [p["destino"] for p in passos]
    nos = [s for s in dict.fromkeys(nos)] if visiveis is not None else afd["estados"]
    expandidos = {p["origem"] for p in passos}
    linhas = [CABECALHO]
    for s in nos:
        forma = "doublecircle" if s in afd["finais"] else "circle"
        cor = C_ORIGEM if s == ativo else C_DESTINO if s == novo else "white"
        estilo = "filled" if s in expandidos or visiveis is None or s in (ativo, novo) else "filled,dashed"
        linhas.append(f"{_q(s)} [shape={forma} style=\"{estilo}\" fillcolor={_q(cor)} "
                      f"color={_q(C_ARESTA if s == ativo else 'black')} "
                      f"penwidth={3 if s == ativo else 1}];")
    linhas.append(f"__i -> {_q(afd['inicial'])};")
    grupos = {}
    for p in passos:
        grupos.setdefault((p["origem"], p["destino"]), []).append(p["simbolo"])
    for (s, t), simbolos in grupos.items():
        on = aresta == (s, t)
        linhas.append(f"{_q(s)} -> {_q(t)} [label={_q(','.join(simbolos))} "
                      f"color={_q(C_ARESTA if on else 'black')} "
                      f"fontcolor={_q(C_ARESTA if on else 'black')} penwidth={3 if on else 1}];")
    return "\n".join(linhas) + "}"


# --------------------------------------------------------------- helpers
@st.cache_data
def preparar(texto_json):
    afnd = json.loads(texto_json)
    afd = construir_afd(afnd)
    regex, passos_re = afnd_para_regex(afnd)
    return afd, regex, passos_re, tabela_fecho(afnd)


def ler_texto(texto):
    return ["" if l.strip() == EPS else l.strip() for l in texto.splitlines() if l.strip()]


def selo(ok):
    return "ACEITA" if ok else "REJEITA"


def texto_regex(r):
    return "∅ (linguagem vazia)" if r == "∅" else (r or "ε (apenas a palavra vazia)")


def mover_passo(chave, delta, n):
    st.session_state[chave] = min(n, max(0, st.session_state[chave] + delta))


def controles(chave, n, sig, rotulo):
    """Slider + botões de passo. Retorna (k, reproduzir). Reinicia se 'sig' mudou."""
    if st.session_state.get("sig_" + chave) != sig:
        st.session_state[chave] = 0
        st.session_state["sig_" + chave] = sig
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 6])
    c1.button("⏮", key=f"r_{chave}", help="Reiniciar", on_click=mover_passo,
              args=(chave, -10**6, n), width="stretch")
    c2.button("◀", key=f"a_{chave}", help="Passo anterior", on_click=mover_passo,
              args=(chave, -1, n), width="stretch")
    c3.button("▶", key=f"p_{chave}", help="Próximo passo", on_click=mover_passo,
              args=(chave, 1, n), width="stretch")
    play = c4.button("⏵⏵", key=f"pl_{chave}", help="Reproduzir do início", type="primary",
                     width="stretch")
    if n > 0:
        c5.slider(rotulo, 0, n, key=chave)
    return (st.session_state[chave] if n > 0 else 0), play


def reproduzir(n, desenhar):
    for k in range(n + 1):
        desenhar(k)
        time.sleep(INTERVALO)


# --------------------------------------------------------------- estado
with open("afnd.json", encoding="utf-8") as f:
    _arq = json.load(f)
_arq.pop("_comentario", None)
base, v = _arq, 0

st.title("AFND → AFD e Expressão Regular")
aba1, aba2, aba3, aba4 = st.tabs(
    ["Entrada (AFND)", "Equivalência: construção do AFD",
     "Comparar AFND × AFD", "Expressão regular"])

# ------------------------------------------------------ 1. entrada do AFND
erros = []
with aba1:
    st.caption("Defina o autômato abaixo. Use **ε** como símbolo para transições vazias.")
    c1, c2 = st.columns(2)
    estados = [x.strip() for x in c1.text_input(
        "Estados (separados por vírgula)", ", ".join(base["estados"]), key=f"est{v}").split(",")
        if x.strip()]
    alfabeto = [x.strip() for x in c1.text_input(
        "Alfabeto (símbolos de 1 caractere)", ", ".join(base["alfabeto"]), key=f"alf{v}").split(",")
        if x.strip()]
    inicial = c2.selectbox("Estado inicial", estados,
                           index=estados.index(base["inicial"]) if base["inicial"] in estados else 0,
                           key=f"ini{v}") if estados else None
    finais = c2.multiselect("Estados finais", estados, key=f"fin{v}",
                            default=[f for f in base["finais"] if f in estados])

    usa_eps = st.checkbox("Incluir coluna ε (transições vazias)", key=f"eps{v}",
                          value=any(EPS in t for t in base["transicoes"].values()))
    colunas = alfabeto + ([EPS] if usa_eps else [])

    # Valores digitados sobrevivem a mudanças de estados/alfabeto: guardamos (estado, símbolo) -> texto
    if st.session_state.get("tr_v") != v:
        st.session_state.tr_v = v
        st.session_state.tr_ultimo = {(s, a): ", ".join(ds)
                                      for s, tr in base["transicoes"].items() for a, ds in tr.items()}
    sig = (v, tuple(estados), tuple(colunas))
    if st.session_state.get("tr_sig") != sig:
        st.session_state.tr_sig = sig
        st.session_state.tr_ref = pd.DataFrame(
            [[s] + [st.session_state.tr_ultimo.get((s, a), "") for a in colunas] for s in estados],
            columns=["Estado"] + colunas)

    st.markdown("**Tabela de transição** — linhas: estados · colunas: símbolos · "
                "célula: estados de destino separados por vírgula (vazia = sem transição)")
    tabela = st.data_editor(
        st.session_state.tr_ref, key=f"tr{v}_{abs(hash(sig))}", width="stretch",
        hide_index=True, disabled=["Estado"], num_rows="fixed",
        column_config={a: st.column_config.TextColumn(
            f"δ(·, {a})", help="Ex.: q0, q1") for a in colunas})

    transicoes = {s: {} for s in estados}
    for row in tabela.to_dict("records"):
        for a in colunas:
            texto = str(row.get(a) or "")
            st.session_state.tr_ultimo[(row["Estado"], a)] = texto
            ds = list(dict.fromkeys(x.strip() for x in texto.split(",") if x.strip()))
            if ds:
                transicoes[row["Estado"]][a] = ds

    if not estados:
        erros.append("Informe ao menos um estado.")
    if len(set(estados)) != len(estados):
        erros.append("Há estados repetidos.")
    if not alfabeto:
        erros.append("Informe o alfabeto.")
    erros += [f"Símbolo inválido '{a}': use um único caractere alfanumérico."
              for a in alfabeto if len(a) != 1 or not a.isalnum()]
    for s, tr in transicoes.items():
        for a, ds in tr.items():
            if s not in estados:
                erros.append(f"Origem desconhecida: {s}")
            if a != EPS and a not in alfabeto:
                erros.append(f"Símbolo '{a}' (de {s}) não está no alfabeto.")
            erros += [f"Destino desconhecido '{d}' em δ({s},{a})." for d in ds if d not in estados]
    erros = list(dict.fromkeys(erros))

    if erros:
        for e in erros:
            st.error(e)
    else:
        afnd = {"estados": estados, "alfabeto": alfabeto, "inicial": inicial,
                "finais": finais, "transicoes": transicoes}
        texto_json = json.dumps(afnd, ensure_ascii=False, sort_keys=True)
        st.graphviz_chart(afnd_dot(afnd), width="stretch")

if erros:
    st.stop()

afd, regex, _passos_re, fechos = preparar(texto_json)

# ----------------------------------------------- 2. construção passo a passo
with aba2:
    with st.expander("Como funciona a construção de subconjuntos", expanded=False):
        st.markdown(
            "1. O **estado inicial do AFD** é o ε-fecho do estado inicial do AFND.\n"
            "2. Para cada estado do AFD *S* (um **conjunto** de estados do AFND) e cada símbolo *a*: "
            "`mover(S, a)` = estados alcançáveis por *a* a partir de qualquer estado de *S*; "
            "depois aplica-se o **ε-fecho**.\n"
            "3. O conjunto obtido é o destino δ(S, a). Se ainda não existe, vira um novo estado do AFD.\n"
            "4. Repete-se até não surgirem estados novos. O conjunto vazio ∅ é o estado de erro.\n"
            "5. Um estado do AFD é **final** se contém algum estado final do AFND.")
    if any(EPS in t for t in transicoes.values()):
        st.markdown("**ε-fecho de cada estado do AFND**")
        st.dataframe(pd.DataFrame({"Estado": list(fechos), "ε-fecho": list(fechos.values())}),
                     hide_index=True)

    N = len(afd["passos"])
    k, play = controles("k_constr", N, texto_json, "Passo da construção")
    esq, dir_ = st.columns(2)
    esq.markdown("**AFND** (destacado: conjunto sendo processado)")
    dir_.markdown("**AFD** sendo construído")
    g_afnd, g_afd = esq.empty(), dir_.empty()
    explic = st.empty()

    def desenhar_constr(k):
        if k == 0:
            ini = afd["inicial"]
            g_afnd.graphviz_chart(afnd_dot(afnd, origem=ini.strip("{}").split(",")), width="stretch")
            g_afd.graphviz_chart(afd_dot(afd, visiveis=[], ativo=ini), width="stretch")
            explic.info(f"**Estado inicial do AFD** = ε-fecho({{{afnd['inicial']}}}) = **{ini}**")
            return
        p = afd["passos"][k - 1]
        g_afnd.graphviz_chart(
            afnd_dot(afnd, origem=p["origem_conj"], destino=p["destino_conj"]), width="stretch")
        g_afd.graphviz_chart(
            afd_dot(afd, ativo=p["origem"], aresta=(p["origem"], p["destino"]),
                    visiveis=afd["passos"][:k], novo=p["destino"] if p["novo"] else None),
            width="stretch")
        explic.markdown(
            f"**Passo {k}/{N}** — estado do AFD **S = {p['origem']}**, lendo **{p['simbolo']}**\n\n"
            f"- `mover(S, {p['simbolo']})` = **{p['mover']}**\n"
            f"- `ε-fecho(mover)` = **{p['destino']}**\n"
            f"- δ({p['origem']}, {p['simbolo']}) = **{p['destino']}** "
            + ("→ **estado novo**, entra na fila" if p["novo"] else "→ já existia"))
        if k == N:
            st.success("Sem estados novos na fila: construção concluída.")

    if play:
        reproduzir(N, desenhar_constr)
    else:
        desenhar_constr(k)

    st.markdown("**Resultado: tabela de transição do AFD**")
    tab = {s: {a: afd["delta"][(s, a)] for a in afd["alfabeto"]} for s in afd["estados"]}
    df = pd.DataFrame(tab).T
    df.index = [("→ " if s == afd["inicial"] else "") + ("* " if s in afd["finais"] else "") + s
                for s in df.index]
    st.dataframe(df, width="stretch")
    st.caption("→ estado inicial · * estado final (contém algum final do AFND)")

# ------------------------------------------------------------ 3. comparação
with aba3:
    e1, e2 = st.columns(2)
    e1.markdown("**AFND**")
    e1.graphviz_chart(afnd_dot(afnd), width="stretch")
    e2.markdown("**AFD equivalente**")
    e2.graphviz_chart(afd_dot(afd), width="stretch")

    st.divider()
    arquivo = st.file_uploader("Arquivo de sentenças (.txt, uma por linha) — sem ele usa entrada.txt",
                               type="txt")
    if arquivo:
        sentencas = ler_texto(arquivo.getvalue().decode("utf-8"))
    else:
        with open("entrada.txt", encoding="utf-8") as f:
            sentencas = ler_texto(f.read())
    if sentencas:
        st.dataframe(pd.DataFrame([{
            "#": i + 1, "Sentença": s or EPS,
            "AFD": selo(simular(afd, s)[1]), "ER": selo(aceita_regex(regex, s))}
            for i, s in enumerate(sentencas)]), hide_index=True, width="stretch")
        validas = sum(simular(afd, s)[1] for s in sentencas)
        st.caption(f"{validas} aceitas e {len(sentencas) - validas} rejeitadas pelo AFD.")

# ------------------------------------------------------------------- 4. ER
with aba4:
    st.subheader("Expressão regular do autômato")
    st.code(texto_regex(regex), language="text")
    st.caption("Obtida por **eliminação de estados** diretamente sobre o AFND digitado.")

    st.divider()
    st.subheader("Testar uma palavra na ER")
    teste = st.text_input("Palavra", "", key="teste_er", help="Vazio testa a palavra vazia")
    st.write(f"ER: {selo(aceita_regex(regex, teste))} · AFND: {selo(aceita_afnd(afnd, teste))}")
