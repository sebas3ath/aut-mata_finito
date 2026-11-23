# Automata finito con interfaz grafica (tkinter, incluido con Python)
# Dibuja el automata, resalta el estado actual y permite usar el menu.

import math
import tkinter as tk
from tkinter import messagebox

# ---------------------------------------------------------------
# Definicion del automata (puedes modificarlo)
# ---------------------------------------------------------------
ALFABETO = ["a", "b"]
ESTADO_INICIAL = "q0"
ESTADOS_FINALES = {"q3"}

# transiciones[estado][simbolo] = estado_destino
# Si un simbolo no aparece para un estado, ese camino NO es posible.
TRANSICIONES = {
    "q0": {"a": "q1", "b": "q0"},
    "q1": {"a": "q1", "b": "q2"},
    "q2": {"b": "q3"},
    "q3": {"a": "q1"},
}

# Posicion (x, y) de cada estado en el lienzo
POSICIONES = {
    "q0": (130, 180),
    "q1": (330, 180),
    "q2": (530, 180),
    "q3": (730, 180),
}

R = 30  # radio de cada estado


class AutomataGrafico:
    def __init__(self, root):
        self.root = root
        self.root.title("Automata Finito")
        self.estado = ESTADO_INICIAL
        self.historial = []

        self.construir_menu_superior()

        self.canvas = tk.Canvas(root, width=860, height=340, bg="white")
        self.canvas.pack(padx=10, pady=10)

        self.lbl_estado = tk.Label(root, font=("Arial", 12, "bold"))
        self.lbl_estado.pack()
        self.lbl_cadena = tk.Label(root, font=("Arial", 11))
        self.lbl_cadena.pack()

        panel = tk.Frame(root)
        panel.pack(pady=8)
        tk.Button(panel, text="Ver caminos", width=14,
                  command=self.ver_caminos).grid(row=0, column=0, padx=4)
        tk.Label(panel, text="Camino (simbolo):").grid(row=0, column=1, padx=4)
        self.entrada = tk.Entry(panel, width=6)
        self.entrada.grid(row=0, column=2)
        self.entrada.bind("<Return>", lambda e: self.elegir_camino())
        tk.Button(panel, text="Elegir camino", width=14,
                  command=self.elegir_camino).grid(row=0, column=3, padx=4)
        tk.Button(panel, text="Verificar cadena", width=14,
                  command=self.verificar).grid(row=0, column=4, padx=4)
        tk.Button(panel, text="Reiniciar", width=10,
                  command=self.reiniciar).grid(row=0, column=5, padx=4)

        self.log = tk.Text(root, height=7, width=100, state="disabled")
        self.log.pack(padx=10, pady=(0, 10))

        self.dibujar()

    # ------------------------- menu superior -------------------------
    def construir_menu_superior(self):
        barra = tk.Menu(self.root)
        menu = tk.Menu(barra, tearoff=0)
        menu.add_command(label="Ver caminos", command=self.ver_caminos)
        menu.add_command(label="Elegir camino", command=self.elegir_camino)
        menu.add_command(label="Verificar cadena", command=self.verificar)
        menu.add_command(label="Reiniciar", command=self.reiniciar)
        menu.add_separator()
        menu.add_command(label="Salir", command=self.root.destroy)
        barra.add_cascade(label="Automata", menu=menu)
        self.root.config(menu=barra)

    # ------------------------- dibujo -------------------------
    def dibujar(self):
        c = self.canvas
        c.delete("all")

        # flecha de entrada al estado inicial
        x, y = POSICIONES[ESTADO_INICIAL]
        c.create_line(x - R - 60, y, x - R, y, arrow=tk.LAST, width=2)
        c.create_text(x - R - 60, y - 12, text="inicio")

        # agrupar simbolos que van del mismo origen al mismo destino
        grupos = {}
        for origen, trans in TRANSICIONES.items():
            for simbolo, destino in trans.items():
                grupos.setdefault((origen, destino), []).append(simbolo)

        for (origen, destino), simbolos in grupos.items():
            self.dibujar_flecha(origen, destino, ",".join(sorted(simbolos)))

        # estados
        for nombre, (x, y) in POSICIONES.items():
            relleno = "#ffd54f" if nombre == self.estado else "white"
            c.create_oval(x - R, y - R, x + R, y + R, fill=relleno, width=2)
            if nombre in ESTADOS_FINALES:
                c.create_oval(x - R + 6, y - R + 6, x + R - 6, y + R - 6, width=2)
            c.create_text(x, y, text=nombre, font=("Arial", 12, "bold"))

        self.lbl_estado.config(text="Estado actual: " + self.estado)
        self.lbl_cadena.config(
            text="Cadena recorrida: " + ("".join(self.historial) or "(vacia)"))

    def dibujar_flecha(self, origen, destino, etiqueta):
        c = self.canvas
        sx, sy = POSICIONES[origen]
        dx, dy = POSICIONES[destino]
        activo = origen == self.estado
        color = "#1565c0" if activo else "black"
        ancho = 3 if activo else 2

        if origen == destino:
            # lazo sobre el estado
            c.create_line(sx - 14, sy - R + 2, sx - 26, sy - R - 32,
                          sx + 26, sy - R - 32, sx + 14, sy - R + 2,
                          smooth=True, arrow=tk.LAST, fill=color, width=ancho)
            c.create_text(sx, sy - R - 42, text=etiqueta, fill=color,
                          font=("Arial", 11, "bold"))
        elif dx < sx:
            # camino de regreso: curva por debajo
            h = 40 + 0.15 * abs(sx - dx)
            c.create_line(sx, sy + R, sx, sy + R + h, dx, dy + R + h, dx, dy + R,
                          smooth=True, arrow=tk.LAST, fill=color, width=ancho)
            c.create_text((sx + dx) / 2, sy + R + h * 0.75 + 12, text=etiqueta,
                          fill=color, font=("Arial", 11, "bold"))
        else:
            # flecha recta
            dist = math.hypot(dx - sx, dy - sy)
            ux, uy = (dx - sx) / dist, (dy - sy) / dist
            c.create_line(sx + ux * R, sy + uy * R, dx - ux * R, dy - uy * R,
                          arrow=tk.LAST, fill=color, width=ancho)
            c.create_text((sx + dx) / 2, (sy + dy) / 2 - 14, text=etiqueta,
                          fill=color, font=("Arial", 11, "bold"))

    # ------------------------- acciones del menu -------------------------
    def escribir(self, texto):
        self.log.config(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def ver_caminos(self):
        caminos = TRANSICIONES.get(self.estado, {})
        self.escribir("Caminos disponibles desde " + self.estado + ":")
        if not caminos:
            self.escribir("  (ninguno)")
        for simbolo, destino in caminos.items():
            self.escribir("  " + self.estado + " --" + simbolo + "--> " + destino)

    def elegir_camino(self):
        simbolo = self.entrada.get().strip()
        self.entrada.delete(0, "end")
        caminos = TRANSICIONES.get(self.estado, {})
        if simbolo not in caminos:
            mensaje = ("Ese camino no es posible desde " + self.estado +
                       " con '" + simbolo + "'.")
            self.escribir(mensaje)
            messagebox.showwarning("Camino no posible", mensaje)
            return
        nuevo = caminos[simbolo]
        self.escribir(self.estado + " --" + simbolo + "--> " + nuevo)
        self.historial.append(simbolo)
        self.estado = nuevo
        self.dibujar()

    def verificar(self):
        if self.estado in ESTADOS_FINALES:
            self.escribir("Cadena ACEPTADA (estado final).")
        else:
            self.escribir("Cadena NO aceptada (no esta en un estado final).")

    def reiniciar(self):
        self.estado = ESTADO_INICIAL
        self.historial = []
        self.escribir("Automata reiniciado.")
        self.dibujar()


if __name__ == "__main__":
    ventana = tk.Tk()
    AutomataGrafico(ventana)
    ventana.mainloop()
