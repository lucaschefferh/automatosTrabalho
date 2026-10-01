"""Tela inicial com a construção e a simulação do AFD."""
import pandas as pd
import streamlit as st

from automato import EPS, simular
from interface import carregar_dados, diagrama


st.set_page_config(page_title="AFD", layout="wide")
st.title("Construção e simulação do AFD")
afd, sentencas_padrao = carregar_dados()

arquivo = st.file_uploader(
    "Escolha um arquivo .txt com uma sentença por linha",
    type=["txt"],
)
if arquivo is None:
    sentencas = sentencas_padrao
    nome_arquivo = "entrada.txt"
else:
    nome_arquivo = arquivo.name
    try:
        texto = arquivo.getvalue().decode("utf-8-sig")
    except UnicodeDecodeError:
        st.error("Não foi possível ler o arquivo. Salve-o em UTF-8 e tente novamente.")
        st.stop()
    sentencas = [
        "" if linha.strip() == EPS else linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

st.session_state.sentencas_carregadas = sentencas
st.session_state.nome_arquivo_carregado = nome_arquivo

st.subheader("Construção pelo método dos subconjuntos")
st.caption("Tabela completa da construção do AFD.")
st.dataframe(
    pd.DataFrame([
        {
            "Estado AFD": passo["origem"],
            "Símbolo": passo["simbolo"],
            "Mover": passo["mover"],
            "ε-fecho / destino": passo["destino"],
            "Estado novo": "Sim" if passo["novo"] else "Não",
        }
        for passo in afd["passos"]
    ]),
    hide_index=True,
    use_container_width=True,
)

st.subheader("Simulação passo a passo")
origem_entrada = st.radio(
    "Sentença para simular",
    ["Arquivo selecionado", "Digitar sentença"],
    horizontal=True,
)
if origem_entrada == "Digitar sentença":
    indice = None
    palavra = st.text_input("Digite a sentença", key="sentenca_manual")
elif sentencas:
    indice = st.selectbox(
        "Sentença do arquivo selecionado",
        range(len(sentencas)),
        format_func=lambda i: f"{i + 1}. {sentencas[i] or 'ε'}",
    )
    palavra = sentencas[indice]
else:
    indice = None
    palavra = ""
    st.warning("O arquivo entrada.txt não contém sentenças.")

assinatura = (nome_arquivo, indice, palavra)
if st.session_state.get("assinatura_simulacao") != assinatura:
    st.session_state.assinatura_simulacao = assinatura
    st.session_state.passo_simulacao = 0

passos, aceita = simular(afd, palavra)
st.session_state.passo_simulacao = min(st.session_state.get("passo_simulacao", 0), len(passos))
col_anterior, col_proximo, col_reiniciar = st.columns(3)
if col_anterior.button("Anterior", disabled=st.session_state.passo_simulacao == 0, key="sim_anterior"):
    st.session_state.passo_simulacao -= 1
if col_proximo.button("Próximo", disabled=st.session_state.passo_simulacao >= len(passos), key="sim_proximo"):
    st.session_state.passo_simulacao += 1
if col_reiniciar.button("Reiniciar simulação", key="sim_reiniciar"):
    st.session_state.passo_simulacao = 0

posicao = st.session_state.passo_simulacao
atual = afd["inicial"] if posicao == 0 else passos[posicao - 1][0]
aresta = None
if posicao:
    origem, simbolo, destino = passos[posicao - 1]
    if destino is not None:
        atual = destino
        aresta = (origem, destino)

st.graphviz_chart(diagrama(afd, atual, aresta), use_container_width=True)
st.caption(f"Símbolos lidos: {posicao} de {len(palavra)}")
if posicao:
    origem, simbolo, destino = passos[posicao - 1]
    if destino is None:
        st.write(f"Símbolo **{simbolo}** fora do alfabeto: a sentença é rejeitada.")
    else:
        st.write(f"Lendo **{simbolo}**: δ({origem}, {simbolo}) = **{destino}**.")
if posicao == len(passos):
    st.write(f"Resultado do AFD: **{'ACEITA' if aceita else 'REJEITA'}**")
