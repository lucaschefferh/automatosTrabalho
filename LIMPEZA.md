# Registro da limpeza

## Removido

- `gui.py` e os bytecodes associados: interface Tkinter, desenho do AFD, controles de execução e abertura de arquivos.
- `main.py`: versão de terminal, que não é exigida pelo trabalho.
- Da interface Streamlit anterior: edição do AFND na tela, upload de arquivos, comparação visual AFND/AFD e reprodução automática.
- De `automato.py`: simulação direta do AFND, rastreamento de fechos, geração alternativa de ER a partir do AFND e comparação exaustiva.

## Mantido e organizado

- `automato.py`: leitura do AFND, construção do AFD, simulação, geração e execução da expressão regular e leitura das sentenças.
- `app.py`: tela inicial com construção completa e simulação do AFD, usando as sentenças do arquivo ou uma sentença digitada.
- `interface.py`: carregamento dos dados e desenho compartilhado do AFD.
- `pages/2_Expressao_regular.py`: expressão regular e simulação visual passo a passo com sentenças do arquivo ou digitadas manualmente.
- `pages/3_Sentencas.py`: resultados das sentenças carregadas na página inicial, com `entrada.txt` como padrão.
- `afnd.json`: autômato do trabalho. O alfabeto contém `0` e `1`; `ε` é usado apenas em transições vazias. Os destinos repetidos de `δ(2,1)` foram reunidos em `2` e `4`.
- `entrada.txt`: as cinco sentenças fornecidas.
- `README.md`: instruções para instalar as dependências e abrir a interface.
