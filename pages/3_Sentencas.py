"""Resultados para as sentenças fornecidas no arquivo de entrada."""
import pandas as pd
import streamlit as st

from automato import aceita_regex, afd_para_regex, simular
from interface import carregar_dados


st.set_page_config(page_title="Sentenças", layout="wide")
st.title("Sentenças do arquivo selecionado")
afd, sentencas_padrao = carregar_dados()
sentencas = st.session_state.get("sentencas_carregadas", sentencas_padrao)
nome_arquivo = st.session_state.get("nome_arquivo_carregado", "entrada.txt")
regex = afd_para_regex(afd)
st.caption(f"Arquivo carregado na página AFD: {nome_arquivo}.")

resultados = [simular(afd, sentenca)[1] for sentenca in sentencas]
st.dataframe(
    pd.DataFrame([
        {
            "Sentença": sentenca or "ε",
            "AFD": "ACEITA" if aceita else "REJEITA",
            "Expressão regular": "ACEITA" if aceita_regex(regex, sentenca) else "REJEITA",
        }
        for sentenca, aceita in zip(sentencas, resultados)
    ]),
    hide_index=True,
    use_container_width=True,
)

validas = sum(resultados)
st.write(f"Total: {len(sentencas)} sentenças, {validas} aceitas e {len(sentencas) - validas} rejeitadas.")
if len(sentencas) != 5 or validas != 3:
    st.warning("O enunciado pede 5 sentenças: 3 válidas e 2 inválidas.")
