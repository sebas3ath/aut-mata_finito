# -*- coding: utf-8 -*-
"""
Simulador de Autómatas Finitos - Estructuras Discretas
Interfaz gráfica con tkinter (incluido con Python). Ejecutar:  python simulador_automatas.py

La sección "LÓGICA DEL AUTÓMATA" contiene los algoritmos; el resto es la interfaz.

Representación del autómata (puedes cambiarla, pero entonces ajusta Grafica):
    automata = {
        "Q":     ["s0", "s1", "s2"],
        "Sigma": ["a", "b"],
        "delta": {("s0", "a"): "s1", ("s0", "b"): "s0", ...},
        "q0":    "s0",
        "F":     ["s2"],
    }
"""
import math
from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox

# =====================================================================
#  LÓGICA DEL AUTÓMATA (lectura de datos, recorrido y búsqueda de palabras)
# =====================================================================

def _separar(texto):
    """Auxiliar: convierte "s0, s1 , ,s2" en ["s0", "s1", "s2"].
    - split(",") parte el texto en cada coma.
    - strip() quita los espacios sobrantes alrededor de cada pedazo.
    - el `if t.strip()` descarta pedazos vacíos (por ejemplo, una coma de más)."""
    return [t.strip() for t in texto.split(",") if t.strip()]


def procesar_estados(texto):
    """Lee y valida el conjunto Q.
    Devuelve (lista_de_estados, None) si es válido o (None, "mensaje de error")."""
    estados = _separar(texto)

    # Regla 1: Q no puede ser vacío (un autómata necesita al menos un estado).
    if not estados:
        return None, "Debes escribir al menos un estado. Intente de nuevo."

    # Regla 2: sin nombres repetidos. Usamos un conjunto `vistos` como "memoria":
    # si un nombre ya está en el conjunto al volver a encontrarlo, está repetido.
    # (Se usa lista para el resultado porque conserva el ORDEN en que el usuario
    # escribió los estados, que luego se usa en la tabla y en la gráfica.)
    vistos = set()
    for e in estados:
        if e in vistos:
            return None, 'El estado "%s" está repetido. Intente de nuevo.' % e
        vistos.add(e)
    return estados, None


def procesar_alfabeto(texto):
    """Lee y valida el alfabeto Σ. Mismo formato de retorno que procesar_estados."""
    simbolos = _separar(texto)

    if not simbolos:
        return None, "Debes escribir al menos un símbolo. Intente de nuevo."

    vistos = set()
    for s in simbolos:
        # Regla: cada símbolo es UN solo carácter (así una palabra como "abab"
        # se puede leer carácter por carácter sin ambigüedad).
        if len(s) != 1:
            return None, 'El símbolo "%s" tiene más de un carácter. Intente de nuevo.' % s
        if s in vistos:
            return None, 'El símbolo "%s" está repetido. Intente de nuevo.' % s
        vistos.add(s)
    return simbolos, None


def procesar_estado(texto, estados):
    """Valida UN estado. Se usa para cada δ(q, s) = ? y para el estado inicial q0:
    en ambos casos la respuesta debe ser un estado que pertenezca a Q."""
    estado = texto.strip()
    if not estado:
        return None, "Falta elegir un estado."
    if estado not in estados:
        return None, "El estado %s no pertenece a Q = {%s}. Intente de nuevo." % (
            estado, ", ".join(estados))
    return estado, None


def procesar_finales(texto, estados):
    """Valida el conjunto F de estados finales. F puede quedar vacío (la interfaz
    avisa que entonces el autómata no reconocerá ninguna palabra)."""
    finales = []
    for e in _separar(texto):
        if e not in estados:
            return None, "El estado %s no pertenece a Q = {%s}. Intente de nuevo." % (
                e, ", ".join(estados))
        if e not in finales:          # si lo escribieron dos veces, se guarda una sola
            finales.append(e)
    return finales, None


def recorrer_palabra(automata, palabra):
    """Simula el autómata sobre `palabra` (la palabra vacía es "").

    ALGORITMO (es exactamente el de clase):
      1. Se parte del estado inicial q0.
      2. Se lee la palabra de izquierda a derecha. Con cada símbolo s, el estado
         actual q pasa a δ(q, s) y se anota el paso (q, s, nuevo_estado).
      3. Al terminar, la palabra es reconocida si y solo si el estado donde quedó
         el autómata pertenece a F.
    Como el autómata es determinista y completo, δ(q, s) siempre existe y es único,
    así que el recorrido de una palabra es UNO solo (no hay que explorar opciones).

    Devuelve {"pasos": [(origen, simbolo, destino), ...],
              "final": estado_donde_termino,
              "aceptada": True/False,
              "error": None  o  (simbolo, posicion)}
    """
    estado = automata["q0"]      # paso 1: empezamos en el estado inicial
    pasos = []

    # enumerate(..., start=1) da la posición humana (1, 2, 3...) que pide el enunciado.
    # Si la palabra es vacía el for no se ejecuta: el autómata se queda en q0, y por
    # eso ε es reconocida solo si q0 es final (caso especial resuelto "gratis").
    for posicion, simbolo in enumerate(palabra, start=1):
        # Símbolo fuera del alfabeto: δ no está definida para él. La palabra se
        # rechaza y se informa cuál símbolo es y en qué posición está.
        if simbolo not in automata["Sigma"]:
            return {"pasos": pasos, "final": estado, "aceptada": False,
                    "error": (simbolo, posicion)}

        # Paso 2: aplicar la función de transición δ(estado, simbolo).
        destino = automata["delta"][(estado, simbolo)]
        pasos.append((estado, simbolo, destino))
        estado = destino

    # Paso 3: decisión final.
    return {"pasos": pasos, "final": estado,
            "aceptada": estado in automata["F"], "error": None}


def palabras_reconocidas(automata, cantidad=5, long_max=10):
    """Devuelve las `cantidad` palabras reconocidas más cortas, en orden canónico
    (primero por longitud; a igual longitud, según el orden en que se ingresó Σ).

    IDEA: búsqueda en anchura (BFS) sobre pares (palabra, estado_donde_queda).
      - Una cola FIFO guarda palabras ya recorridas junto con el estado final de su
        recorrido (así no hay que volver a simular desde cero cada palabra).
      - Se saca la primera de la cola; si su estado es final, es una palabra
        reconocida. Luego se "extiende" con cada símbolo de Σ EN ORDEN y las
        nuevas palabras se meten al final de la cola.
      - Por ser una cola FIFO, siempre salen primero todas las palabras de
        longitud k antes que las de longitud k+1, y como los símbolos se agregan
        en el orden de Σ, dentro de cada longitud salen en orden alfabético.
        Eso es justo el orden canónico: ε, a, b, aa, ab, ba, bb, aaa...

    OPTIMIZACIÓN (poda): se calculan los estados "vivos" = desde los que se puede
    llegar a algún estado final. Si una palabra deja al autómata en un estado NO
    vivo, ninguna extensión suya podrá ser reconocida, así que no se encola.
    Así, si ningún final es alcanzable (autómata A4), la búsqueda termina de
    inmediato en vez de probar miles de palabras inútiles.
    """
    Q, Sigma, delta = automata["Q"], automata["Sigma"], automata["delta"]
    F = set(automata["F"])

    # --- Cálculo de estados vivos (alcanzabilidad hacia atrás) ---
    # Empezamos con los finales (están "vivos": ya aceptan) y repetimos: si un
    # estado q tiene alguna transición hacia un estado vivo, q también está vivo.
    # Se repite hasta que en una vuelta completa no se agregue nada nuevo.
    vivos = set(F)
    cambio = True
    while cambio:
        cambio = False
        for q in Q:
            if q not in vivos and any(delta[(q, s)] in vivos for s in Sigma):
                vivos.add(q)
                cambio = True

    encontradas = []
    if automata["q0"] not in vivos:      # ningún final es alcanzable: no hay palabras
        return encontradas

    cola = deque([("", automata["q0"])])   # ε empieza en q0
    while cola:
        palabra, estado = cola.popleft()

        if estado in F:                    # el recorrido de `palabra` termina en final
            encontradas.append(palabra)
            if len(encontradas) == cantidad:
                break

        # Solo se extiende si aún no llegamos al límite de longitud (10 por defecto).
        if len(palabra) < long_max:
            for s in Sigma:                # en el orden en que se ingresó Σ
                siguiente = delta[(estado, s)]
                if siguiente in vivos:     # poda: solo caminos que aún pueden aceptar
                    cola.append((palabra + s, siguiente))
    return encontradas


# =====================================================================
#  FORMATO DE TEXTO (solo presentación)
# =====================================================================

def fmt_conjunto(xs):
    return "{" + ", ".join(xs) + "}"


def fmt_tupla(a):
    return "M = (%s, %s, δ, %s, %s)" % (
        fmt_conjunto(a["Q"]), fmt_conjunto(a["Sigma"]), a["q0"], fmt_conjunto(a["F"]))


def fmt_tabla(a):
    w = max(len(x) for x in a["Q"] + a["Sigma"]) + 1
    enc = "   " + "δ".ljust(w) + "| " + "  ".join(s.ljust(w) for s in a["Sigma"])
    sep = "-" * (3 + w) + "+" + "-" * (2 + (w + 2) * len(a["Sigma"]))
    filas = [enc, sep]
    for q in a["Q"]:
        marca = ("→" if q == a["q0"] else " ") + ("*" if q in a["F"] else " ") + " "
        celdas = "  ".join(a["delta"][(q, s)].ljust(w) for s in a["Sigma"])
        filas.append(marca + q.ljust(w) + "| " + celdas)
    return "\n".join(filas)


def fmt_recorrido(pasos, inicial):
    if not pasos:
        return inicial
    txt = pasos[0][0]
    for _, s, d in pasos:
        txt += " –%s→ %s" % (s, d)
    return txt


def ver_palabra(p):
    return p if p else "ε"


# =====================================================================
#  ESTILO
# =====================================================================
AZUL_OSC, AZUL, AZUL_CLARO = "#1e293b", "#2563eb", "#dbeafe"
FONDO, BLANCO, TEXTO, GRIS = "#f1f5f9", "#ffffff", "#0f172a", "#64748b"
VERDE, VERDE_CLARO = "#16a34a", "#bbf7d0"
ROJO, ROJO_CLARO = "#dc2626", "#fecaca"
NARANJA, AMARILLO, BORDE = "#ea580c", "#fde68a", "#cbd5e1"
F = "Segoe UI"
MONO = "Consolas"


def _oscurecer(c):
    r, g, b = [int(c[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % (int(r * .85), int(g * .85), int(b * .85))


def boton(master, texto, comando, color=AZUL, fg="white", size=11):
    b = tk.Label(master, text=texto, bg=color, fg=fg, font=(F, size, "bold"),
                 padx=16, pady=8, cursor="hand2")
    b._c = color
    b.bind("<Button-1>", lambda e: comando())
    b.bind("<Enter>", lambda e: b.config(bg=_oscurecer(b._c)))
    b.bind("<Leave>", lambda e: b.config(bg=b._c))
    return b


def recolor(b, color):
    b._c = color
    b.config(bg=color)


# =====================================================================
#  GRÁFICA DEL AUTÓMATA (se dibuja sola a partir de los datos)
# =====================================================================
class Grafica(tk.Canvas):
    def __init__(self, master):
        super().__init__(master, bg=BLANCO, highlightthickness=1, highlightbackground=BORDE)
        self.a, self.pasos, self.actual, self.col = None, (), None, None
        self.bind("<Configure>", lambda e: self.dibujar())

    def mostrar(self, a, pasos=(), actual=None, col=None):
        self.a, self.pasos, self.actual, self.col = a, pasos, actual, col
        self.dibujar()

    def dibujar(self):
        self.delete("all")
        a = self.a
        if not a:
            return
        w, h = self.winfo_width(), self.winfo_height()
        Q = a["Q"]
        n = len(Q)
        R = 28 if n <= 6 else 22
        cx, cy = w / 2, h / 2
        if n == 1:
            pos = {Q[0]: (cx, cy)}
        else:
            rx, ry = max(w / 2 - 110, 40), max(h / 2 - 90, 40)
            ang = lambda i: math.pi + 2 * math.pi * i / n
            pos = {q: (cx + rx * math.cos(ang(i)), cy + ry * math.sin(ang(i)))
                   for i, q in enumerate(Q)}
        grupos = {}
        for q in Q:
            for s in a["Sigma"]:
                grupos.setdefault((q, a["delta"][(q, s)]), []).append(s)
        usados = {(o, d) for o, _, d in self.pasos}

        x, y = pos[a["q0"]]  # flecha de entrada
        self.create_line(x - R - 50, y, x - R, y, arrow=tk.LAST, width=2,
                         fill=AZUL_OSC, arrowshape=(10, 12, 4))
        for (o, d), sims in grupos.items():
            self._flecha(pos, o, d, ", ".join(sims), (o, d) in usados,
                         (d, o) in grupos, R, (cx, cy))
        for q, (x, y) in pos.items():
            relleno = (self.col or AMARILLO) if q == self.actual else AZUL_CLARO
            self.create_oval(x - R, y - R, x + R, y + R, fill=relleno, outline=AZUL_OSC, width=2)
            if q in a["F"]:
                self.create_oval(x - R + 5, y - R + 5, x + R - 5, y + R - 5, outline=AZUL_OSC, width=2)
            self.create_text(x, y, text=q, font=(F, 12 if n <= 6 else 10, "bold"), fill=TEXTO)

    @staticmethod
    def _borde(x, y, tx, ty, R):
        d = math.hypot(tx - x, ty - y) or 1
        return (x + (tx - x) / d * R, y + (ty - y) / d * R)

    def _flecha(self, pos, o, d, txt, activa, doble, R, centro):
        col = NARANJA if activa else "#475569"
        kw = dict(arrow=tk.LAST, fill=col, width=3.5 if activa else 2, arrowshape=(11, 13, 5))
        fuente = (F, 12, "bold")
        x1, y1 = pos[o]
        if o == d:  # bucle hacia afuera del grafo
            ux, uy = x1 - centro[0], y1 - centro[1]
            L = math.hypot(ux, uy)
            ux, uy = (ux / L, uy / L) if L > 1 else (0, -1)
            px, py = -uy, ux
            P = lambda a, b: (x1 + ux * a + px * b, y1 + uy * a + py * b)
            pts = [P(R - 2, -10), P(R + 34, -18), P(R + 34, 18), P(R - 2, 10)]
            self.create_line(*[c for p in pts for c in p], smooth=True, **kw)
            self.create_text(*P(R + 46, 0), text=txt, fill=col, font=fuente)
            return
        x2, y2 = pos[d]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        px, py = -dy / L, dx / L
        if doble:  # dos flechas separadas (una curva a cada lado)
            qx, qy = mx + px * 45, my + py * 45
            s, e = self._borde(x1, y1, qx, qy, R), self._borde(x2, y2, qx, qy, R)
            self.create_line(*s, qx, qy, *e, smooth=True, **kw)
            lx = 0.25 * s[0] + 0.5 * qx + 0.25 * e[0] + px * 14
            ly = 0.25 * s[1] + 0.5 * qy + 0.25 * e[1] + py * 14
        else:
            s, e = self._borde(x1, y1, x2, y2, R), self._borde(x2, y2, x1, y1, R)
            self.create_line(*s, *e, **kw)
            if py > 0:
                px, py = -px, -py
            lx, ly = mx + px * 14, my + py * 14
        self.create_text(lx, ly, text=txt, fill=col, font=fuente)


# =====================================================================
#  VISTAS
# =====================================================================
class Vista(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=FONDO)
        self.app = app

    def al_mostrar(self):
        pass

    def titulo(self, texto, guia):
        tk.Label(self, text=texto, font=(F, 20, "bold"), bg=FONDO, fg=TEXTO).pack(anchor="w", padx=30, pady=(18, 0))
        tk.Label(self, text=guia, font=(F, 11), bg=FONDO, fg=GRIS, justify="left",
                 wraplength=1000).pack(anchor="w", padx=30, pady=(2, 8))


# ------------------------------- MENÚ --------------------------------
class VistaMenu(Vista):
    def __init__(self, master, app):
        super().__init__(master, app)
        tk.Label(self, text="¿Qué quieres hacer hoy?", font=(F, 24, "bold"), bg=FONDO, fg=TEXTO).pack(pady=(32, 4))
        tk.Label(self, text="Sigue los módulos en orden: construye tu autómata, descubre qué palabras reconoce y pruébalo.",
                 font=(F, 12), bg=FONDO, fg=GRIS).pack()
        fila = tk.Frame(self, bg=FONDO)
        fila.pack(pady=28)
        datos = [("1", "Construir el autómata", "Ingresa Q, Σ, δ, q₀ y F paso a paso y mira su gráfica.", "m1"),
                 ("2", "Palabras reconocidas", "Descubre las cinco palabras más cortas que tu autómata reconoce.", "m2"),
                 ("3", "Probar una palabra", "Escribe palabras y comprueba, paso a paso, si el autómata las reconoce.", "m3")]
        self.botones = {}
        for i, (num, tit, desc, dest) in enumerate(datos):
            fila.grid_columnconfigure(i, uniform="t")
            t = tk.Frame(fila, bg=BLANCO, highlightbackground=BORDE, highlightthickness=1, padx=22, pady=22)
            t.grid(row=0, column=i, padx=14, sticky="nsew")
            tk.Label(t, text="MÓDULO " + num, font=(F, 10, "bold"), bg=BLANCO, fg=AZUL).pack(anchor="w")
            tk.Label(t, text=tit, font=(F, 16, "bold"), bg=BLANCO, fg=TEXTO, wraplength=240,
                     justify="left").pack(anchor="w", pady=(4, 8))
            tk.Label(t, text=desc, font=(F, 11), bg=BLANCO, fg=GRIS, wraplength=240,
                     justify="left").pack(anchor="w", pady=(0, 18))
            b = boton(t, "Abrir", lambda d=dest: app.ir_modulo(d))
            b.pack(anchor="w")
            self.botones[dest] = b
        self.estado = tk.Label(self, font=(F, 11), bg=FONDO, wraplength=950, justify="center")
        self.estado.pack(pady=6)
        boton(self, "Salir", app.destroy, color="#94a3b8").pack(pady=14)

    def al_mostrar(self):
        a = self.app.automata
        if a:
            self.estado.config(text="✔ Autómata en memoria:  " + fmt_tupla(a), fg=VERDE)
        else:
            self.estado.config(text="ℹ Aún no hay un autómata en memoria. Empieza por el Módulo 1.", fg=GRIS)
        for d in ("m2", "m3"):
            b = self.botones[d]
            b.config(text="Abrir" if a else "🔒 Primero el Módulo 1")
            recolor(b, AZUL if a else "#94a3b8")


# ------------------------ MÓDULO 1: CONSTRUCCIÓN ----------------------
class VistaM1(Vista):
    PASOS = [
        ("Estados (Q)", "Escribe los nombres de los estados separados por comas.\nEjemplo:  s0, s1, s2",
         "Necesitas al menos un estado y no puedes repetir nombres."),
        ("Alfabeto (Σ)", "Escribe los símbolos que el autómata puede leer, separados por comas.\nEjemplo:  a, b",
         "Cada símbolo es un único carácter y no puede repetirse."),
        ("Función de transición (δ)",
         "Para cada estado y cada símbolo, elige (o escribe) el estado al que pasa el autómata.\n"
         "Por ejemplo, δ(s0, a) = s1 significa que desde s0, al leer a, pasa a s1.",
         "Debes llenar {n} celdas (|Q| × |Σ|) para que el autómata quede completo."),
        ("Estado inicial (q₀)", "Elige el estado en el que el autómata empieza a leer cada palabra.",
         "Debe ser uno de los estados de Q."),
        ("Estados finales (F)", "Escribe uno o varios estados de aceptación separados por comas.\nEjemplo:  s2",
         "Una palabra es reconocida si el autómata termina en uno de estos estados."),
    ]

    def __init__(self, master, app):
        super().__init__(master, app)
        self.titulo("Módulo 1 · Construcción del autómata",
                    "Define los cinco elementos M = (Q, Σ, δ, q₀, F). Al final verás la 5-tupla, la tabla y la gráfica.")
        self.f_form = tk.Frame(self, bg=FONDO)
        self.f_res = tk.Frame(self, bg=FONDO)
        self._armar_form()
        self._armar_res()
        self.reiniciar()

    # ---- armado de contenedores ----
    def _armar_form(self):
        f = self.f_form
        self.paso_lbls = []
        barra = tk.Frame(f, bg=FONDO)
        barra.pack(pady=(4, 10))
        nombres = ["Q", "Σ", "δ", "q₀", "F"]
        for i, n in enumerate(nombres):
            l = tk.Label(barra, text=n, font=(F, 12, "bold"), width=4, pady=5)
            l.grid(row=0, column=2 * i, padx=2)
            self.paso_lbls.append(l)
            if i < 4:
                tk.Label(barra, text="──", bg=FONDO, fg=BORDE).grid(row=0, column=2 * i + 1)
        c = tk.Frame(f, bg=BLANCO, highlightbackground=BORDE, highlightthickness=1, padx=28, pady=22)
        c.pack(fill="x", padx=60, pady=6)
        self.lbl_paso = tk.Label(c, font=(F, 11, "bold"), bg=BLANCO, fg=AZUL)
        self.lbl_paso.pack(anchor="w")
        self.lbl_tit = tk.Label(c, font=(F, 18, "bold"), bg=BLANCO, fg=TEXTO)
        self.lbl_tit.pack(anchor="w")
        self.lbl_guia = tk.Label(c, font=(F, 12), bg=BLANCO, fg=TEXTO, justify="left", wraplength=850)
        self.lbl_guia.pack(anchor="w", pady=(6, 10))
        self.zona = tk.Frame(c, bg=BLANCO)
        self.zona.pack(anchor="w", pady=4)
        self.lbl_hint = tk.Label(c, font=(F, 10, "italic"), bg=BLANCO, fg=GRIS, justify="left", wraplength=850)
        self.lbl_hint.pack(anchor="w", pady=(8, 0))
        self.lbl_err = tk.Label(c, font=(F, 11, "bold"), bg=BLANCO, fg=ROJO, justify="left", wraplength=850)
        self.lbl_err.pack(anchor="w", pady=(6, 0))
        bt = tk.Frame(f, bg=FONDO)
        bt.pack(pady=14)
        self.b_atras = boton(bt, "← Atrás", self.atras, color="#94a3b8")
        self.b_atras.grid(row=0, column=0, padx=6)
        self.b_sig = boton(bt, "Siguiente →", self.siguiente)
        self.b_sig.grid(row=0, column=1, padx=6)
        self.b_ej = boton(bt, "Cargar ejemplo A2 (terminan en ab)", self.cargar_ejemplo, color="#7c3aed", size=10)
        self.b_ej.grid(row=0, column=2, padx=20)

    def _armar_res(self):
        f = self.f_res
        cuerpo = tk.Frame(f, bg=FONDO)
        cuerpo.pack(fill="both", expand=True, padx=30)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)
        izq = tk.Frame(cuerpo, bg=BLANCO, highlightbackground=BORDE, highlightthickness=1, padx=14, pady=12)
        izq.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        tk.Label(izq, text="Autómata construido", font=(F, 13, "bold"), bg=BLANCO, fg=TEXTO).pack(anchor="w")
        tk.Label(izq, text="→ estado inicial     * estado final", font=(F, 9), bg=BLANCO, fg=GRIS).pack(anchor="w")
        self.txt = tk.Text(izq, width=46, height=16, font=(MONO, 11), bg=BLANCO, relief="flat", wrap="none")
        self.txt.pack(pady=8, fill="y", expand=True)
        tk.Label(izq, text="La gráfica se genera sola a partir de tus datos.", font=(F, 9, "italic"),
                 bg=BLANCO, fg=GRIS, wraplength=330, justify="left").pack(anchor="w")
        self.grafica = Grafica(cuerpo)
        self.grafica.grid(row=0, column=1, sticky="nsew")
        bt = tk.Frame(f, bg=FONDO)
        bt.pack(pady=12)
        boton(bt, "Construir otro autómata", self.reiniciar_y_mostrar, color="#94a3b8").grid(row=0, column=0, padx=6)
        boton(bt, "Módulo 2 →", lambda: self.app.ir("m2")).grid(row=0, column=1, padx=6)
        boton(bt, "Módulo 3 →", lambda: self.app.ir("m3")).grid(row=0, column=2, padx=6)

    # ---- estado del asistente ----
    def reiniciar(self):
        self.raw = {"Q": "", "S": "", "delta": {}, "q0": "", "F": ""}
        self.val = {}
        self.paso = 0
        self.mostrar_form()

    def reiniciar_y_mostrar(self):
        self.reiniciar()

    def al_mostrar(self):
        if self.app.automata:
            self.mostrar_resultado()

    def mostrar_form(self):
        self.f_res.pack_forget()
        self.f_form.pack(fill="both", expand=True)
        self.mostrar_paso()

    def mostrar_resultado(self):
        a = self.app.automata
        self.f_form.pack_forget()
        self.f_res.pack(fill="both", expand=True)
        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("end", fmt_tupla(a) + "\n\n" + fmt_tabla(a))
        self.txt.config(state="disabled")
        self.grafica.mostrar(a)

    def cargar_ejemplo(self):
        self.raw = {"Q": "s0, s1, s2", "S": "a, b", "q0": "s0", "F": "s2",
                    "delta": {("s0", "a"): "s1", ("s0", "b"): "s0", ("s1", "a"): "s1",
                              ("s1", "b"): "s2", ("s2", "a"): "s1", ("s2", "b"): "s0"}}
        self.val = {}
        self.paso = 0
        self.mostrar_paso()

    # ---- pasos ----
    def mostrar_paso(self):
        for w in self.zona.winfo_children():
            w.destroy()
        self.lbl_err.config(text="")
        p = self.paso
        tit, guia, hint = self.PASOS[p]
        n = len(self.val.get("Q", [])) * len(self.val.get("Sigma", []))
        self.lbl_paso.config(text="PASO %d DE 5" % (p + 1))
        self.lbl_tit.config(text=tit)
        self.lbl_guia.config(text=guia)
        self.lbl_hint.config(text="💡 " + hint.format(n=n))
        for i, l in enumerate(self.paso_lbls):
            if i < p:
                l.config(bg=VERDE, fg="white")
            elif i == p:
                l.config(bg=AZUL, fg="white")
            else:
                l.config(bg="#e2e8f0", fg=GRIS)
        self.b_atras.pack_forget() if False else None
        recolor(self.b_atras, "#94a3b8" if p else "#e2e8f0")
        self.b_sig.config(text="Construir autómata ✔" if p == 4 else "Siguiente →")
        if p == 0:
            self.b_ej.grid()
        else:
            self.b_ej.grid_remove()

        if p in (0, 1, 4):
            self.var = tk.StringVar(value={0: self.raw["Q"], 1: self.raw["S"], 4: self.raw["F"]}[p])
            e = tk.Entry(self.zona, textvariable=self.var, font=(F, 15), width=36, relief="flat",
                         highlightthickness=2, highlightbackground=BORDE, highlightcolor=AZUL)
            e.pack(ipady=6)
            e.bind("<Return>", lambda ev: self.siguiente())
            e.focus_set()
        elif p == 3:
            self.var = tk.StringVar(value=self.raw["q0"])
            c = ttk.Combobox(self.zona, textvariable=self.var, values=self.val["Q"], font=(F, 14), width=12)
            c.pack(ipady=3)
            c.bind("<Return>", lambda ev: self.siguiente())
        else:
            self.celdas = {}
            Q, S = self.val["Q"], self.val["Sigma"]
            for j, s in enumerate(S):
                tk.Label(self.zona, text="símbolo  " + s, font=(F, 11, "bold"), bg=BLANCO, fg=AZUL).grid(row=0, column=j + 1, padx=8)
            for i, q in enumerate(Q):
                tk.Label(self.zona, text="desde  " + q, font=(F, 11, "bold"), bg=BLANCO, fg=TEXTO).grid(row=i + 1, column=0, sticky="e", padx=8, pady=3)
                for j, s in enumerate(S):
                    v = tk.StringVar(value=self.raw["delta"].get((q, s), ""))
                    self.celdas[(q, s)] = v
                    ttk.Combobox(self.zona, textvariable=v, values=Q, width=9, font=(F, 11)).grid(row=i + 1, column=j + 1, padx=8, pady=3)

    def capturar(self):
        p = self.paso
        if p == 0:
            self.raw["Q"] = self.var.get()
        elif p == 1:
            self.raw["S"] = self.var.get()
        elif p == 2:
            for k, v in self.celdas.items():
                self.raw["delta"][k] = v.get()
        elif p == 3:
            self.raw["q0"] = self.var.get()
        else:
            self.raw["F"] = self.var.get()

    def error(self, msg):
        self.lbl_err.config(text="⚠ " + msg)
        return False

    def guardar(self):
        self.capturar()
        ej, p, v = self.app.ejecutar, self.paso, self.val
        if p in (0, 1):
            r = ej(procesar_estados if p == 0 else procesar_alfabeto, self.raw["Q" if p == 0 else "S"])
        elif p == 2:
            delta = {}
            for (q, s), txt in self.raw["delta"].items():
                r = ej(procesar_estado, txt, v["Q"])
                if r is None:
                    return False
                if r[1]:
                    return self.error("δ(%s, %s): %s" % (q, s, r[1]))
                delta[(q, s)] = r[0]
            v["delta"] = delta
            self.lbl_err.config(text="")
            return True
        elif p == 3:
            r = ej(procesar_estado, self.raw["q0"], v["Q"])
        else:
            r = ej(procesar_finales, self.raw["F"], v["Q"])
        if r is None:
            return False
        val, err = r
        if err:
            return self.error(err)
        if p == 0 and val != v.get("Q"):       # cambiaron los estados: lo demás ya no sirve
            self.raw.update(delta={}, q0="", F="")
        if p == 1 and val != v.get("Sigma"):
            self.raw["delta"] = {}
        v[{0: "Q", 1: "Sigma", 3: "q0", 4: "F"}[p]] = val
        self.lbl_err.config(text="")
        return True

    def atras(self):
        if self.paso == 0:
            return
        self.capturar()
        self.paso -= 1
        self.mostrar_paso()

    def siguiente(self):
        if not self.guardar():
            return
        if self.paso < 4:
            self.paso += 1
            self.mostrar_paso()
            return
        v = self.val
        if not v["F"]:
            messagebox.showwarning("Sin estados finales",
                                   "No indicaste estados finales: el autómata no reconocerá ninguna palabra.")
        self.app.automata = {"Q": v["Q"], "Sigma": v["Sigma"], "delta": dict(v["delta"]),
                             "q0": v["q0"], "F": v["F"]}
        self.mostrar_resultado()


# ------------------- MÓDULO 2: PALABRAS RECONOCIDAS -------------------
class VistaM2(Vista):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.titulo("Módulo 2 · Cinco palabras reconocidas",
                    "Estas son las palabras reconocidas más cortas (orden canónico, hasta longitud 10). "
                    "Haz clic en una fila para ver su recorrido sobre la gráfica.")
        cuerpo = tk.Frame(self, bg=FONDO)
        cuerpo.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)
        izq = tk.Frame(cuerpo, bg=FONDO)
        izq.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        self.lbl_m = tk.Label(izq, font=(MONO, 11, "bold"), bg=FONDO, fg=AZUL_OSC, wraplength=480, justify="left")
        self.lbl_m.pack(anchor="w", pady=(0, 8))
        self.lista = tk.Frame(izq, bg=FONDO)
        self.lista.pack(anchor="w")
        self.lbl_info = tk.Label(izq, font=(F, 11, "bold"), bg=FONDO, fg=GRIS, wraplength=480, justify="left")
        self.lbl_info.pack(anchor="w", pady=12)
        self.grafica = Grafica(cuerpo)
        self.grafica.grid(row=0, column=1, sticky="nsew")

    def al_mostrar(self):
        a = self.app.automata
        for w in self.lista.winfo_children():
            w.destroy()
        self.lbl_m.config(text=fmt_tupla(a))
        self.grafica.mostrar(a)
        pals = self.app.ejecutar(palabras_reconocidas, a, 5, 10)
        if pals is None:
            self.lbl_info.config(text="Completa la función palabras_reconocidas para ver los resultados.", fg=ROJO)
            return
        for i, p in enumerate(pals, 1):
            r = self.app.ejecutar(recorrer_palabra, a, p)
            if r is None:
                return
            fila = tk.Frame(self.lista, bg=BLANCO, highlightbackground=BORDE, highlightthickness=1,
                            padx=10, pady=8, cursor="hand2")
            fila.pack(fill="x", pady=3)
            textos = [tk.Label(fila, text="%d." % i, font=(F, 11, "bold"), bg=BLANCO, fg=GRIS, width=3),
                      tk.Label(fila, text=ver_palabra(p), font=(MONO, 14, "bold"), bg=BLANCO, fg=AZUL, width=8, anchor="w"),
                      tk.Label(fila, text=fmt_recorrido(r["pasos"], a["q0"]), font=(MONO, 11), bg=BLANCO, fg=TEXTO)]
            for t in textos:
                t.pack(side="left")
            for w in [fila] + textos:
                w.bind("<Button-1>", lambda e, r=r: self.grafica.mostrar(a, r["pasos"], r["final"], VERDE_CLARO))
        n = len(pals)
        if n == 0:
            self.lbl_info.config(text="Este autómata no reconoce ninguna palabra de longitud menor o igual que 10 "
                                      "(por ejemplo, porque ningún estado final es alcanzable desde el inicial).", fg=ROJO)
        elif n < 5:
            self.lbl_info.config(text="Este autómata solo reconoce %d palabras de longitud menor o igual que 10." % n, fg=NARANJA)
        else:
            self.lbl_info.config(text="Todas terminan en un estado final. ¡Compruébalo en la gráfica!", fg=VERDE)


# ------------------- MÓDULO 3: PROBAR PALABRAS -------------------
class VistaM3(Vista):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.anim = None
        self.titulo("Módulo 3 · ¿Reconoce el autómata esta palabra?",
                    "Escribe una palabra y presiona Enter. Para probar la palabra vacía ε, déjala en blanco.")
        cuerpo = tk.Frame(self, bg=FONDO)
        cuerpo.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)
        izq = tk.Frame(cuerpo, bg=FONDO)
        izq.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        self.lbl_m = tk.Label(izq, font=(MONO, 10, "bold"), bg=FONDO, fg=AZUL_OSC, wraplength=430, justify="left")
        self.lbl_m.pack(anchor="w")
        tk.Label(izq, text="Palabra:", font=(F, 12, "bold"), bg=FONDO, fg=TEXTO).pack(anchor="w", pady=(12, 2))
        self.entrada = tk.Entry(izq, font=(MONO, 16), width=26, relief="flat", highlightthickness=2,
                                highlightbackground=BORDE, highlightcolor=AZUL)
        self.entrada.pack(anchor="w", ipady=6)
        self.entrada.bind("<Return>", lambda e: self.probar())
        boton(izq, "Probar palabra", self.probar).pack(anchor="w", pady=10)
        self.res = tk.Frame(izq, bg=BLANCO, highlightbackground=BORDE, highlightthickness=1, padx=14, pady=12)
        self.res.pack(fill="x")
        self.l_rec = tk.Label(self.res, font=(MONO, 11), bg=BLANCO, fg=TEXTO, wraplength=400, justify="left", anchor="w")
        self.l_fin = tk.Label(self.res, font=(F, 11), bg=BLANCO, fg=TEXTO, wraplength=400, justify="left", anchor="w")
        self.l_res = tk.Label(self.res, font=(F, 12, "bold"), bg=BLANCO, fg=TEXTO, wraplength=400, justify="left", anchor="w")
        for l in (self.l_rec, self.l_fin, self.l_res):
            l.pack(anchor="w", pady=2, fill="x")
        self.otra = tk.Frame(izq, bg=FONDO)
        tk.Label(self.otra, text="¿Desea probar otra palabra?", font=(F, 11, "bold"), bg=FONDO, fg=TEXTO).grid(row=0, column=0, padx=(0, 10))
        boton(self.otra, "Sí", self.nueva, color=VERDE).grid(row=0, column=1, padx=3)
        boton(self.otra, "No", lambda: app.ir("menu"), color="#94a3b8").grid(row=0, column=2, padx=3)
        tk.Label(izq, text="Historial", font=(F, 11, "bold"), bg=FONDO, fg=GRIS).pack(anchor="w", pady=(14, 2))
        self.hist = tk.Text(izq, width=44, height=5, font=(MONO, 10), state="disabled", relief="flat")
        self.hist.pack(anchor="w")
        self.grafica = Grafica(cuerpo)
        self.grafica.grid(row=0, column=1, sticky="nsew")

    def al_mostrar(self):
        a = self.app.automata
        self.lbl_m.config(text=fmt_tupla(a))
        self.grafica.mostrar(a)
        self.limpiar()
        self.entrada.focus_set()

    def limpiar(self):
        if self.anim:
            self.after_cancel(self.anim)
            self.anim = None
        self.otra.pack_forget()
        self.res.config(bg=BLANCO)
        for l in (self.l_rec, self.l_fin, self.l_res):
            l.config(text="", bg=BLANCO)
        self.l_res.config(text="Aquí aparecerá el resultado.", fg=GRIS)

    def nueva(self):
        self.entrada.delete(0, "end")
        self.limpiar()
        self.grafica.mostrar(self.app.automata)
        self.entrada.focus_set()

    def probar(self):
        a = self.app.automata
        pal = self.entrada.get().strip()
        r = self.app.ejecutar(recorrer_palabra, a, pal)
        if r is None:
            return
        self.limpiar()
        mostrar = '"%s"' % ver_palabra(pal)
        if r["error"]:
            sim, pos = r["error"]
            ok = False
            self.l_rec.config(text="Recorrido: " + fmt_recorrido(r["pasos"], a["q0"]))
            msg = 'la palabra %s NO es reconocida: el símbolo "%s" (posición %d) no pertenece al alfabeto Σ = %s.' % (
                mostrar, sim, pos, fmt_conjunto(a["Sigma"]))
        else:
            ok = r["aceptada"]
            self.l_rec.config(text="Recorrido: " + fmt_recorrido(r["pasos"], a["q0"]))
            self.l_fin.config(text="Estado final: %s, que %s un estado final." % (r["final"], "es" if ok else "no es"))
            msg = "la palabra %s %s es reconocida por el autómata." % (mostrar, "SÍ" if ok else "NO")
        fondo = VERDE_CLARO if ok else ROJO_CLARO
        self.res.config(bg=fondo)
        for l in (self.l_rec, self.l_fin, self.l_res):
            l.config(bg=fondo)
        self.l_res.config(text="Resultado: " + msg, fg=VERDE if ok else ROJO)
        self._historial("%-14s %s" % (ver_palabra(pal), "✔ reconocida" if ok else "✘ rechazada"))
        self._animar(a, r, ok, 0)

    def _historial(self, linea):
        self.hist.config(state="normal")
        self.hist.insert("end", linea + "\n")
        self.hist.see("end")
        self.hist.config(state="disabled")

    def _animar(self, a, r, ok, k):
        pasos = r["pasos"]
        estado = a["q0"] if k == 0 else pasos[k - 1][2]
        fin = k >= len(pasos)
        col = (VERDE_CLARO if ok else ROJO_CLARO) if fin else AMARILLO
        self.grafica.mostrar(a, pasos[:k], estado, col)
        if fin:
            self.anim = None
            self.otra.pack(anchor="w", pady=10)
        else:
            self.anim = self.after(550, lambda: self._animar(a, r, ok, k + 1))


# =====================================================================
#  APLICACIÓN
# =====================================================================
class App(tk.Tk):
    TITULOS = {"menu": "Menú principal", "m1": "Módulo 1 · Construcción", "m2": "Módulo 2 · Palabras reconocidas",
               "m3": "Módulo 3 · Probar palabras"}

    def __init__(self):
        super().__init__()
        self.title("Simulador de Autómatas Finitos")
        self.geometry("1150x760")
        self.minsize(1000, 680)
        self.configure(bg=FONDO)
        self.automata = None
        cab = tk.Frame(self, bg=AZUL_OSC)
        cab.pack(fill="x")
        tk.Label(cab, text="◉  Simulador de Autómatas Finitos", font=(F, 15, "bold"), bg=AZUL_OSC, fg="white").pack(side="left", padx=20, pady=12)
        self.btn_menu = boton(cab, "⌂ Menú principal", lambda: self.ir("menu"), color="#334155", size=10)
        self.btn_menu.pack(side="right", padx=16, pady=8)
        self.lbl_ruta = tk.Label(cab, font=(F, 11), bg=AZUL_OSC, fg="#93c5fd")
        self.lbl_ruta.pack(side="right", padx=10)
        cont = tk.Frame(self, bg=FONDO)
        cont.pack(fill="both", expand=True)
        cont.grid_rowconfigure(0, weight=1)
        cont.grid_columnconfigure(0, weight=1)
        self.vistas = {"menu": VistaMenu(cont, self), "m1": VistaM1(cont, self),
                       "m2": VistaM2(cont, self), "m3": VistaM3(cont, self)}
        for v in self.vistas.values():
            v.grid(row=0, column=0, sticky="nsew")
        self.ir("menu")

    def ir(self, nombre):
        v = self.vistas[nombre]
        v.tkraise()
        v.al_mostrar()
        self.lbl_ruta.config(text=self.TITULOS[nombre])
        if nombre == "menu":
            self.btn_menu.pack_forget()
        elif not self.btn_menu.winfo_ismapped():
            self.btn_menu.pack(side="right", padx=16, pady=8)

    def ir_modulo(self, destino):
        if destino != "m1" and not self.automata:
            if messagebox.askyesno("Primero construye un autómata",
                                   "Para usar este módulo primero debes pasar por el Módulo 1.\n\n¿Quieres ir al Módulo 1 ahora?"):
                self.ir("m1")
            return
        self.ir(destino)

    def ejecutar(self, fn, *args):
        """Llama una función de la LÓGICA; si aún no está hecha, avisa en vez de cerrarse."""
        try:
            return fn(*args)
        except NotImplementedError:
            messagebox.showinfo("Falta implementar",
                                "Completa la función «%s» en la sección LÓGICA DEL EQUIPO del código." % fn.__name__)
            return None


if __name__ == "__main__":
    App().mainloop()