"""Interface Tkinter: diagrama do AFD e execução passo a passo."""
import math
import tkinter as tk
from tkinter import filedialog

from automato import simular, aceita_regex, ler_sentencas

RAIO = 28
W, H = 820, 520


def calcular_posicoes(afd):
    """Layout em camadas: coluna = distância (BFS) até o estado inicial."""
    nivel, fila = {afd["inicial"]: 0}, [afd["inicial"]]
    while fila:
        s = fila.pop(0)
        for a in afd["alfabeto"]:
            t = afd["delta"].get((s, a))
            if t is not None and t not in nivel:
                nivel[t] = nivel[s] + 1
                fila.append(t)
    colunas = {}
    for s in afd["estados"]:
        colunas.setdefault(nivel.get(s, 0), []).append(s)
    n = len(colunas)
    pos = {}
    for lvl, lista in colunas.items():
        x = W / 2 if n == 1 else 90 + lvl * (W - 180) / (n - 1)
        for k, s in enumerate(lista):
            pos[s] = (x, H * (k + 1) / (len(lista) + 1))
    return pos, nivel


class App:
    def __init__(self, root, afd, regex, arquivo=None):
        self.afd, self.regex = afd, regex
        self.pos, self.nivel = calcular_posicoes(afd)
        self.pares = {(s, t) for (s, _a), t in afd["delta"].items()}
        self.sentencas, self.passos, self.aceita, self.i, self.job = [], [], False, 0, None
        self.palavra = ""

        root.title("Simulador de AFD e Expressão Regular")
        esq = tk.Frame(root)
        esq.pack(side="left", padx=6, pady=6)
        dir_ = tk.Frame(root)
        dir_.pack(side="right", fill="y", padx=6, pady=6)

        self.canvas = tk.Canvas(esq, width=W, height=H, bg="white", relief="sunken", bd=1)
        self.canvas.pack()
        self.fita = tk.Canvas(esq, width=W, height=60, bg="#f4f4f4")
        self.fita.pack(pady=4, fill="x")
        self.lbl_res = tk.Label(esq, text="", font=("Helvetica", 14, "bold"))
        self.lbl_res.pack()

        tk.Label(dir_, text="Expressão regular:", font=("Helvetica", 10, "bold")).pack(anchor="w")
        tk.Label(dir_, text=regex or "ε", font=("Courier", 10), wraplength=300,
                 justify="left", fg="#0645ad").pack(anchor="w", pady=(0, 8))

        tk.Button(dir_, text="Abrir arquivo de sentenças", command=self.abrir).pack(fill="x")
        self.lista = tk.Listbox(dir_, width=42, height=8, font=("Courier", 11), exportselection=False)
        self.lista.pack(pady=4)
        self.lista.bind("<<ListboxSelect>>", self.selecionar)
        tk.Button(dir_, text="Executar todas (AFD × ER)", command=self.executar_todas).pack(fill="x")

        linha = tk.Frame(dir_)
        linha.pack(fill="x", pady=6)
        self.entrada = tk.Entry(linha, font=("Courier", 11))
        self.entrada.pack(side="left", fill="x", expand=True)
        tk.Button(linha, text="Usar", command=self.usar_digitada).pack(side="left", padx=2)

        ctrl = tk.Frame(dir_)
        ctrl.pack(fill="x")
        for txt, cmd in (("⏮ Reiniciar", self.reiniciar), ("⏭ Passo", self.passo),
                         ("▶ Auto", self.auto)):
            tk.Button(ctrl, text=txt, command=cmd).pack(side="left", expand=True, fill="x")
        self.vel = tk.Scale(dir_, from_=200, to=2000, orient="horizontal",
                            label="Intervalo (ms)", resolution=100)
        self.vel.set(900)
        self.vel.pack(fill="x")

        tk.Label(dir_, text="Registro da execução:", font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.log = tk.Text(dir_, width=42, height=12, font=("Courier", 10), state="disabled")
        self.log.pack()

        self.desenhar()
        self.desenhar_fita()
        if arquivo:
            self.carregar_arquivo(arquivo)

    # ------------------------------------------------------------ desenho
    def _estado_atual(self):
        return self.passos[self.i - 1][2] if self.i else self.afd["inicial"]

    def desenhar(self):
        c = self.canvas
        c.delete("all")
        ativo = self._estado_atual()
        aresta = self.passos[self.i - 1][::2] if self.i else None  # (origem, destino)
        self._desenhar_arestas(aresta)
        for s, (x, y) in self.pos.items():
            cor = "#ffe066" if s == ativo else "white"
            c.create_oval(x - RAIO, y - RAIO, x + RAIO, y + RAIO, fill=cor, width=2)
            if s in self.afd["finais"]:
                c.create_oval(x - RAIO + 5, y - RAIO + 5, x + RAIO - 5, y + RAIO - 5, width=2)
            c.create_text(x, y, text=s, font=("Helvetica", 9, "bold"))
        x, y = self.pos[self.afd["inicial"]]
        c.create_line(x - RAIO - 45, y, x - RAIO, y, arrow="last", width=2)

    def _desenhar_arestas(self, ativa):
        grupos = {}
        for (s, a), t in self.afd["delta"].items():
            grupos.setdefault((s, t), []).append(a)
        for (s, t), simbolos in grupos.items():
            self._aresta(s, t, ",".join(simbolos), ativa == (s, t))

    def _aresta(self, s, t, rotulo, ativa):
        c = self.canvas
        cor, larg = ("#d62828", 3) if ativa else ("black", 1.5)
        x1, y1 = self.pos[s]
        x2, y2 = self.pos[t]
        if s == t:
            c.create_line(x1 - 12, y1 - RAIO + 2, x1 - 24, y1 - RAIO - 32,
                          x1 + 24, y1 - RAIO - 32, x1 + 12, y1 - RAIO + 2,
                          smooth=True, arrow="last", fill=cor, width=larg)
            c.create_text(x1, y1 - RAIO - 42, text=rotulo, fill=cor, font=("Helvetica", 11, "bold"))
            return
        dx, dy = x2 - x1, y2 - y1
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        nx, ny = -uy, ux
        reverso = (t, s) in self.pares
        curva = reverso or abs(self.nivel.get(s, 0) - self.nivel.get(t, 0)) > 1
        if not curva:
            c.create_line(x1 + ux * RAIO, y1 + uy * RAIO, x2 - ux * RAIO, y2 - uy * RAIO,
                          arrow="last", fill=cor, width=larg)
            c.create_text((x1 + x2) / 2 + nx * 12, (y1 + y2) / 2 + ny * 12, text=rotulo,
                          fill=cor, font=("Helvetica", 11, "bold"))
            return
        cx, cy = (x1 + x2) / 2 + nx * 60, (y1 + y2) / 2 + ny * 60
        vs = math.hypot(cx - x1, cy - y1)
        ve = math.hypot(cx - x2, cy - y2)
        p1 = (x1 + (cx - x1) / vs * RAIO, y1 + (cy - y1) / vs * RAIO)
        p2 = (x2 + (cx - x2) / ve * RAIO, y2 + (cy - y2) / ve * RAIO)
        c.create_line(*p1, cx, cy, *p2, smooth=True, arrow="last", fill=cor, width=larg)
        mx = 0.25 * p1[0] + 0.5 * cx + 0.25 * p2[0]
        my = 0.25 * p1[1] + 0.5 * cy + 0.25 * p2[1]
        c.create_text(mx + nx * 10, my + ny * 10, text=rotulo, fill=cor,
                      font=("Helvetica", 11, "bold"))

    def desenhar_fita(self):
        f = self.fita
        f.delete("all")
        f.create_text(8, 10, anchor="w", text="Sentença:", font=("Helvetica", 9))
        if not self.palavra:
            f.create_text(8, 38, anchor="w", text="ε (palavra vazia)", font=("Courier", 12))
            return
        for k, ch in enumerate(self.palavra):
            x = 10 + k * 36
            lido = k < self.i
            proximo = k == self.i
            fill = "#b7e4c7" if lido else ("#ffe066" if proximo else "white")
            f.create_rectangle(x, 22, x + 32, 54, fill=fill, width=2 if proximo else 1)
            f.create_text(x + 16, 38, text=ch, font=("Courier", 14, "bold"))

    # ---------------------------------------------------------- execução
    def _log(self, texto, limpar=False):
        self.log.config(state="normal")
        if limpar:
            self.log.delete("1.0", "end")
        else:
            self.log.insert("end", texto + "\n")
            self.log.see("end")
        self.log.config(state="disabled")

    def carregar_palavra(self, palavra):
        self.parar()
        self.palavra = palavra
        self.passos, self.aceita = simular(self.afd, palavra)
        self.reiniciar()

    def reiniciar(self):
        self.parar()
        self.i = 0
        self._log("", limpar=True)
        self._log(f"Início em {self.afd['inicial']}")
        self.lbl_res.config(text="")
        self.desenhar()
        self.desenhar_fita()

    def passo(self):
        if self.i >= len(self.passos):
            self._finalizar()
            return False
        origem, simbolo, destino = self.passos[self.i]
        self.i += 1
        if destino is None:
            self._log(f"'{simbolo}' ∉ alfabeto → rejeita")
        else:
            self._log(f"δ({origem}, {simbolo}) = {destino}")
        self.desenhar()
        self.desenhar_fita()
        if self.i >= len(self.passos) or destino is None:
            self._finalizar()
            return False
        return True

    def _finalizar(self):
        self.i = len(self.passos)
        self.desenhar()
        self.desenhar_fita()
        re_ok = aceita_regex(self.regex, self.palavra)
        txt = (f"AFD: {'ACEITA ✓' if self.aceita else 'REJEITA ✗'}    "
               f"ER: {'ACEITA ✓' if re_ok else 'REJEITA ✗'}")
        self.lbl_res.config(text=txt, fg="#2d6a4f" if self.aceita else "#d62828")
        self._log(f"Estado final {self._estado_atual()}: "
                  f"{'aceita' if self.aceita else 'rejeita'}")
        self.parar()

    def auto(self):
        if self.job:
            return
        if self.i >= len(self.passos) and self.lbl_res.cget("text"):
            self.reiniciar()

        def tick():
            self.job = None
            if self.passo():
                self.job = self.canvas.after(self.vel.get(), tick)
        tick()

    def parar(self):
        if self.job:
            self.canvas.after_cancel(self.job)
            self.job = None

    # ---------------------------------------------------------- sentenças
    def abrir(self):
        caminho = filedialog.askopenfilename(filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if caminho:
            self.carregar_arquivo(caminho)

    def carregar_arquivo(self, caminho):
        self.sentencas = ler_sentencas(caminho)
        self.lista.delete(0, "end")
        for s in self.sentencas:
            self.lista.insert("end", s or "ε")
        if self.sentencas:
            self.lista.selection_set(0)
            self.carregar_palavra(self.sentencas[0])

    def selecionar(self, _evento):
        sel = self.lista.curselection()
        if sel:
            self.carregar_palavra(self.sentencas[sel[0]])

    def usar_digitada(self):
        self.carregar_palavra(self.entrada.get().strip().replace("ε", ""))

    def executar_todas(self):
        marca = lambda ok: "✓" if ok else "✗"
        sel = self.lista.curselection()
        for k, s in enumerate(self.sentencas):
            afd_ok = simular(self.afd, s)[1]
            re_ok = aceita_regex(self.regex, s)
            self.lista.delete(k)
            self.lista.insert(k, f"{(s or 'ε'):<14} AFD {marca(afd_ok)}  ER {marca(re_ok)}")
        if sel:
            self.lista.selection_set(sel[0])


def iniciar(afd, regex, arquivo=None):
    root = tk.Tk()
    App(root, afd, regex, arquivo)
    root.mainloop()
