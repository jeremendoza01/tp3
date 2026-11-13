# -*- coding: utf-8 -*-
"""
TP N.º 3 · Análisis y Diseño de Algoritmos · UNViMe 2026
Versión gráfica del programa (100 % Python, solo biblioteca estándar: tkinter).

Alumno : Jeremías Mendoza
Profesor: Reinaldo Gómez

Diseño de la aplicación
-----------------------
* Núcleo (arriba): estructuras (Árbol AVL, Max Heap) y "tareas" (consignas a-k).
  Cada tarea se ejecuta en un HILO APARTE y se comunica con la interfaz mediante
  una cola (queue). Así la ventana nunca se congela, muestra progreso real y
  permite CANCELAR operaciones largas (100 millones de datos).
* Interfaz (abajo): barra lateral con las opciones, un panel por consigna,
  consola de registro, barra de progreso y un gráfico comparativo de tiempos.
* Los archivos se leen en modo streaming (por bloques de líneas), igual que en
  la versión de consola: los 100 M de datos nunca se cargan completos en
  memoria, salvo en las muestras de los algoritmos que lo requieren.
"""
import csv
import math
import os
import queue
import random
import sys
import threading
import time
import tkinter as tk
from collections import Counter
from datetime import datetime
from tkinter import font as tkfont
from tkinter import messagebox, ttk

# La profundidad de recursión del AVL y del heapify es O(log n) (< 40 niveles).
sys.setrecursionlimit(10000)

# ============================================================================
# CONFIGURACIÓN Y RUTAS (los archivos se crean junto al ejecutable)
# ============================================================================
BASE_DIR = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.abspath(__file__)))


def ruta(nombre):
    return os.path.join(BASE_DIR, nombre)


ARCHIVO_DATOS = ruta("Datos.txt")
ARCHIVO_COUNTING = ruta("Datos_CountingSort.txt")
ARCHIVO_SELECTION = ruta("Datos_SelectionSort.txt")
ARCHIVO_HEAPSORT = ruta("Datos_HeapSort.txt")
ARCHIVO_CSV = ruta("resultados_tp3.csv")

RANGO_MAX = 100_000_000          # k: los valores están en [0, RANGO_MAX]
CANTIDAD_DEFECTO = 100_000_000   # n de la consigna

# Paleta (estilo oscuro)
BG = "#0d1117"
PANEL = "#161b22"
PANEL2 = "#1c2330"
BORDE = "#30363d"
TEXTO = "#e6edf3"
MUTED = "#8b949e"
ACENTO = "#1f6feb"
VERDE = "#3fb950"
ROJO = "#f85149"
AMARILLO = "#d29922"
VIOLETA = "#a371f7"
DESHAB = "#2d333b"


# ============================================================================
# UTILIDADES DE FORMATO
# ============================================================================
def fmt_num(n):
    """1000000 -> '1.000.000'"""
    return f"{n:,}".replace(",", ".")


def fmt_dec(x, dec=2):
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_tiempo(s):
    """Formatea segundos con la unidad más legible (µs, ms, s, min, h)."""
    if s < 1e-3:
        return f"{s * 1e6:.0f} µs"
    if s < 1:
        return f"{fmt_dec(s * 1e3, 1)} ms"
    if s < 60:
        return f"{fmt_dec(s, 2)} s"
    if s < 3600:
        m, r = divmod(s, 60)
        return f"{int(m)} min {r:.0f} s"
    h, resto = divmod(s, 3600)
    return f"{int(h)} h {int(resto // 60)} min"


def fmt_duracion_larga(s):
    """Para proyecciones enormes (días, años)."""
    if s < 86400:
        return fmt_tiempo(s)
    if s < 86400 * 365:
        return f"≈ {fmt_dec(s / 86400, 1)} días"
    return f"≈ {fmt_dec(s / (86400 * 365), 1)} años"


def fmt_bytes(b):
    for unidad in ("B", "KB", "MB", "GB"):
        if b < 1024 or unidad == "GB":
            return f"{fmt_dec(b, 2 if unidad in ('MB', 'GB') else 0)} {unidad}"
        b /= 1024


def aclarar(color, f=0.18):
    h = color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (int(c + (255 - c) * f) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def _borrar(ruta_archivo):
    try:
        os.remove(ruta_archivo)
    except OSError:
        pass


# ============================================================================
# ESTRUCTURAS DE DATOS (implementaciones propias)
# ============================================================================
class NodoAVL:
    """Nodo del Árbol AVL: valor, altura y punteros a los hijos."""

    def __init__(self, valor):
        self.valor = valor
        self.izquierdo = None
        self.derecho = None
        self.altura = 1


class ArbolAVL:
    """
    Árbol AVL (árbol binario de búsqueda autobalanceado).
    * El factor de balance de cada nodo (altura izq. - altura der.) se mantiene en {-1, 0, 1}.
    * Los valores repetidos se insertan en el subárbol derecho.
    * El rebalanceo se decide con el factor de balance del HIJO (no comparando
      valores), lo que garantiza el invariante AVL incluso con duplicados.
    """

    def __init__(self):
        self.raiz = None
        self.total_nodos = 0

    def obtener_altura(self, nodo):
        return nodo.altura if nodo else 0

    def obtener_balance(self, nodo):
        if not nodo:
            return 0
        return self.obtener_altura(nodo.izquierdo) - self.obtener_altura(nodo.derecho)

    def rotacion_derecha(self, y):
        x = y.izquierdo
        t2 = x.derecho
        x.derecho = y
        y.izquierdo = t2
        y.altura = 1 + max(self.obtener_altura(y.izquierdo), self.obtener_altura(y.derecho))
        x.altura = 1 + max(self.obtener_altura(x.izquierdo), self.obtener_altura(x.derecho))
        return x

    def rotacion_izquierda(self, x):
        y = x.derecho
        t2 = y.izquierdo
        y.izquierdo = x
        x.derecho = t2
        x.altura = 1 + max(self.obtener_altura(x.izquierdo), self.obtener_altura(x.derecho))
        y.altura = 1 + max(self.obtener_altura(y.izquierdo), self.obtener_altura(y.derecho))
        return y

    def rebalancear(self, raiz):
        """Actualiza la altura y aplica la rotación necesaria (casos LL, RR, LR y RL)."""
        raiz.altura = 1 + max(self.obtener_altura(raiz.izquierdo), self.obtener_altura(raiz.derecho))
        balance = self.obtener_balance(raiz)
        if balance > 1:
            if self.obtener_balance(raiz.izquierdo) < 0:        # Izquierda-Derecha
                raiz.izquierdo = self.rotacion_izquierda(raiz.izquierdo)
            return self.rotacion_derecha(raiz)                   # Izquierda-Izquierda
        if balance < -1:
            if self.obtener_balance(raiz.derecho) > 0:           # Derecha-Izquierda
                raiz.derecho = self.rotacion_derecha(raiz.derecho)
            return self.rotacion_izquierda(raiz)                 # Derecha-Derecha
        return raiz

    def insertar(self, raiz, valor):
        if not raiz:
            self.total_nodos += 1
            return NodoAVL(valor)
        if valor < raiz.valor:
            raiz.izquierdo = self.insertar(raiz.izquierdo, valor)
        else:
            raiz.derecho = self.insertar(raiz.derecho, valor)
        return self.rebalancear(raiz)

    def buscar(self, raiz, valor):
        while raiz is not None and raiz.valor != valor:
            raiz = raiz.derecho if raiz.valor < valor else raiz.izquierdo
        return raiz

    def nodo_minimo(self, nodo):
        while nodo is not None and nodo.izquierdo is not None:
            nodo = nodo.izquierdo
        return nodo

    def eliminar(self, raiz, valor):
        if not raiz:
            return raiz
        if valor < raiz.valor:
            raiz.izquierdo = self.eliminar(raiz.izquierdo, valor)
        elif valor > raiz.valor:
            raiz.derecho = self.eliminar(raiz.derecho, valor)
        else:
            if raiz.izquierdo is None:
                self.total_nodos -= 1
                return raiz.derecho
            if raiz.derecho is None:
                self.total_nodos -= 1
                return raiz.izquierdo
            sucesor = self.nodo_minimo(raiz.derecho)
            raiz.valor = sucesor.valor
            raiz.derecho = self.eliminar(raiz.derecho, sucesor.valor)
        return self.rebalancear(raiz)

    def in_orden(self, raiz, resultado, limite):
        """Recorrido InOrden acotado a los primeros 'limite' elementos."""
        if raiz and len(resultado) < limite:
            self.in_orden(raiz.izquierdo, resultado, limite)
            if len(resultado) < limite:
                resultado.append(raiz.valor)
            self.in_orden(raiz.derecho, resultado, limite)


class MaxHeap:
    """Max Heap en arreglo: padre de i = (i-1)//2, hijos = 2i+1 y 2i+2."""

    def __init__(self):
        self.heap = []

    def padre(self, i):
        return (i - 1) // 2

    def insertar(self, valor):
        """Agrega al final y 'sube' el elemento mientras sea mayor que su padre."""
        self.heap.append(valor)
        i = len(self.heap) - 1
        while i != 0 and self.heap[self.padre(i)] < self.heap[i]:
            p = self.padre(i)
            self.heap[i], self.heap[p] = self.heap[p], self.heap[i]
            i = p

    def extraer_maximo(self):
        """Quita la raíz, mueve el último a la raíz y lo 'hunde' (heapify_down)."""
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        raiz = self.heap[0]
        self.heap[0] = self.heap.pop()
        self.heapify_down(0)
        return raiz

    def heapify_down(self, i):
        n = len(self.heap)
        izq, der, mayor = 2 * i + 1, 2 * i + 2, i
        if izq < n and self.heap[izq] > self.heap[mayor]:
            mayor = izq
        if der < n and self.heap[der] > self.heap[mayor]:
            mayor = der
        if mayor != i:
            self.heap[i], self.heap[mayor] = self.heap[mayor], self.heap[i]
            self.heapify_down(mayor)

    def buscar(self, valor):
        """Búsqueda lineal O(n): el heap no tiene orden entre hermanos."""
        for i, v in enumerate(self.heap):
            if v == valor:
                return i
        return -1

    def altura_aprox(self):
        return int(math.log2(len(self.heap))) if self.heap else 0


# ============================================================================
# INFRAESTRUCTURA DE TAREAS (hilo de trabajo <-> interfaz)
# ============================================================================
class Cancelado(Exception):
    """Se lanza dentro del hilo de trabajo cuando el usuario cancela."""


class Contexto:
    """Canal de comunicación que usan las tareas para informar a la interfaz."""

    def __init__(self, cola, cancelar):
        self.cola = cola
        self.cancelar = cancelar

    def log(self, texto, tag="info"):
        self.cola.put(("log", texto, tag))

    def progreso(self, fraccion, texto=""):
        self.cola.put(("progreso", fraccion, texto))

    def revisar(self):
        if self.cancelar.is_set():
            raise Cancelado()


def trozos(ctx, ruta_archivo, limite=None, texto="Leyendo", desde=0.0, hasta=1.0,
           hint=8 * 1024 * 1024):
    """
    Lee un archivo por BLOQUES de líneas (bytes). Permite informar el progreso y
    cancelar sin agregar costo al bucle interno que procesa cada línea.
    'limite' = máximo de líneas a leer (None = todo el archivo).
    """
    total_bytes = os.path.getsize(ruta_archivo) or 1
    lineas = 0
    bytes_leidos = 0
    with open(ruta_archivo, "rb") as f:
        while True:
            ctx.revisar()
            bloque = f.readlines(hint)
            if not bloque:
                break
            if limite is not None and lineas + len(bloque) > limite:
                bloque = bloque[: limite - lineas]
            lineas += len(bloque)
            bytes_leidos += sum(map(len, bloque))
            yield bloque
            frac = (lineas / limite) if limite else (bytes_leidos / total_bytes)
            ctx.progreso(desde + (hasta - desde) * min(frac, 1.0),
                         f"{texto}… {fmt_num(lineas)} líneas")
            if limite is not None and lineas >= limite:
                break


def leer_lista(ctx, limite, desde=0.0, hasta=0.1, texto="Leyendo datos"):
    """Carga en una lista los primeros 'limite' enteros de Datos.txt."""
    datos = []
    for bloque in trozos(ctx, ARCHIVO_DATOS, limite, texto, desde, hasta):
        for linea in bloque:
            s = linea.strip()
            if s:
                datos.append(int(s))
    return datos


def escribir_lista(ctx, ruta_archivo, datos, desde, hasta):
    """Escribe una lista ordenada (un número por línea) por bloques de 1.000.000."""
    paso = 1_000_000
    total = len(datos) or 1
    try:
        with open(ruta_archivo, "w") as f:
            for ini in range(0, len(datos), paso):
                ctx.revisar()
                f.write("\n".join(map(str, datos[ini:ini + paso])) + "\n")
                ctx.progreso(desde + (hasta - desde) * min((ini + paso) / total, 1.0),
                             "Guardando resultado…")
    except Cancelado:
        _borrar(ruta_archivo)
        raise


# ============================================================================
# TAREAS (CONSIGNAS a - k). Cada una devuelve un diccionario con sus resultados.
# ============================================================================
def tarea_generar(ctx, n):
    """Consigna a) Genera Datos.txt con n números aleatorios en [0, RANGO_MAX]. O(n)."""
    ctx.log(f"Generando {fmt_num(n)} números aleatorios en [0, {fmt_num(RANGO_MAX)}]…", "titulo")
    inicio = time.perf_counter()
    bloque = 1_000_000
    hechos = 0
    try:
        with open(ARCHIVO_DATOS, "w") as f:
            while hechos < n:
                ctx.revisar()
                m = min(bloque, n - hechos)
                f.write("\n".join([str(random.randint(0, RANGO_MAX)) for _ in range(m)]) + "\n")
                hechos += m
                ctx.progreso(hechos / n, f"Generados {fmt_num(hechos)} de {fmt_num(n)}")
    except Cancelado:
        _borrar(ARCHIVO_DATOS)
        raise
    t = time.perf_counter() - inicio
    return {"n": n, "t": t, "tam": os.path.getsize(ARCHIVO_DATOS)}


def tarea_analizar(ctx):
    """Consignas b) y c) Máximo, mínimo y top 10 de frecuencias en UN solo recorrido. O(n)."""
    ctx.log("Recorriendo Datos.txt: máximo, mínimo y frecuencias…", "titulo")
    inicio = time.perf_counter()
    maximo, minimo, lineas = -1, RANGO_MAX + 1, 0
    contador = Counter()                      # tabla hash: número -> apariciones
    for bloque in trozos(ctx, ARCHIVO_DATOS, texto="Analizando"):
        for linea in bloque:
            s = linea.strip()
            if s:
                num = int(s)
                if num > maximo:
                    maximo = num
                if num < minimo:
                    minimo = num
                contador[num] += 1
        lineas += len(bloque)
    t = time.perf_counter() - inicio
    return {"n": lineas, "t": t, "max": maximo, "min": minimo,
            "top": contador.most_common(10), "distintos": len(contador)}


def tarea_counting(ctx):
    """Consigna d) Counting Sort. Tiempo O(n + k), espacio O(k)."""
    ctx.log(f"Counting Sort: reservando el arreglo de conteo (k + 1 = {fmt_num(RANGO_MAX + 1)} posiciones)…",
            "titulo")
    inicio = time.perf_counter()
    ctx.progreso(0.0, "Reservando memoria para el arreglo de conteo…")
    conteo = [0] * (RANGO_MAX + 1)
    memoria = sys.getsizeof(conteo)
    lineas = 0
    # Fase 1: contar apariciones (lectura en streaming)
    for bloque in trozos(ctx, ARCHIVO_DATOS, texto="Contando", desde=0.0, hasta=0.5):
        for linea in bloque:
            s = linea.strip()
            if s:
                conteo[int(s)] += 1
        lineas += len(bloque)
    # Fase 2: recorrer el arreglo y escribir cada valor tantas veces como fue contado
    paso = 1_000_000
    total = RANGO_MAX + 1
    try:
        with open(ARCHIVO_COUNTING, "w") as f:
            for ini in range(0, total, paso):
                ctx.revisar()
                fin = min(ini + paso, total)
                partes = [f"{num}\n" * c for num, c in enumerate(conteo[ini:fin], ini) if c]
                if partes:
                    f.write("".join(partes))
                ctx.progreso(0.5 + 0.5 * fin / total, f"Escribiendo valores ordenados… {fmt_num(fin)} de {fmt_num(total)}")
    except Cancelado:
        _borrar(ARCHIVO_COUNTING)
        raise
    t = time.perf_counter() - inicio
    return {"n": lineas, "t": t, "mem": memoria}


def tarea_selection(ctx, limite):
    """Consigna e) Selection Sort. O(n²) en mejor y peor caso (muestra acotada)."""
    ctx.log(f"Selection Sort sobre {fmt_num(limite)} elementos (O(n²))…", "titulo")
    inicio = time.perf_counter()
    datos = leer_lista(ctx, limite, 0.0, 0.02)
    n = len(datos)
    total = n * (n - 1) / 2 or 1
    for i in range(n):
        if i % 25 == 0:
            ctx.revisar()
            hecho = i * (2 * n - i - 1) / 2          # comparaciones ya realizadas
            ctx.progreso(0.02 + 0.96 * hecho / total,
                         f"Ordenando… posición {fmt_num(i)} de {fmt_num(n)}")
        indice_min = i
        for j in range(i + 1, n):
            if datos[j] < datos[indice_min]:
                indice_min = j
        datos[i], datos[indice_min] = datos[indice_min], datos[i]
    escribir_lista(ctx, ARCHIVO_SELECTION, datos, 0.98, 1.0)
    t = time.perf_counter() - inicio
    return {"n": n, "t": t}


def tarea_heapsort(ctx, limite):
    """Consigna k) Heap Sort in-place: construcción bottom-up O(n) + n-1 extracciones O(log n)."""
    ctx.log(f"Heap Sort sobre {fmt_num(limite)} elementos…", "titulo")
    inicio = time.perf_counter()
    datos = leer_lista(ctx, limite, 0.0, 0.05)
    n = len(datos)

    def heapify(arr, tam, i):
        mayor, izq, der = i, 2 * i + 1, 2 * i + 2
        if izq < tam and arr[izq] > arr[mayor]:
            mayor = izq
        if der < tam and arr[der] > arr[mayor]:
            mayor = der
        if mayor != i:
            arr[i], arr[mayor] = arr[mayor], arr[i]
            heapify(arr, tam, mayor)

    # Fase 1: construir el Max Heap (de la última hoja-padre hacia la raíz)
    for i in range(n // 2 - 1, -1, -1):
        if i % 100_000 == 0:
            ctx.revisar()
            ctx.progreso(0.05 + 0.10 * (1 - i / max(n // 2, 1)), "Construyendo el heap…")
        heapify(datos, n, i)
    # Fase 2: mover el máximo al final y restaurar el heap reducido
    for i in range(n - 1, 0, -1):
        if i % 100_000 == 0:
            ctx.revisar()
            ctx.progreso(0.15 + 0.80 * (1 - i / max(n, 1)),
                         f"Extrayendo máximos… quedan {fmt_num(i)}")
        datos[i], datos[0] = datos[0], datos[i]
        heapify(datos, i, 0)
    escribir_lista(ctx, ARCHIVO_HEAPSORT, datos, 0.95, 1.0)
    t = time.perf_counter() - inicio
    return {"n": n, "t": t}


def tarea_avl_construir(ctx, limite):
    """Consigna i) Construye el AVL insertando los primeros 'limite' números del archivo."""
    ctx.log(f"Construyendo el árbol AVL con {fmt_num(limite)} datos…", "titulo")
    arbol = ArbolAVL()
    inicio = time.perf_counter()
    for bloque in trozos(ctx, ARCHIVO_DATOS, limite, "Insertando en el AVL"):
        for linea in bloque:
            s = linea.strip()
            if s:
                arbol.raiz = arbol.insertar(arbol.raiz, int(s))
    t = time.perf_counter() - inicio
    muestra = []
    arbol.in_orden(arbol.raiz, muestra, 10)
    return {"estructura": arbol, "t": t, "n": arbol.total_nodos,
            "altura": arbol.obtener_altura(arbol.raiz), "muestra": muestra}


def tarea_heap_construir(ctx, limite):
    """Consigna j) Construye el Max Heap con inserciones sucesivas."""
    ctx.log(f"Construyendo el Max Heap con {fmt_num(limite)} datos…", "titulo")
    h = MaxHeap()
    inicio = time.perf_counter()
    for bloque in trozos(ctx, ARCHIVO_DATOS, limite, "Insertando en el heap"):
        for linea in bloque:
            s = linea.strip()
            if s:
                h.insertar(int(s))
    t = time.perf_counter() - inicio
    return {"estructura": h, "t": t, "n": len(h.heap)}


def tarea_heap_buscar(ctx, h, valor):
    ctx.progreso(0.0, f"Buscando {fmt_num(valor)} en el heap (O(n))…")
    t0 = time.perf_counter()
    idx = h.buscar(valor)
    return {"idx": idx, "t": time.perf_counter() - t0}


def tarea_verificar(ctx, archivos):
    """Consigna f) Verifica que cada archivo esté ordenado de forma ascendente. O(n)."""
    ctx.log("Verificando el orden de los archivos generados…", "titulo")
    resultados = []
    k = len(archivos)
    for idx, (nombre, ruta_archivo) in enumerate(archivos):
        if not os.path.exists(ruta_archivo):
            resultados.append((nombre, None, 0.0, 0))
            continue
        inicio = time.perf_counter()
        previo, ordenado, lineas = -1, True, 0
        for bloque in trozos(ctx, ruta_archivo, texto=f"Verificando {nombre}",
                             desde=idx / k, hasta=(idx + 1) / k):
            for linea in bloque:
                s = linea.strip()
                if not s:
                    continue
                actual = int(s)
                if actual < previo:
                    ordenado = False
                    break
                previo = actual
            lineas += len(bloque)
            if not ordenado:
                break
        resultados.append((nombre, ordenado, time.perf_counter() - inicio, lineas))
    return {"resultados": resultados}


# ============================================================================
# COMPONENTES VISUALES
# ============================================================================
class Boton(tk.Label):
    """Botón plano con efecto hover y estado habilitado/deshabilitado."""

    def __init__(self, master, texto, comando, color=ACENTO, fuente=None, padx=18, pady=9):
        super().__init__(master, text=texto, bg=color, fg="white", font=fuente,
                         padx=padx, pady=pady, cursor="hand2")
        self.color = color
        self.comando = comando
        self.activo = True
        self.bind("<Enter>", lambda e: self.activo and self.config(bg=aclarar(self.color)))
        self.bind("<Leave>", lambda e: self.activo and self.config(bg=self.color))
        self.bind("<Button-1>", lambda e: self.activo and self.comando())

    def habilitar(self, valor):
        self.activo = valor
        if valor:
            self.config(bg=self.color, fg="white", cursor="hand2")
        else:
            self.config(bg=DESHAB, fg=MUTED, cursor="arrow")


class Tarjeta(tk.Frame):
    """Tarjeta con un valor destacado y su título (con borde superior de color)."""

    def __init__(self, master, titulo, color, f_valor, f_texto):
        super().__init__(master, bg=PANEL, highlightthickness=1, highlightbackground=BORDE)
        tk.Frame(self, bg=color, height=3).pack(fill="x")
        self.valor = tk.Label(self, text="—", bg=PANEL, fg=TEXTO, font=f_valor, anchor="w")
        self.valor.pack(fill="x", padx=14, pady=(10, 0))
        tk.Label(self, text=titulo, bg=PANEL, fg=MUTED, font=f_texto, anchor="w").pack(
            fill="x", padx=14, pady=(0, 10))

    def set(self, texto):
        self.valor.config(text=texto)


# ============================================================================
# PANELES (uno por consigna)
# ============================================================================
class Panel(tk.Frame):
    TITULO = ""
    ICONO = ""
    DESC = ""

    def __init__(self, app):
        super().__init__(app.contenido, bg=BG)
        self.app = app
        tk.Label(self, text=f"{self.ICONO}  {self.TITULO}", font=app.f_titulo, bg=BG, fg=TEXTO,
                 anchor="w").pack(fill="x", padx=28, pady=(22, 2))
        tk.Label(self, text=self.DESC, font=app.f_texto, bg=BG, fg=MUTED, anchor="w",
                 justify="left", wraplength=820).pack(fill="x", padx=28, pady=(0, 12))
        self.cuerpo = tk.Frame(self, bg=BG)
        self.cuerpo.pack(fill="both", expand=True, padx=28)
        self.construir()

    # --- ganchos ---
    def construir(self):
        pass

    def al_mostrar(self):
        pass

    # --- ayudas de construcción ---
    def campo(self, padre, etiqueta, defecto, col, ancho=16):
        tk.Label(padre, text=etiqueta, bg=BG, fg=MUTED, font=self.app.f_texto,
                 anchor="w").grid(row=0, column=col, sticky="w")
        var = tk.StringVar(value=defecto)
        tk.Entry(padre, textvariable=var, width=ancho, bg=PANEL2, fg=TEXTO,
                 insertbackground=TEXTO, relief="flat", font=self.app.f_texto,
                 highlightthickness=1, highlightbackground=BORDE,
                 highlightcolor=ACENTO).grid(row=1, column=col, sticky="w", ipady=6, padx=(0, 14))
        return var

    def tarjetas(self, padre, definiciones):
        """definiciones: lista de (clave, titulo, color). Devuelve dict clave -> Tarjeta."""
        fila = tk.Frame(padre, bg=BG)
        fila.pack(fill="x", pady=(16, 4))
        tarjetas = {}
        for i, (clave, titulo, color) in enumerate(definiciones):
            t = Tarjeta(fila, titulo, color, self.app.f_valor, self.app.f_chico)
            t.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0))
            fila.columnconfigure(i, weight=1, uniform="t")
            tarjetas[clave] = t
        return tarjetas

    def tabla(self, padre, columnas, alto=6, anchos=None):
        marco = tk.Frame(padre, bg=BORDE)
        marco.pack(fill="x", pady=(10, 0))
        arbol = ttk.Treeview(marco, columns=[c for c, _ in columnas], show="headings", height=alto)
        for i, (c, titulo) in enumerate(columnas):
            arbol.heading(c, text=titulo)
            arbol.column(c, width=(anchos[i] if anchos else 120), anchor="w")
        arbol.pack(fill="x", padx=1, pady=1)
        arbol.tag_configure("par", background=PANEL2)
        return arbol

    def entero(self, var, minimo=0, nombre="El valor"):
        texto = var.get().strip().replace(".", "").replace(",", "").replace(" ", "")
        try:
            valor = int(texto)
        except ValueError:
            messagebox.showwarning("Dato inválido", f"{nombre} debe ser un número entero.")
            return None
        if valor < minimo:
            messagebox.showwarning("Dato inválido", f"{nombre} debe ser mayor o igual a {fmt_num(minimo)}.")
            return None
        return valor


class PanelInicio(Panel):
    TITULO = "Bienvenido"
    ICONO = "🏠"
    DESC = ("Trabajo Práctico N.º 3 · Transformar y Conquistar. Genera un archivo de 100 millones de números "
            "y compara algoritmos de ordenamiento y estructuras de datos midiendo sus tiempos reales.")

    def construir(self):
        self.t = self.tarjetas(self.cuerpo, [
            ("datos", "Estado de Datos.txt", VERDE),
            ("opciones", "Consignas implementadas", ACENTO),
            ("lenguaje", "Lenguaje", AMARILLO),
        ])
        self.t["opciones"].set("a) a k)")
        self.t["lenguaje"].set("Python 100 %")
        caja = tk.Frame(self.cuerpo, bg=PANEL, highlightthickness=1, highlightbackground=BORDE)
        caja.pack(fill="x", pady=(14, 0))
        pasos = [
            ("1", "Generá Datos.txt", "Opción 1 (≈ 1 GB en disco; con 100 M de datos tarda ≈ 1 minuto)."),
            ("2", "Analizá y ordená", "Opciones 2 a 4 y 7: máximo/mínimo, frecuencias y los tres algoritmos de ordenamiento."),
            ("3", "Explorá las estructuras", "Opciones 5 y 6: Árbol AVL y Max Heap con operaciones interactivas."),
            ("4", "Verificá y compará", "Opción 8 verifica el orden; la opción 9 muestra el gráfico comparativo y exporta un CSV."),
        ]
        for num, titulo, desc in pasos:
            fila = tk.Frame(caja, bg=PANEL)
            fila.pack(fill="x", padx=16, pady=8)
            tk.Label(fila, text=num, bg=ACENTO, fg="white", font=self.app.f_negrita, width=3,
                     pady=4).pack(side="left")
            txt = tk.Frame(fila, bg=PANEL)
            txt.pack(side="left", padx=12)
            tk.Label(txt, text=titulo, bg=PANEL, fg=TEXTO, font=self.app.f_negrita, anchor="w").pack(fill="x")
            tk.Label(txt, text=desc, bg=PANEL, fg=MUTED, font=self.app.f_texto, anchor="w").pack(fill="x")
        tk.Label(self.cuerpo, text="👨‍💻 Jeremías Mendoza  ·  👨‍🏫 Prof. Reinaldo Gómez  ·  🏛️ UNViMe 2026",
                 bg=BG, fg=MUTED, font=self.app.f_texto).pack(anchor="w", pady=(16, 0))

    def al_mostrar(self):
        if os.path.exists(ARCHIVO_DATOS):
            self.t["datos"].set(f"✔ {fmt_bytes(os.path.getsize(ARCHIVO_DATOS))}")
        else:
            self.t["datos"].set("✖ No existe")


class PanelGenerar(Panel):
    TITULO = "Generar archivo de datos"
    ICONO = "🎲"
    DESC = ("Consigna a) · Crea Datos.txt con números aleatorios en [0, 100.000.000], uno por línea. "
            "Se escribe por bloques de 1.000.000. Complejidad O(n).")

    def construir(self):
        fila = tk.Frame(self.cuerpo, bg=BG)
        fila.pack(fill="x")
        self.var_n = self.campo(fila, "Cantidad de números (n)", fmt_num(CANTIDAD_DEFECTO), 0, 20)
        Boton(fila, "▶  Generar Datos.txt", self.ejecutar, fuente=self.app.f_boton).grid(
            row=1, column=1, sticky="w")
        self.t = self.tarjetas(self.cuerpo, [
            ("t", "Tiempo", ACENTO), ("n", "Números generados", VERDE),
            ("tam", "Tamaño del archivo", AMARILLO), ("v", "Velocidad", VIOLETA)])

    def ejecutar(self):
        n = self.entero(self.var_n, 1, "La cantidad")
        if n is None:
            return
        if os.path.exists(ARCHIVO_DATOS) and not messagebox.askyesno(
                "Reemplazar archivo", "Datos.txt ya existe. ¿Querés reemplazarlo?"):
            return
        self.app.ejecutar(tarea_generar, n, al_terminar=self.terminado)

    def terminado(self, r):
        self.t["t"].set(fmt_tiempo(r["t"]))
        self.t["n"].set(fmt_num(r["n"]))
        self.t["tam"].set(fmt_bytes(r["tam"]))
        self.t["v"].set(f"{fmt_num(int(r['n'] / r['t']))} /s")
        self.app.registrar("Generación de Datos.txt", r["n"], r["t"])
        self.app.log(f"✔ Datos.txt generado en {fmt_tiempo(r['t'])} ({fmt_bytes(r['tam'])}).", "ok")


class PanelAnalizar(Panel):
    TITULO = "Máximo, mínimo y frecuencias"
    ICONO = "🔎"
    DESC = ("Consignas b) y c) · Un solo recorrido del archivo: máximo, mínimo y los 10 números que más se repiten "
            "(tabla hash con Counter). Complejidad O(n).")

    def construir(self):
        Boton(self.cuerpo, "▶  Analizar Datos.txt", self.ejecutar, fuente=self.app.f_boton).pack(anchor="w")
        self.t = self.tarjetas(self.cuerpo, [
            ("max", "Número mayor", VERDE), ("min", "Número menor", ROJO),
            ("t", "Tiempo", ACENTO), ("n", "Líneas leídas", AMARILLO)])
        self.tabla_top = self.tabla(self.cuerpo, [("p", "Posición"), ("num", "Número"), ("ap", "Apariciones")],
                                    alto=10, anchos=[120, 260, 160])
        tk.Label(self.cuerpo, text=("Referencia teórica (Poisson, λ = 1): se esperan ≈ 10 valores con exactamente 10 "
                                    "apariciones y ≈ 1 valor con 11 o más."),
                 bg=BG, fg=MUTED, font=self.app.f_chico, anchor="w").pack(fill="x", pady=(8, 0))

    def ejecutar(self):
        if self.app.requiere_datos():
            self.app.ejecutar(tarea_analizar, al_terminar=self.terminado)

    def terminado(self, r):
        self.t["max"].set(fmt_num(r["max"]))
        self.t["min"].set(fmt_num(r["min"]))
        self.t["t"].set(fmt_tiempo(r["t"]))
        self.t["n"].set(fmt_num(r["n"]))
        self.tabla_top.delete(*self.tabla_top.get_children())
        for i, (num, ap) in enumerate(r["top"], 1):
            self.tabla_top.insert("", "end", values=(i, fmt_num(num), ap), tags=("par",) if i % 2 == 0 else ())
        self.app.registrar("Máx, mín y frecuencias", r["n"], r["t"])
        self.app.log(f"✔ Mayor: {fmt_num(r['max'])} · Menor: {fmt_num(r['min'])} · "
                     f"{fmt_num(r['distintos'])} valores distintos · {fmt_tiempo(r['t'])}.", "ok")


class PanelCounting(Panel):
    TITULO = "Counting Sort"
    ICONO = "🟢"
    DESC = ("Consigna d) · Ordenamiento por conteo: cuenta las apariciones de cada valor y luego escribe cada valor "
            "tantas veces como fue contado. Tiempo O(n + k), espacio O(k). Guarda Datos_CountingSort.txt.")

    def construir(self):
        Boton(self.cuerpo, "▶  Ordenar con Counting Sort", self.ejecutar, VERDE, self.app.f_boton).pack(anchor="w")
        self.t = self.tarjetas(self.cuerpo, [
            ("t", "Tiempo", ACENTO), ("n", "Elementos ordenados", VERDE),
            ("mem", "Memoria del arreglo de conteo", AMARILLO), ("v", "Tiempo por elemento", VIOLETA)])
        tk.Label(self.cuerpo, text=("⚠ Reserva ≈ 800 MB de RAM (k + 1 = 100.000.001 posiciones de 8 bytes). "
                                    "Cerrá otras aplicaciones si tu equipo tiene poca memoria."),
                 bg=BG, fg=AMARILLO, font=self.app.f_texto, anchor="w").pack(fill="x", pady=(10, 0))

    def ejecutar(self):
        if self.app.requiere_datos():
            self.app.ejecutar(tarea_counting, al_terminar=self.terminado)

    def terminado(self, r):
        self.t["t"].set(fmt_tiempo(r["t"]))
        self.t["n"].set(fmt_num(r["n"]))
        self.t["mem"].set(fmt_bytes(r["mem"]))
        self.t["v"].set(f"{fmt_dec(r['t'] / max(r['n'], 1) * 1e6, 2)} µs")
        self.app.registrar("Counting Sort", r["n"], r["t"])
        self.app.log(f"✔ Counting Sort finalizado en {fmt_tiempo(r['t'])}. Guardado en Datos_CountingSort.txt.", "ok")


class PanelSelection(Panel):
    TITULO = "Selection Sort"
    ICONO = "🔴"
    DESC = ("Consigna e) · Ordenamiento por selección: O(n²) en mejor y peor caso. Se aplica a una muestra reducida "
            "porque con 100 millones tardaría años. Guarda Datos_SelectionSort.txt.")

    def construir(self):
        fila = tk.Frame(self.cuerpo, bg=BG)
        fila.pack(fill="x")
        self.var_n = self.campo(fila, "Tamaño de la muestra (n)", "100.000", 0, 20)
        Boton(fila, "▶  Ordenar con Selection Sort", self.ejecutar, ROJO, self.app.f_boton).grid(
            row=1, column=1, sticky="w")
        self.t = self.tarjetas(self.cuerpo, [
            ("t", "Tiempo", ACENTO), ("cmp", "Comparaciones n(n−1)/2", AMARILLO),
            ("ns", "Tiempo por comparación", VIOLETA), ("proy", "Proyección a 100 M datos", ROJO)])
        tk.Label(self.cuerpo, text="Referencia: con n = 100.000 tarda ≈ 2,5 minutos (varía según el equipo).",
                 bg=BG, fg=MUTED, font=self.app.f_chico, anchor="w").pack(fill="x", pady=(10, 0))

    def ejecutar(self):
        n = self.entero(self.var_n, 2, "El tamaño")
        if n is not None and self.app.requiere_datos():
            if n > 200_000 and not messagebox.askyesno(
                    "Tiempo estimado alto",
                    f"Con {fmt_num(n)} elementos Selection Sort puede tardar muchos minutos. ¿Continuar?"):
                return
            self.app.ejecutar(tarea_selection, n, al_terminar=self.terminado)

    def terminado(self, r):
        n, t = r["n"], r["t"]
        comparaciones = n * (n - 1) / 2
        self.t["t"].set(fmt_tiempo(t))
        self.t["cmp"].set(fmt_dec(comparaciones / 1e9, 3) + " × 10⁹" if comparaciones > 1e8 else fmt_num(int(comparaciones)))
        self.t["ns"].set(f"{fmt_dec(t / comparaciones * 1e9, 1)} ns")
        self.t["proy"].set(fmt_duracion_larga(t * (100_000_000 / n) ** 2))
        self.app.registrar("Selection Sort", n, t)
        self.app.log(f"✔ Selection Sort finalizado en {fmt_tiempo(t)}. Guardado en Datos_SelectionSort.txt.", "ok")


class PanelEstructura(Panel):
    """Base de los paneles interactivos del AVL y del Heap."""
    NOMBRE = ""

    def construir_base(self, n_defecto, color, cards):
        fila = tk.Frame(self.cuerpo, bg=BG)
        fila.pack(fill="x")
        self.var_n = self.campo(fila, "Cantidad de datos a cargar", n_defecto, 0, 20)
        Boton(fila, f"▶  Construir {self.NOMBRE}", self.construir_estructura, color, self.app.f_boton).grid(
            row=1, column=1, sticky="w")
        self.t = self.tarjetas(self.cuerpo, cards)
        self.estructura = None

    def fila_operaciones(self, con_valor=True):
        marco = tk.Frame(self.cuerpo, bg=PANEL, highlightthickness=1, highlightbackground=BORDE)
        marco.pack(fill="x", pady=(12, 0))
        interior = tk.Frame(marco, bg=PANEL)
        interior.pack(fill="x", padx=14, pady=12)
        tk.Label(interior, text="Operaciones interactivas", bg=PANEL, fg=TEXTO, font=self.app.f_negrita).pack(
            anchor="w")
        fila = tk.Frame(interior, bg=PANEL)
        fila.pack(fill="x", pady=(8, 0))
        self.var_val = tk.StringVar()
        if con_valor:
            tk.Label(fila, text="Valor:", bg=PANEL, fg=MUTED, font=self.app.f_texto).pack(side="left")
            tk.Entry(fila, textvariable=self.var_val, width=14, bg=PANEL2, fg=TEXTO, insertbackground=TEXTO,
                     relief="flat", font=self.app.f_texto, highlightthickness=1, highlightbackground=BORDE,
                     highlightcolor=ACENTO).pack(side="left", padx=(8, 12), ipady=5)
        self.botones_op = []
        return fila

    def agregar_boton_op(self, fila, texto, comando, color):
        b = Boton(fila, texto, comando, color, self.app.f_texto, padx=14, pady=6)
        b.pack(side="left", padx=(0, 8))
        b.habilitar(False)
        self.botones_op.append(b)
        return b

    def habilitar_operaciones(self, valor=True):
        for b in self.botones_op:
            b.habilitar(valor)

    def registrar_op(self, operacion, valor, resultado, t):
        i = len(self.tabla_ops.get_children())
        self.tabla_ops.insert("", 0, values=(operacion, valor, resultado, fmt_tiempo(t)),
                              tags=("par",) if i % 2 == 0 else ())
        self.app.registrar(f"{self.NOMBRE} · {operacion}", self.cantidad_actual(), t, tipo="operacion")
        self.app.log(f"{self.NOMBRE} · {operacion}: {resultado} ({fmt_tiempo(t)})", "info")

    def cantidad_actual(self):
        return 0

    def construir_estructura(self):
        n = self.entero(self.var_n, 1, "La cantidad")
        if n is not None and self.app.requiere_datos():
            self.habilitar_operaciones(False)
            self.app.ejecutar(self.TAREA, n, al_terminar=self.construido)


class PanelAVL(PanelEstructura):
    TITULO = "Árbol AVL"
    ICONO = "🌳"
    NOMBRE = "AVL"
    TAREA = staticmethod(tarea_avl_construir)
    DESC = ("Consigna i) · Árbol binario de búsqueda autobalanceado: inserción, búsqueda y eliminación en O(log n). "
            "Primero se construye con los datos del archivo y luego se opera de forma interactiva.")

    def construir(self):
        self.construir_base("1.000.000", ACENTO, [
            ("altura", "Altura del árbol", VERDE), ("nodos", "Cantidad de nodos", ACENTO),
            ("t", "Tiempo de construcción", AMARILLO), ("cota", "Cota teórica 1,44·log₂(n+2)", VIOLETA)])
        self.lbl_muestra = tk.Label(self.cuerpo, text="Muestra InOrden (primeros 10): —", bg=BG, fg=MUTED,
                                    font=self.app.f_mono, anchor="w")
        self.lbl_muestra.pack(fill="x", pady=(8, 0))
        fila = self.fila_operaciones()
        self.agregar_boton_op(fila, "➕ Insertar", self.insertar, VERDE)
        self.agregar_boton_op(fila, "🔍 Buscar", self.buscar, ACENTO)
        self.agregar_boton_op(fila, "🗑 Eliminar", self.eliminar, ROJO)
        self.tabla_ops = self.tabla(self.cuerpo, [("op", "Operación"), ("val", "Valor"), ("res", "Resultado"),
                                                  ("t", "Tiempo")], alto=4, anchos=[150, 150, 360, 110])

    def cantidad_actual(self):
        return self.estructura.total_nodos if self.estructura else 0

    def construido(self, r):
        self.estructura = r["estructura"]
        self.refrescar(r["t"])
        self.t["cota"].set(f"≈ {fmt_dec(1.44 * math.log2(r['n'] + 2), 1)}")
        muestra = ", ".join(fmt_num(v) for v in r["muestra"])
        self.lbl_muestra.config(text=f"Muestra InOrden (primeros 10): [{muestra}]")
        self.habilitar_operaciones(True)
        self.app.registrar("Construcción del AVL", r["n"], r["t"])
        self.app.log(f"✔ AVL construido: {fmt_num(r['n'])} nodos, altura {r['altura']}, {fmt_tiempo(r['t'])}.", "ok")

    def refrescar(self, t=None):
        a = self.estructura
        self.t["altura"].set(str(a.obtener_altura(a.raiz)))
        self.t["nodos"].set(fmt_num(a.total_nodos))
        if t is not None:
            self.t["t"].set(fmt_tiempo(t))

    def valor(self):
        return self.entero(self.var_val, 0, "El valor")

    def insertar(self):
        v = self.valor()
        if v is None or self.app.ocupado:
            return
        a = self.estructura
        t0 = time.perf_counter()
        a.raiz = a.insertar(a.raiz, v)
        t = time.perf_counter() - t0
        self.refrescar()
        self.registrar_op("Inserción", fmt_num(v), f"Insertado · nodos: {fmt_num(a.total_nodos)} · altura: "
                          f"{a.obtener_altura(a.raiz)}", t)

    def buscar(self):
        v = self.valor()
        if v is None or self.app.ocupado:
            return
        a = self.estructura
        t0 = time.perf_counter()
        nodo = a.buscar(a.raiz, v)
        t = time.perf_counter() - t0
        self.registrar_op("Búsqueda", fmt_num(v), "ENCONTRADO" if nodo else "NO ENCONTRADO", t)

    def eliminar(self):
        v = self.valor()
        if v is None or self.app.ocupado:
            return
        a = self.estructura
        t0 = time.perf_counter()
        existe = a.buscar(a.raiz, v) is not None
        if not existe:
            t = time.perf_counter() - t0
            self.registrar_op("Eliminación", fmt_num(v), "El valor no existe: no se eliminó nada", t)
            return
        t0 = time.perf_counter()
        a.raiz = a.eliminar(a.raiz, v)
        t = time.perf_counter() - t0
        self.refrescar()
        self.registrar_op("Eliminación", fmt_num(v), f"Eliminado · nodos: {fmt_num(a.total_nodos)}", t)


class PanelHeap(PanelEstructura):
    TITULO = "Max Heap"
    ICONO = "⛰️"
    NOMBRE = "Heap"
    TAREA = staticmethod(tarea_heap_construir)
    DESC = ("Consigna j) · Árbol binario completo almacenado en un arreglo; la raíz es siempre el máximo. "
            "Inserción y extracción O(log n); búsqueda O(n). Se construye con inserciones sucesivas.")

    def construir(self):
        self.construir_base("10.000.000", VIOLETA, [
            ("n", "Cantidad de elementos", ACENTO), ("raiz", "Elemento raíz (máximo)", VERDE),
            ("altura", "Altura aproximada", AMARILLO), ("t", "Tiempo de construcción", VIOLETA)])
        fila = self.fila_operaciones()
        self.agregar_boton_op(fila, "➕ Insertar", self.insertar, VERDE)
        self.agregar_boton_op(fila, "🔍 Buscar", self.buscar, ACENTO)
        self.agregar_boton_op(fila, "⬆ Extraer máximo", self.extraer, ROJO)
        self.tabla_ops = self.tabla(self.cuerpo, [("op", "Operación"), ("val", "Valor"), ("res", "Resultado"),
                                                  ("t", "Tiempo")], alto=4, anchos=[150, 150, 360, 110])

    def cantidad_actual(self):
        return len(self.estructura.heap) if self.estructura else 0

    def construido(self, r):
        self.estructura = r["estructura"]
        self.refrescar(r["t"])
        self.habilitar_operaciones(True)
        self.app.registrar("Construcción del Max Heap", r["n"], r["t"])
        self.app.log(f"✔ Max Heap construido: {fmt_num(r['n'])} elementos, {fmt_tiempo(r['t'])}.", "ok")

    def refrescar(self, t=None):
        h = self.estructura
        self.t["n"].set(fmt_num(len(h.heap)))
        self.t["raiz"].set(fmt_num(h.heap[0]) if h.heap else "Vacío")
        self.t["altura"].set(str(h.altura_aprox()))
        if t is not None:
            self.t["t"].set(fmt_tiempo(t))

    def valor(self):
        return self.entero(self.var_val, 0, "El valor")

    def insertar(self):
        v = self.valor()
        if v is None or self.app.ocupado:
            return
        h = self.estructura
        t0 = time.perf_counter()
        h.insertar(v)
        t = time.perf_counter() - t0
        self.refrescar()
        self.registrar_op("Inserción", fmt_num(v), f"Insertado · raíz: {fmt_num(h.heap[0])}", t)

    def buscar(self):
        v = self.valor()
        if v is None or self.app.ocupado:
            return
        self.app.ejecutar(tarea_heap_buscar, self.estructura, v, al_terminar=lambda r: self.buscado(v, r))

    def buscado(self, v, r):
        res = f"Encontrado en el índice {fmt_num(r['idx'])}" if r["idx"] != -1 else "NO ENCONTRADO (recorrió todo el arreglo)"
        self.registrar_op("Búsqueda O(n)", fmt_num(v), res, r["t"])

    def extraer(self):
        if self.app.ocupado:
            return
        h = self.estructura
        t0 = time.perf_counter()
        maximo = h.extraer_maximo()
        t = time.perf_counter() - t0
        self.refrescar()
        nueva = fmt_num(h.heap[0]) if h.heap else "ninguna"
        self.registrar_op("Extraer máximo", fmt_num(maximo) if maximo is not None else "—",
                          f"Nueva raíz: {nueva}", t)


class PanelHeapSort(Panel):
    TITULO = "Heap Sort"
    ICONO = "🔵"
    DESC = ("Consigna k) · Construye un Max Heap sobre el arreglo (bottom-up, O(n)) y extrae el máximo n − 1 veces "
            "(O(log n) cada una). In-place, O(n log n) en todos los casos. Guarda Datos_HeapSort.txt.")

    def construir(self):
        fila = tk.Frame(self.cuerpo, bg=BG)
        fila.pack(fill="x")
        self.var_n = self.campo(fila, "Tamaño de la muestra (n)", "10.000.000", 0, 20)
        Boton(fila, "▶  Ordenar con Heap Sort", self.ejecutar, ACENTO, self.app.f_boton).grid(
            row=1, column=1, sticky="w")
        self.t = self.tarjetas(self.cuerpo, [
            ("t", "Tiempo", ACENTO), ("n", "Elementos ordenados", VERDE),
            ("v", "Tiempo por elemento", AMARILLO), ("proy", "Proyección a 100 M (n log n)", VIOLETA)])
        tk.Label(self.cuerpo, text="Referencia: con n = 10.000.000 tarda ≈ 1 a 2 minutos (varía según el equipo).",
                 bg=BG, fg=MUTED, font=self.app.f_chico, anchor="w").pack(fill="x", pady=(10, 0))

    def ejecutar(self):
        n = self.entero(self.var_n, 2, "El tamaño")
        if n is not None and self.app.requiere_datos():
            self.app.ejecutar(tarea_heapsort, n, al_terminar=self.terminado)

    def terminado(self, r):
        n, t = r["n"], r["t"]
        self.t["t"].set(fmt_tiempo(t))
        self.t["n"].set(fmt_num(n))
        self.t["v"].set(f"{fmt_dec(t / n * 1e6, 2)} µs")
        proy = t * (1e8 * math.log2(1e8)) / (n * math.log2(max(n, 2)))
        self.t["proy"].set(fmt_duracion_larga(proy))
        self.app.registrar("Heap Sort", n, t)
        self.app.log(f"✔ Heap Sort finalizado en {fmt_tiempo(t)}. Guardado en Datos_HeapSort.txt.", "ok")


class PanelVerificar(Panel):
    TITULO = "Verificar ordenamiento"
    ICONO = "✅"
    DESC = ("Consigna f) · Recorre cada archivo generado comprobando que a[i] ≤ a[i+1] para todo i. "
            "Complejidad O(n), memoria O(1).")

    def construir(self):
        Boton(self.cuerpo, "▶  Verificar los archivos", self.ejecutar, VERDE, self.app.f_boton).pack(anchor="w")
        self.tabla_v = self.tabla(self.cuerpo, [("a", "Archivo"), ("n", "Elementos"), ("r", "Resultado"),
                                                ("t", "Tiempo")], alto=4, anchos=[300, 160, 180, 130])
        self.tabla_v.pack_configure(pady=(16, 0))
        self.tabla_v.tag_configure("ok", foreground=VERDE)
        self.tabla_v.tag_configure("mal", foreground=ROJO)
        self.tabla_v.tag_configure("nada", foreground=MUTED)

    def ejecutar(self):
        archivos = [("Datos_CountingSort.txt", ARCHIVO_COUNTING), ("Datos_SelectionSort.txt", ARCHIVO_SELECTION),
                    ("Datos_HeapSort.txt", ARCHIVO_HEAPSORT)]
        self.app.ejecutar(tarea_verificar, archivos, al_terminar=self.terminado)

    def terminado(self, r):
        self.tabla_v.delete(*self.tabla_v.get_children())
        for nombre, ordenado, t, lineas in r["resultados"]:
            if ordenado is None:
                self.tabla_v.insert("", "end", values=(nombre, "—", "No existe (generalo primero)", "—"), tags=("nada",))
                self.app.log(f"{nombre}: el archivo no existe todavía.", "warn")
            else:
                texto = "✔ ORDENADO" if ordenado else "✖ NO ORDENADO"
                self.tabla_v.insert("", "end", values=(nombre, fmt_num(lineas), texto, fmt_tiempo(t)),
                                    tags=("ok" if ordenado else "mal",))
                self.app.registrar(f"Verificación {nombre}", lineas, t)
                self.app.log(f"{nombre}: {texto} ({fmt_tiempo(t)})", "ok" if ordenado else "error")


class PanelComparativa(Panel):
    TITULO = "Comparativa de tiempos"
    ICONO = "📊"
    DESC = ("Resumen de todas las mediciones de esta sesión. El gráfico permite comparar visualmente los algoritmos; "
            "podés exportar los datos a un CSV para tu informe.")

    COLORES = {"Counting": VERDE, "Selection": ROJO, "Heap Sort": ACENTO, "AVL": AMARILLO,
               "Heap": VIOLETA, "Generación": MUTED, "Máx": "#39c5cf", "Verificación": "#6e7681"}

    def construir(self):
        fila = tk.Frame(self.cuerpo, bg=BG)
        fila.pack(fill="x")
        self.var_log = tk.BooleanVar(value=True)
        Boton(fila, "💾  Exportar CSV", self.exportar, VERDE, self.app.f_texto, 14, 7).pack(side="left")
        Boton(fila, "🧹  Borrar historial", self.borrar, DESHAB, self.app.f_texto, 14, 7).pack(side="left", padx=8)
        tk.Checkbutton(fila, text="Escala logarítmica", variable=self.var_log, command=self.dibujar, bg=BG, fg=TEXTO,
                       selectcolor=PANEL2, activebackground=BG, activeforeground=TEXTO, font=self.app.f_texto,
                       highlightthickness=0, bd=0).pack(side="left", padx=14)
        self.lienzo = tk.Canvas(self.cuerpo, bg=PANEL, height=250, highlightthickness=1, highlightbackground=BORDE)
        self.lienzo.pack(fill="x", pady=(12, 0))
        self.lienzo.bind("<Configure>", lambda e: self.dibujar())
        self.tabla_h = self.tabla(self.cuerpo, [("op", "Medición"), ("n", "n"), ("t", "Tiempo"), ("e", "µs por elemento"),
                                                ("h", "Hora")], alto=5, anchos=[330, 150, 140, 140, 90])

    def al_mostrar(self):
        self.refrescar()

    def color_de(self, nombre):
        for clave, color in self.COLORES.items():
            if nombre.startswith(clave):
                return color
        return ACENTO

    def refrescar(self):
        self.tabla_h.delete(*self.tabla_h.get_children())
        for i, r in enumerate(reversed(self.app.historial)):
            por_elem = fmt_dec(r["t"] / r["n"] * 1e6, 3) if r["n"] else "—"
            self.tabla_h.insert("", "end", values=(r["op"], fmt_num(r["n"]) if r["n"] else "—", fmt_tiempo(r["t"]),
                                                   por_elem, r["hora"]), tags=("par",) if i % 2 == 0 else ())
        self.dibujar()

    def dibujar(self):
        c = self.lienzo
        c.delete("all")
        datos = [r for r in self.app.historial if r["tipo"] == "tarea"][-8:]
        ancho = max(c.winfo_width(), 600)
        if not datos:
            c.create_text(ancho / 2, 125, text="Todavía no hay mediciones. Ejecutá alguna opción para ver el gráfico.",
                          fill=MUTED, font=self.app.f_texto)
            return
        logaritmica = self.var_log.get()
        mayor = max(r["t"] for r in datos)
        escala = (lambda s: math.log10(s * 1000 + 1)) if logaritmica else (lambda s: s)
        maximo = escala(mayor) or 1
        x0, x1 = 250, ancho - 120
        alto_fila = 28
        for i, r in enumerate(datos):
            y = 18 + i * alto_fila
            etiqueta = f"{r['op']} · {fmt_num(r['n'])}" if r["n"] else r["op"]
            c.create_text(x0 - 12, y + 10, text=etiqueta[:34], anchor="e", fill=TEXTO, font=self.app.f_chico)
            largo = max(4, (x1 - x0) * escala(r["t"]) / maximo)
            c.create_rectangle(x0, y, x0 + largo, y + 20, fill=self.color_de(r["op"]), outline="")
            c.create_text(x0 + largo + 8, y + 10, text=fmt_tiempo(r["t"]), anchor="w", fill=MUTED, font=self.app.f_chico)
        c.create_text(x0, 240, text=("escala logarítmica" if logaritmica else "escala lineal"), anchor="w",
                      fill=MUTED, font=self.app.f_chico)

    def exportar(self):
        if not self.app.historial:
            messagebox.showinfo("Sin datos", "Todavía no hay mediciones para exportar.")
            return
        try:
            with open(ARCHIVO_CSV, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["medicion", "n", "segundos", "microsegundos_por_elemento", "hora"])
                for r in self.app.historial:
                    w.writerow([r["op"], r["n"], f"{r['t']:.6f}".replace(".", ","),
                                f"{r['t'] / r['n'] * 1e6:.4f}".replace(".", ",") if r["n"] else "", r["hora"]])
            self.app.log(f"✔ Resultados exportados a {os.path.basename(ARCHIVO_CSV)}", "ok")
            messagebox.showinfo("Exportado", f"Se guardó el archivo:\n{ARCHIVO_CSV}")
        except OSError as e:
            messagebox.showerror("Error", f"No se pudo guardar el CSV: {e}")

    def borrar(self):
        if self.app.historial and messagebox.askyesno("Borrar historial", "¿Borrar todas las mediciones de la sesión?"):
            self.app.historial.clear()
            self.refrescar()


# ============================================================================
# APLICACIÓN PRINCIPAL
# ============================================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TP N.º 3 · Análisis y Diseño de Algoritmos · UNViMe")
        self.geometry("1220x830")
        self.minsize(1080, 760)
        self.configure(bg=BG)
        self.cola = queue.Queue()
        self.cancelar = threading.Event()
        self.ocupado = False
        self.historial = []
        self.items_menu = {}
        self.paneles = {}
        self.actual = None
        self._crear_fuentes()
        self._crear_estilos()
        self._crear_interfaz()
        self.mostrar("inicio")
        self.after(40, self._procesar_cola)
        self.after(1500, self._vigilar_datos)
        self.log("Aplicación lista. Los archivos se guardan en: " + BASE_DIR, "info")

    # ----------------------------------------------------------- estilos
    def _crear_fuentes(self):
        familias = set(tkfont.families())
        base = next((f for f in ("Segoe UI", "Helvetica Neue", "DejaVu Sans", "Arial") if f in familias), "TkDefaultFont")
        mono = next((f for f in ("Consolas", "DejaVu Sans Mono", "Courier New") if f in familias), "TkFixedFont")
        self.f_titulo = (base, 19, "bold")
        self.f_texto = (base, 10)
        self.f_chico = (base, 9)
        self.f_negrita = (base, 10, "bold")
        self.f_boton = (base, 10, "bold")
        self.f_valor = (base, 16, "bold")
        self.f_menu = (base, 11)
        self.f_mono = (mono, 10)

    def _crear_estilos(self):
        e = ttk.Style(self)
        e.theme_use("clam")
        e.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXTO, rowheight=26,
                    borderwidth=0, font=self.f_texto)
        e.configure("Treeview.Heading", background=PANEL2, foreground=TEXTO, relief="flat", font=self.f_negrita,
                    padding=6)
        e.map("Treeview", background=[("selected", ACENTO)], foreground=[("selected", "white")])
        e.map("Treeview.Heading", background=[("active", BORDE)])
        e.configure("Acento.Horizontal.TProgressbar", troughcolor=PANEL2, background=ACENTO, bordercolor=BG,
                    lightcolor=ACENTO, darkcolor=ACENTO, thickness=10)
        e.configure("Vertical.TScrollbar", background=PANEL2, troughcolor=BG, bordercolor=BG, arrowcolor=MUTED)

    # ----------------------------------------------------------- interfaz
    def _crear_interfaz(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        # Encabezado
        cab = tk.Frame(self, bg=PANEL, highlightthickness=1, highlightbackground=BORDE)
        cab.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(cab, text="⚙️  TP N.º 3 · Análisis y Diseño de Algoritmos", bg=PANEL, fg=TEXTO,
                 font=(self.f_titulo[0], 14, "bold")).pack(side="left", padx=18, pady=12)
        tk.Label(cab, text="Transformar y Conquistar", bg=PANEL, fg=MUTED, font=self.f_texto).pack(side="left")
        self.chip = tk.Label(cab, text="", bg=PANEL2, fg=TEXTO, font=self.f_texto, padx=12, pady=4)
        self.chip.pack(side="right", padx=18)
        # Barra lateral
        lateral = tk.Frame(self, bg=PANEL, width=250, highlightthickness=1, highlightbackground=BORDE)
        lateral.grid(row=1, column=0, sticky="ns")
        lateral.grid_propagate(False)
        tk.Label(lateral, text="MENÚ", bg=PANEL, fg=MUTED, font=(self.f_texto[0], 9, "bold")).pack(
            anchor="w", padx=18, pady=(16, 6))
        opciones = [("inicio", "🏠", "Inicio"), ("generar", "🎲", "1 · Generar datos"),
                    ("analizar", "🔎", "2 · Máx, mín y frecuencias"), ("counting", "🟢", "3 · Counting Sort"),
                    ("selection", "🔴", "4 · Selection Sort"), ("avl", "🌳", "5 · Árbol AVL"),
                    ("heap", "⛰️", "6 · Max Heap"), ("heapsort", "🔵", "7 · Heap Sort"),
                    ("verificar", "✅", "8 · Verificar orden"), ("comparativa", "📊", "9 · Comparativa")]
        for clave, icono, texto in opciones:
            self._item_menu(lateral, clave, f"{icono}   {texto}")
        tk.Label(lateral, text="Jeremías Mendoza\nProf. Reinaldo Gómez\nUNViMe · 2026", bg=PANEL, fg=MUTED,
                 font=self.f_chico, justify="left").pack(side="bottom", anchor="w", padx=18, pady=16)
        # Contenido (todos los paneles apilados en la misma celda)
        self.contenido = tk.Frame(self, bg=BG)
        self.contenido.grid(row=1, column=1, sticky="nsew")
        self.contenido.columnconfigure(0, weight=1)
        self.contenido.rowconfigure(0, weight=1)
        for clave, clase in [("inicio", PanelInicio), ("generar", PanelGenerar), ("analizar", PanelAnalizar),
                             ("counting", PanelCounting), ("selection", PanelSelection), ("avl", PanelAVL),
                             ("heap", PanelHeap), ("heapsort", PanelHeapSort), ("verificar", PanelVerificar),
                             ("comparativa", PanelComparativa)]:
            panel = clase(self)
            panel.grid(row=0, column=0, sticky="nsew")
            self.paneles[clave] = panel
        # Zona inferior: progreso + consola de registro
        inferior = tk.Frame(self, bg=BG)
        inferior.grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=(6, 12))
        inferior.columnconfigure(0, weight=1)
        fila = tk.Frame(inferior, bg=BG)
        fila.grid(row=0, column=0, sticky="ew")
        fila.columnconfigure(0, weight=1)
        self.lbl_estado = tk.Label(fila, text="Listo.", bg=BG, fg=TEXTO, font=self.f_texto, anchor="w")
        self.lbl_estado.grid(row=0, column=0, sticky="ew")
        self.lbl_pct = tk.Label(fila, text="", bg=BG, fg=MUTED, font=self.f_negrita)
        self.lbl_pct.grid(row=0, column=1, padx=10)
        self.btn_cancelar = Boton(fila, "✖  Cancelar", self.pedir_cancelar, ROJO, self.f_texto, 12, 3)
        self.btn_cancelar.grid(row=0, column=2)
        self.btn_cancelar.habilitar(False)
        self.barra = ttk.Progressbar(inferior, style="Acento.Horizontal.TProgressbar", maximum=100)
        self.barra.grid(row=1, column=0, sticky="ew", pady=(6, 8))
        marco = tk.Frame(inferior, bg=BORDE)
        marco.grid(row=2, column=0, sticky="ew")
        self.txt = tk.Text(marco, height=7, bg="#010409", fg=TEXTO, font=self.f_mono, relief="flat", wrap="word",
                           state="disabled", padx=10, pady=6, highlightthickness=0)
        self.txt.pack(fill="x", padx=1, pady=1)
        for tag, color in [("info", TEXTO), ("ok", VERDE), ("warn", AMARILLO), ("error", ROJO), ("hora", MUTED),
                           ("titulo", "#58a6ff")]:
            self.txt.tag_configure(tag, foreground=color)

    def _item_menu(self, padre, clave, texto):
        marco = tk.Frame(padre, bg=PANEL, cursor="hand2")
        marco.pack(fill="x")
        barra = tk.Frame(marco, bg=PANEL, width=4)
        barra.pack(side="left", fill="y")
        etiqueta = tk.Label(marco, text=texto, bg=PANEL, fg=MUTED, font=self.f_menu, anchor="w", padx=14, pady=9)
        etiqueta.pack(side="left", fill="x", expand=True)
        for w in (marco, etiqueta):
            w.bind("<Button-1>", lambda e, k=clave: self.mostrar(k))
            w.bind("<Enter>", lambda e, k=clave: self._hover(k, True))
            w.bind("<Leave>", lambda e, k=clave: self._hover(k, False))
        self.items_menu[clave] = (marco, barra, etiqueta)

    def _hover(self, clave, dentro):
        if clave == self.actual:
            return
        marco, barra, etiqueta = self.items_menu[clave]
        color = PANEL2 if dentro else PANEL
        marco.config(bg=color)
        etiqueta.config(bg=color, fg=TEXTO if dentro else MUTED)

    def mostrar(self, clave):
        self.actual = clave
        for k, (marco, barra, etiqueta) in self.items_menu.items():
            activo = k == clave
            marco.config(bg=PANEL2 if activo else PANEL)
            barra.config(bg=ACENTO if activo else PANEL)
            etiqueta.config(bg=PANEL2 if activo else PANEL, fg=TEXTO if activo else MUTED)
        panel = self.paneles[clave]
        panel.al_mostrar()
        panel.tkraise()

    # ----------------------------------------------------------- utilidades
    def log(self, texto, tag="info"):
        self.txt.config(state="normal")
        self.txt.insert("end", datetime.now().strftime("[%H:%M:%S] "), "hora")
        self.txt.insert("end", texto + "\n", tag)
        self.txt.see("end")
        self.txt.config(state="disabled")

    def registrar(self, operacion, n, t, tipo="tarea"):
        self.historial.append({"op": operacion, "n": n, "t": t, "tipo": tipo,
                               "hora": datetime.now().strftime("%H:%M:%S")})
        if self.actual == "comparativa":
            self.paneles["comparativa"].refrescar()

    def requiere_datos(self):
        if os.path.exists(ARCHIVO_DATOS):
            return True
        messagebox.showinfo("Falta Datos.txt", "Primero generá el archivo de datos con la opción 1.")
        self.mostrar("generar")
        return False

    def _vigilar_datos(self):
        if os.path.exists(ARCHIVO_DATOS):
            self.chip.config(text=f"● Datos.txt · {fmt_bytes(os.path.getsize(ARCHIVO_DATOS))}", fg=VERDE)
        else:
            self.chip.config(text="● Datos.txt no encontrado", fg=ROJO)
        self.after(2000, self._vigilar_datos)

    # ----------------------------------------------------------- ejecución de tareas
    def ejecutar(self, tarea, *args, al_terminar=None):
        """Lanza 'tarea' en un hilo aparte; el resultado vuelve por la cola a la interfaz."""
        if self.ocupado:
            messagebox.showinfo("Operación en curso", "Esperá a que termine la operación actual o cancelala.")
            return
        self.ocupado = True
        self.cancelar.clear()
        self.barra["value"] = 0
        self.lbl_pct.config(text="0 %")
        self.lbl_estado.config(text="Iniciando…")
        self.btn_cancelar.habilitar(True)
        ctx = Contexto(self.cola, self.cancelar)

        def correr():
            try:
                self.cola.put(("fin", tarea(ctx, *args), al_terminar))
            except Cancelado:
                self.cola.put(("cancelado", None, None))
            except MemoryError:
                self.cola.put(("error", "Memoria insuficiente para esta operación. Cerrá otras aplicaciones "
                                        "o usá una muestra más chica.", None))
            except Exception as exc:                                  # noqa: BLE001
                self.cola.put(("error", f"{type(exc).__name__}: {exc}", None))

        threading.Thread(target=correr, daemon=True).start()

    def pedir_cancelar(self):
        if self.ocupado:
            self.cancelar.set()
            self.lbl_estado.config(text="Cancelando…")

    def _liberar(self, texto, color=TEXTO):
        self.ocupado = False
        self.btn_cancelar.habilitar(False)
        self.lbl_estado.config(text=texto, fg=color)

    def _procesar_cola(self):
        try:
            while True:
                msg = self.cola.get_nowait()
                tipo = msg[0]
                if tipo == "log":
                    self.log(msg[1], msg[2])
                elif tipo == "progreso":
                    self.barra["value"] = msg[1] * 100
                    self.lbl_pct.config(text=f"{msg[1] * 100:.0f} %")
                    if msg[2]:
                        self.lbl_estado.config(text=msg[2], fg=TEXTO)
                elif tipo == "fin":
                    self.barra["value"] = 100
                    self.lbl_pct.config(text="100 %")
                    self._liberar("✔ Operación finalizada.", VERDE)
                    if msg[2]:
                        try:
                            msg[2](msg[1])
                        except Exception as exc:                      # noqa: BLE001
                            self.log(f"Error al mostrar resultados: {exc}", "error")
                elif tipo == "cancelado":
                    self._liberar("Operación cancelada.", AMARILLO)
                    self.barra["value"] = 0
                    self.lbl_pct.config(text="")
                    self.log("Operación cancelada por el usuario.", "warn")
                elif tipo == "error":
                    self._liberar("✖ Error en la operación.", ROJO)
                    self.log(msg[1], "error")
                    messagebox.showerror("Error", msg[1])
        except queue.Empty:
            pass
        self.after(40, self._procesar_cola)


def main():
    try:                                  # Nitidez en pantallas de alta densidad (Windows)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:                     # noqa: BLE001
        pass
    App().mainloop()


if __name__ == "__main__":
    main()
