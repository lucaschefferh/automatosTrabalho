# Simulador de AFD

O programa converte o AFND de `afnd.json` em AFD e analisa as sentenças de `entrada.txt`.

Instale `streamlit` e `pandas` e inicie com:

```bash
python -m pip install streamlit pandas
python -m streamlit run app.py
```

O AFD abre como tela inicial. Escolha o arquivo `.txt` nessa página; as sentenças carregadas também ficam disponíveis na página de expressão regular, onde é possível digitar uma sentença manualmente. Sem upload, o programa usa `entrada.txt`.
