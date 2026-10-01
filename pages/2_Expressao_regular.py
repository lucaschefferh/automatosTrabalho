"""Exibe e executa a expressão regular com simulação do AFD."""
import streamlit as st

from automato import aceita_regex, afd_para_regex, simular
from interface import carregar_dados, diagrama


st.set_page_config(page_title="Expressão regular", layout="wide")
st.title("Expressão regular")
afd, sentencas_padrao = carregar_dados()
regex = afd_para_regex(afd)
sentencas = st.session_state.get("sentencas_carregadas", sentencas_padrao)
nome_arquivo = st.session_state.get("nome_arquivo_carregado", "entrada.txt")

st.subheader("Expressão regular equivalente")
st.code(regex or "ε", language="text")

origem_sentenca = st.radio(
    "Sentença para testar",
    ["Arquivo carregado", "Digitar sentença"],
    horizontal=True,
)
if origem_sentenca == "Digitar sentença":
    indice = None
    palavra = st.text_input("Digite a sentença", key="sentenca_manual_regex")
elif sentencas:
    st.caption(f"Sentenças carregadas na página AFD: {nome_arquivo}.")
    indice = st.selectbox(
        "Sentença para simular",
        range(len(sentencas)),
        format_func=lambda i: f"{i + 1}. {sentencas[i] or 'ε'}",
    )
    palavra = sentencas[indice]
else:
    indice = None
    palavra = ""
    st.warning("O arquivo escolhido não contém sentenças.")

assinatura = (nome_arquivo, origem_sentenca, indice, palavra)
if st.session_state.get("assinatura_simulacao_regex") != assinatura:
    st.session_state.assinatura_simulacao_regex = assinatura
    st.session_state.passo_simulacao_regex = 0

passos, aceita_afd = simular(afd, palavra)
st.subheader("Simulação passo a passo")
st.session_state.passo_simulacao_regex = min(
    st.session_state.get("passo_simulacao_regex", 0), len(passos)
)
col_anterior, col_proximo, col_reiniciar = st.columns(3)
if col_anterior.button(
    "Anterior",
    disabled=st.session_state.passo_simulacao_regex == 0,
    key="regex_sim_anterior",
):
    st.session_state.passo_simulacao_regex -= 1
if col_proximo.button(
    "Próximo",
    disabled=st.session_state.passo_simulacao_regex >= len(passos),
    key="regex_sim_proximo",
):
    st.session_state.passo_simulacao_regex += 1
if col_reiniciar.button("Reiniciar simulação", key="regex_sim_reiniciar"):
    st.session_state.passo_simulacao_regex = 0

posicao = st.session_state.passo_simulacao_regex
atual = afd["inicial"] if posicao == 0 else passos[posicao - 1][0]
aresta = None
if posicao:
    origem, simbolo, destino = passos[posicao - 1]
    if destino is not None:
        atual = destino
        aresta = (origem, destino)

st.graphviz_chart(diagrama(afd, atual, aresta), use_container_width=True)
st.caption(f"Arquivo: {nome_arquivo} · Símbolos lidos: {posicao} de {len(palavra)}")
if posicao:
    origem, simbolo, destino = passos[posicao - 1]
    if destino is None:
        st.write(f"Símbolo **{simbolo}** fora do alfabeto: a sentença é rejeitada.")
    else:
        st.write(f"Lendo **{simbolo}**: δ({origem}, {simbolo}) = **{destino}**.")
if posicao == len(passos):
    aceita_er = aceita_regex(regex, palavra)
    st.write(f"Resultado do AFD: **{'ACEITA' if aceita_afd else 'REJEITA'}**")
    st.write(f"Resultado da expressão regular: **{'ACEITA' if aceita_er else 'REJEITA'}**")
