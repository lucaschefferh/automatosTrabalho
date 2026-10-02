# AFND → AFD e Expressão Regular

Trabalho de Linguagens Regulares (Autômatos, 6º semestre). A ferramenta recebe um
**AFND** (com ou sem transições ε) e mostra:

1. a construção do **AFD equivalente** passo a passo (construção de subconjuntos);
2. a **expressão regular** da linguagem (eliminação de estados);
3. o teste de **sentenças** lidas de um arquivo, usando o AFD e a ER.

## Como executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

O Streamlit abre a interface no navegador (por padrão em http://localhost:8501).
O programa deve ser executado dentro desta pasta, pois lê o `afnd.json` pelo caminho relativo.

## Arquivos

| Arquivo | Função |
|---|---|
| `app.py` | Interface Streamlit (as quatro abas e os desenhos dos grafos em DOT) |
| `automato.py` | Núcleo teórico: ε-fecho, construção de subconjuntos, simulação do AFD, AFND → ER e teste da ER |
| `afnd.json` | AFND carregado ao abrir o app (valor inicial dos campos da aba 1) |
| `entrada.txt` | Arquivo de exemplo com 5 sentenças para enviar na aba "Testar sentenças" |
| `requirements.txt` | Dependências (`pip install -r requirements.txt`) |

## Formato do `afnd.json`

```json
{
  "estados": ["q0", "q1", "q2"],
  "alfabeto": ["a", "b"],
  "inicial": "q0",
  "finais": ["q2"],
  "transicoes": {
    "q0": {"a": ["q0", "q1"], "b": ["q0"]},
    "q1": {"b": ["q2"]},
    "q2": {}
  }
}
```

- Símbolos do alfabeto têm **um único caractere alfanumérico**.
- `transicoes[estado][símbolo]` é a **lista** de estados de destino (não determinismo).
- Transições vazias usam o símbolo `"ε"` (não faz parte do alfabeto).
- A chave `_comentario`, se existir, é ignorada.

## As abas do programa

### 1. Entrada (AFND)
Permite editar o autômato: estados, alfabeto, estado inicial, estados finais e a
**tabela de transição** (cada célula aceita destinos separados por vírgula; célula vazia =
sem transição). A coluna ε é incluída marcando a caixa correspondente. Há validação
(estados repetidos, símbolo fora do alfabeto, destino desconhecido etc.) e, se tudo
estiver correto, o diagrama do AFND é desenhado. Enquanto houver erros, as demais abas
não são exibidas.

### 2. Equivalência: construção do AFD
- **Tabela de transição do AFND** (à esquerda) com `→` no estado inicial, `*` nos finais e
  `∅` onde não há transição; a coluna ε aparece se o AFND tiver transições ε.
- **ε-fecho de cada estado** (à direita).
- **Nova tabela de transição (AFD)** logo abaixo. Estados do AFD são conjuntos de
  estados do AFND, como `{q0,q1}`.
- **Construção passo a passo**: controles ⏮ ◀ ▶ ⏵⏵ e um slider. Cada passo mostra, lado a
  lado, o AFND (com o conjunto sendo processado destacado) e o AFD parcial construído até
  ali, além da explicação `mover(S, a)` → `ε-fecho(mover)` → δ(S, a). O botão ⏵⏵ reproduz
  a construção automaticamente, um quadro por segundo.

### 3. Testar sentenças
Envie um `.txt` com **uma sentença por linha** (use `ε` para a palavra vazia). A tabela
mostra, para cada sentença, se o **AFD** e a **ER** aceitam ou rejeitam, e o total de
aceitas e rejeitadas. Sem arquivo enviado, a tabela fica vazia.

O projeto traz o `entrada.txt` como arquivo de exemplo, com 5 sentenças (3 válidas e 2
inválidas para o AFND do `afnd.json`). Ele **não é lido automaticamente**: envie-o pelo
campo de upload da aba. Para outro teste, basta enviar outro `.txt` no mesmo formato.

Abaixo da tabela há a **execução passo a passo do AFD**: escolha uma sentença do arquivo
(ou digite outra) e avance com ⏮ ◀ ▶ ⏵⏵ ou com o slider. Em cada passo o diagrama do AFD
destaca o estado atual (amarelo) e a transição percorrida (vermelha), a sentença mostra o
símbolo lido (vermelho) e o já consumido (cinza), e o texto informa δ(estado, símbolo).
No fim aparece ACEITA (estado final) ou REJEITADA (estado não final ou transição
inexistente).

### 4. Expressão regular
Exibe a ER obtida do AFND e permite testar uma palavra digitada, comparando o resultado
da ER com o do AFND.

## Como funciona

### AFND → AFD (construção de subconjuntos)
1. O estado inicial do AFD é o ε-fecho do estado inicial do AFND.
2. Para cada estado S do AFD e cada símbolo `a`: calcula-se `mover(S, a)` (estados
   alcançáveis por `a` a partir de qualquer estado de S) e depois o ε-fecho do resultado.
3. O conjunto obtido é δ(S, a); se ainda não existia, vira um novo estado do AFD.
4. Repete-se até não surgirem estados novos.
5. Um estado do AFD é **final** se contém algum estado final do AFND.

O **estado vazio (∅) não é criado**: o AFD é parcial, e a ausência de transição significa
rejeição imediata (aparece como `—` na tabela).

### AFND → Expressão regular (eliminação de estados)
1. Acrescenta-se um novo estado inicial (`«início»`) e um novo final (`«fim»`) ao autômato.
   Estados que não estão em nenhum caminho do inicial a um final são descartados.
2. Transições paralelas entre os mesmos estados são unidas com `+`.
3. Cada estado `q` é eliminado: para toda entrada `i → q` e saída `q → j`, cria-se
   `i → j` com rótulo `(i→q)(laço de q)*(q→j)`.
4. O rótulo restante de `«início»` para `«fim»` é a ER. Se não existir, a linguagem é
   vazia e a ER é `∅`.

### Notação da ER
Somente os operadores primários:

| Símbolo | Significado |
|---|---|
| `+` | união |
| justaposição (`ab`) | concatenação |
| `*` | fecho de Kleene (estrela) |
| `( )` | agrupamento |
| `ε` | palavra vazia |
| `∅` | linguagem vazia |

Exemplo: `(a+b)*ab` é o conjunto das palavras sobre {a, b} terminadas em `ab`.

Para testar uma palavra, `aceita_regex` converte a notação para o módulo `re` do Python
(`+` → `|`, `ε` → `()`) e usa `re.fullmatch`.

## Limitações conhecidas

- A ER é gerada automaticamente e pode não ser a forma mais curta possível.
- A execução passo a passo recebe a sentença do arquivo ou digitada; para testar a palavra
  vazia, use uma linha `ε` no arquivo de sentenças.
