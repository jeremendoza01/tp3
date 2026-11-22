# -*- coding: utf-8 -*-
"""
Trabajo Práctico N.º 3 · Análisis y Diseño de Algoritmos (UNViMe · 2026)
Tema: Transformar y Conquistar — Estructuras avanzadas y ordenamiento sobre 100 millones de datos.

Alumno  : Jeremías Mendoza
Profesor: Reinaldo Gómez

Decisiones de diseño principales (Consigna h):
----------------------------------------------
1. Biblioteca estándar 100 %: no requiere instalar dependencias externas.
2. Lectura y escritura en streaming / por bloques: nunca se cargan los 100 millones
   de datos completos en RAM salvo cuando el algoritmo lo exige (muestras acotadas
   para Selection Sort, AVL, Heap y Heap Sort).
3. Memoria optimizada:
   - NodoAVL usa __slots__ para eliminar el diccionario por instancia (__dict__),
     reduciendo el consumo de RAM por nodo en más del 50 % en CPython.
   - Counting Sort y el conteo de frecuencias para archivos grandes utilizan
     array('I') (enteros C sin signo de 4 bytes): ≈ 400 MB fijos para k = 10^8,
     en lugar de ≈ 800 MB (lista de referencias) o ≈ 6-7 GB (dict/Counter con 63 M de claves).
4. Heapify iterativo: tanto HeapBinario como Heap Sort implementan sift-down de forma
   iterativa, garantizando espacio auxiliar estrictamente O(1) sin consumo de pila.
5. Medición precisa: se utiliza time.perf_counter() (reloj monotónico de alta resolución)
   y se separan los tiempos de lectura/escritura (I/O) del cómputo puro del algoritmo.
6. Verificación de invariantes: tanto el AVL como el Heap incluyen verificadores
   estructurales que comprueban las propiedades formales de cada estructura.
"""

import array
import csv
import heapq
import math
import os
import random
import sys
import time
from collections import Counter
from datetime import datetime

# La altura máxima de un AVL con 10^8 nodos es <= 1.44 * log2(10^8 + 2) ≈ 39.
# Un límite de 10.000 es holgado y seguro (evita desbordamiento de pila C en Windows).
sys.setrecursionlimit(10000)

# ============================================================================
# CONSTANTES DE CONFIGURACIÓN
# ============================================================================
ARCHIVO_DATOS = "Datos.txt"
ARCHIVO_COUNTING = "Datos_CountingSort.txt"
ARCHIVO_SELECTION = "Datos_SelectionSort.txt"
ARCHIVO_HEAPSORT = "Datos_HeapSort.txt"
ARCHIVO_CSV = "resultados_tp3.csv"

CANTIDAD_NUMEROS = 100_000_000  # n = 100 millones de números (Consigna a)
RANGO_MAX = 100_000_000         # k = valores en [0, 100.000.000] (k + 1 valores posibles)

# Registro en memoria de tiempos medidos durante la sesión (Consignas g y l)
REGISTRO_TIEMPOS = []


# ============================================================================
# UTILIDADES DE FORMATO, ENTRADA Y MEDICIÓN
# ============================================================================
def fmt_num(n):
    """Formatea un entero con separador de miles por punto (1000000 -> '1.000.000')."""
    return f"{n:,}".replace(",", ".")


def fmt_dec(x, dec=2):
    """Formatea un decimal con coma decimal y punto de miles."""
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_tiempo(segundos):
    """Devuelve una representación legible del tiempo (µs, ms, s, min o h)."""
    if segundos < 1e-3:
        return f"{segundos * 1e6:.1f} µs"
    if segundos < 1:
        return f"{fmt_dec(segundos * 1e3, 2)} ms"
    if segundos < 60:
        return f"{fmt_dec(segundos, 2)} s"
    if segundos < 3600:
        mins, seg = divmod(segundos, 60)
        return f"{int(mins)} min {seg:.1f} s"
    horas, resto = divmod(segundos, 3600)
    return f"{int(horas)} h {int(resto // 60)} min"


def fmt_duracion_larga(segundos):
    """Formatea proyecciones asintóticas muy grandes (días o años)."""
    if segundos < 86_400:
        return fmt_tiempo(segundos)
    if segundos < 86_400 * 365:
        return f"≈ {fmt_dec(segundos / 86_400, 1)} días"
    return f"≈ {fmt_dec(segundos / (86_400 * 365), 1)} años"


def fmt_bytes(cantidad_bytes):
    """Formatea un tamaño en bytes a B, KB, MB o GB."""
    valor = float(cantidad_bytes)
    for unidad in ("B", "KB", "MB", "GB"):
        if valor < 1024 or unidad == "GB":
            dec = 2 if unidad in ("MB", "GB") else 0
            return f"{fmt_dec(valor, dec)} {unidad}"
        valor /= 1024


def leer_entero(mensaje, defecto=None, minimo=0, maximo=None):
    """
    Lee un entero por consola aceptando separadores de miles (puntos, comas o espacios).
    Si el usuario presiona Enter y existe 'defecto', devuelve el valor por defecto.
    """
    while True:
        entrada = input(mensaje).strip()
        if not entrada and defecto is not None:
            return defecto
        limpio = entrada.replace(".", "").replace(",", "").replace("_", "").replace(" ", "")
        try:
            valor = int(limpio)
        except ValueError:
            print("[ERROR] Ingrese un número entero válido.")
            continue
        if valor < minimo:
            print(f"[ERROR] El valor debe ser mayor o igual a {fmt_num(minimo)}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"[ERROR] El valor debe ser menor o igual a {fmt_num(maximo)}.")
            continue
        return valor


def archivo_existe(nombre_archivo, mensaje_ayuda=None):
    """Verifica la existencia de un archivo antes de operar sobre él."""
    if not os.path.exists(nombre_archivo):
        print(f"\n[ERROR] El archivo '{nombre_archivo}' no existe.")
        if mensaje_ayuda:
            print(mensaje_ayuda)
        elif nombre_archivo == ARCHIVO_DATOS:
            print("Por favor, genere primero el archivo de datos con la opción 1.")
        else:
            print("Genere primero este archivo ejecutando el algoritmo de ordenamiento correspondiente.")
        return False
    return True


def registrar_tiempo(operacion, n, t_total, t_algoritmo=None):
    """Registra una medición en la tabla de la sesión para la comparativa (Consigna g)."""
    REGISTRO_TIEMPOS.append({
        "operacion": operacion,
        "n": n,
        "t_total": t_total,
        "t_algoritmo": t_algoritmo if t_algoritmo is not None else t_total,
        "hora": datetime.now().strftime("%H:%M:%S"),
    })


def escribir_lista_por_bloques(archivo_salida, datos, bloque=1_000_000):
    """Escribe una lista de enteros a disco en bloques para minimizar llamadas de I/O."""
    with open(archivo_salida, "w", encoding="utf-8") as archivo:
        for ini in range(0, len(datos), bloque):
            archivo.write("\n".join(map(str, datos[ini:ini + bloque])) + "\n")


# ============================================================================
# CLASES DE ESTRUCTURAS DE DATOS (IMPLEMENTACIONES PROPIAS)
# ============================================================================
class NodoAVL:
    """
    Nodo del Árbol AVL.
    Usa __slots__ para ahorrar memoria (evita crear un diccionario __dict__ por cada nodo).
    """
    __slots__ = ("valor", "izquierdo", "derecho", "altura")

    def __init__(self, valor):
        self.valor = valor
        self.izquierdo = None
        self.derecho = None
        self.altura = 1


class ArbolAVL:
    """
    Árbol Binario de Búsqueda Autobalanceado (AVL).

    Invariante AVL:
        Para todo nodo, factor_balance = altura(izq) - altura(der) ∈ {-1, 0, 1}.
        Esto acota la altura en h <= 1.44 * log2(n + 2) = O(log n).

    Decisiones de diseño:
        - Los valores duplicados se insertan en el subárbol derecho (izq <= nodo <= der).
        - El rebalanceo decide las rotaciones (LL, RR, LR, RL) inspeccionando el factor
          de balance del HIJO, lo cual mantiene el invariante incluso con duplicados.
        - Búsqueda y nodo_minimo se implementan de forma iterativa para evitar sobrecarga
          de llamadas recursivas.

    Complejidades:
        - Inserción  : O(log n) en mejor, promedio y peor caso.
        - Búsqueda   : O(log n) en peor caso, O(1) si está en la raíz.
        - Eliminación: O(log n) para cualquier valor arbitrario.
        - Espacio    : O(n) (un NodoAVL por elemento).
    """

    def __init__(self):
        self.raiz = None
        self.total_nodos = 0

    def obtener_altura(self, nodo):
        """Devuelve la altura en niveles del subárbol (0 si es None)."""
        return nodo.altura if nodo else 0

    def obtener_balance(self, nodo):
        """Calcula altura(izquierdo) - altura(derecho)."""
        if not nodo:
            return 0
        return self.obtener_altura(nodo.izquierdo) - self.obtener_altura(nodo.derecho)

    def rotacion_derecha(self, y):
        """Rotación simple a la derecha (corrige desequilibrio izquierda-izquierda)."""
        x = y.izquierdo
        t2 = x.derecho
        x.derecho = y
        y.izquierdo = t2
        y.altura = 1 + max(self.obtener_altura(y.izquierdo), self.obtener_altura(y.derecho))
        x.altura = 1 + max(self.obtener_altura(x.izquierdo), self.obtener_altura(x.derecho))
        return x

    def rotacion_izquierda(self, x):
        """Rotación simple a la izquierda (corrige desequilibrio derecha-derecha)."""
        y = x.derecho
        t2 = y.izquierdo
        y.izquierdo = x
        x.derecho = t2
        x.altura = 1 + max(self.obtener_altura(x.izquierdo), self.obtener_altura(x.derecho))
        y.altura = 1 + max(self.obtener_altura(y.izquierdo), self.obtener_altura(y.derecho))
        return y

    def rebalancear(self, raiz):
        """Actualiza la altura del nodo y aplica la rotación correspondiente (LL, LR, RR, RL)."""
        raiz.altura = 1 + max(self.obtener_altura(raiz.izquierdo), self.obtener_altura(raiz.derecho))
        balance = self.obtener_balance(raiz)

        if balance > 1:
            if self.obtener_balance(raiz.izquierdo) < 0:      # Caso Izquierda-Derecha (LR)
                raiz.izquierdo = self.rotacion_izquierda(raiz.izquierdo)
            return self.rotacion_derecha(raiz)                # Caso Izquierda-Izquierda (LL)

        if balance < -1:
            if self.obtener_balance(raiz.derecho) > 0:        # Caso Derecha-Izquierda (RL)
                raiz.derecho = self.rotacion_derecha(raiz.derecho)
            return self.rotacion_izquierda(raiz)              # Caso Derecha-Derecha (RR)

        return raiz

    def insertar(self, raiz, valor):
        """Inserta 'valor' en O(log n) y rebalancea en el retorno de la recursión."""
        if not raiz:
            self.total_nodos += 1
            return NodoAVL(valor)
        if valor < raiz.valor:
            raiz.izquierdo = self.insertar(raiz.izquierdo, valor)
        else:
            raiz.derecho = self.insertar(raiz.derecho, valor)
        return self.rebalancear(raiz)

    def buscar(self, raiz, valor):
        """Búsqueda binaria iterativa en O(log n). Devuelve el NodoAVL o None."""
        actual = raiz
        while actual is not None:
            if valor == actual.valor:
                return actual
            actual = actual.derecho if valor > actual.valor else actual.izquierdo
        return None

    def nodo_minimo(self, nodo):
        """Encuentra el nodo con valor mínimo en el subárbol dado (sucesor inorden)."""
        actual = nodo
        while actual is not None and actual.izquierdo is not None:
            actual = actual.izquierdo
        return actual

    def eliminar(self, raiz, valor):
        """Elimina una ocurrencia de 'valor' en O(log n) y rebalancea el camino de retorno."""
        if not raiz:
            return None

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
        """Recorrido InOrden acotado a los primeros 'limite' elementos (orden ascendente)."""
        if raiz and len(resultado) < limite:
            self.in_orden(raiz.izquierdo, resultado, limite)
            if len(resultado) < limite:
                resultado.append(raiz.valor)
            self.in_orden(raiz.derecho, resultado, limite)

    def es_valido_avl(self):
        """
        Verifica de forma exhaustiva en O(n) las tres propiedades del Árbol AVL:
          1. Propiedad de Árbol Binario de Búsqueda (izq <= nodo <= der).
          2. Factor de balance en {-1, 0, 1} y alturas consistentes en cada nodo.
          3. Coincidencia entre los nodos recorridos y self.total_nodos.
        """
        def validar(nodo, cota_min, cota_max):
            if nodo is None:
                return True, 0, 0
            if (cota_min is not None and nodo.valor < cota_min) or (
                cota_max is not None and nodo.valor > cota_max
            ):
                return False, 0, 0
            ok_izq, h_izq, cnt_izq = validar(nodo.izquierdo, cota_min, nodo.valor)
            if not ok_izq:
                return False, 0, 0
            ok_der, h_der, cnt_der = validar(nodo.derecho, nodo.valor, cota_max)
            if not ok_der:
                return False, 0, 0
            if abs(h_izq - h_der) > 1:
                return False, 0, 0
            altura_real = 1 + max(h_izq, h_der)
            if nodo.altura != altura_real:
                return False, 0, 0
            return True, altura_real, 1 + cnt_izq + cnt_der

        ok, _, contados = validar(self.raiz, None, None)
        return ok and contados == self.total_nodos


class HeapBinario:
    """
    Heap Binario (Montículo) representado sobre un arreglo contiguo (lista Python).

    Relación padre-hijos para el índice i (base 0):
        - padre(i)    = (i - 1) // 2
        - hijo_izq(i) = 2 * i + 1
        - hijo_der(i) = 2 * i + 2

    Modos soportados (Consigna j):
        - tipo="max" (Max Heap): todo padre >= sus hijos; la raíz es el MÁXIMO.
        - tipo="min" (Min Heap): todo padre <= sus hijos; la raíz es el MÍNIMO.

    Complejidades:
        - Consultar raíz (peek)         : O(1)
        - Inserción (sift-up)           : O(log n) peor caso; O(1) promedio en datos aleatorios
        - Extracción de raíz (sift-down): O(log n) en peor caso
        - Construcción bottom-up (Floyd): O(n) garantizado
        - Búsqueda de valor arbitrario  : O(n) (no existe orden entre hermanos)
        - Espacio auxiliar de heapify   : O(1) (implementación iterativa)
    """

    def __init__(self, tipo="max"):
        if tipo not in ("max", "min"):
            raise ValueError("El tipo de heap debe ser 'max' o 'min'.")
        self.tipo = tipo
        self.es_max = (tipo == "max")
        self.heap = []

    def padre(self, i):
        return (i - 1) // 2

    def hijo_izq(self, i):
        return 2 * i + 1

    def hijo_der(self, i):
        return 2 * i + 2

    def _tiene_prioridad(self, a, b):
        """Devuelve True si 'a' debe estar por encima de 'b' según el tipo de heap."""
        return a > b if self.es_max else a < b

    def obtener_raiz(self):
        """Consulta el elemento prioritario (máximo o mínimo) en O(1) sin eliminarlo."""
        return self.heap[0] if self.heap else None

    def insertar(self, valor):
        """Agrega el elemento al final del arreglo y lo hace flotar (sift-up) en O(log n)."""
        arr = self.heap
        arr.append(valor)
        i = len(arr) - 1
        if self.es_max:
            while i > 0:
                p = (i - 1) >> 1
                if arr[i] > arr[p]:
                    arr[i], arr[p] = arr[p], arr[i]
                    i = p
                else:
                    break
        else:
            while i > 0:
                p = (i - 1) >> 1
                if arr[i] < arr[p]:
                    arr[i], arr[p] = arr[p], arr[i]
                    i = p
                else:
                    break

    def heapify_down(self, i, limite=None):
        """
        Hunde el elemento en la posición i de forma ITERATIVA hasta restaurar
        la propiedad de heap. Complejidad temporal O(log n), espacio auxiliar O(1).
        """
        arr = self.heap
        n = len(arr) if limite is None else limite
        es_max = self.es_max

        while True:
            prioritario = i
            izq = (i << 1) + 1
            der = izq + 1

            if es_max:
                if izq < n and arr[izq] > arr[prioritario]:
                    prioritario = izq
                if der < n and arr[der] > arr[prioritario]:
                    prioritario = der
            else:
                if izq < n and arr[izq] < arr[prioritario]:
                    prioritario = izq
                if der < n and arr[der] < arr[prioritario]:
                    prioritario = der

            if prioritario != i:
                arr[i], arr[prioritario] = arr[prioritario], arr[i]
                i = prioritario
            else:
                break

    def construir_bottom_up(self, datos):
        """Construye el heap a partir de una lista en O(n) mediante el algoritmo de Floyd."""
        self.heap = list(datos)
        n = len(self.heap)
        for i in range(n // 2 - 1, -1, -1):
            self.heapify_down(i, n)

    def extraer_raiz(self):
        """Elimina y devuelve la raíz (máximo en Max Heap, mínimo en Min Heap) en O(log n)."""
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        raiz = self.heap[0]
        self.heap[0] = self.heap.pop()
        self.heapify_down(0)
        return raiz

    def buscar(self, valor):
        """Búsqueda secuencial O(n): devuelve el índice si existe o -1 si no está."""
        for i, val in enumerate(self.heap):
            if val == valor:
                return i
        return -1

    def altura_aristas(self):
        """Altura medida en aristas desde la raíz hasta la hoja más profunda: floor(log2(n))."""
        return int(math.log2(len(self.heap))) if self.heap else 0

    def altura_niveles(self):
        """Altura medida en niveles/nodos (comparable con ArbolAVL): floor(log2(n)) + 1."""
        return int(math.log2(len(self.heap))) + 1 if self.heap else 0

    def es_valido_heap(self):
        """Comprueba en O(n) que todo padre cumpla la relación de prioridad con sus hijos."""
        arr = self.heap
        n = len(arr)
        for i in range(n // 2):
            izq = 2 * i + 1
            der = 2 * i + 2
            if izq < n and self._tiene_prioridad(arr[izq], arr[i]):
                return False
            if der < n and self._tiene_prioridad(arr[der], arr[i]):
                return False
        return True


class MaxHeap(HeapBinario):
    """Max Heap: la raíz siempre contiene el elemento máximo."""

    def __init__(self):
        super().__init__(tipo="max")

    def extraer_maximo(self):
        return self.extraer_raiz()


class MinHeap(HeapBinario):
    """Min Heap: la raíz siempre contiene el elemento mínimo."""

    def __init__(self):
        super().__init__(tipo="min")

    def extraer_minimo(self):
        return self.extraer_raiz()


# ============================================================================
# FUNCIONES DE LAS CONSIGNAS (a - l)
# ============================================================================
def generar_archivo_datos(cantidad=CANTIDAD_NUMEROS):
    """
    Consigna a) Generación del archivo de datos.
    Genera 'Datos.txt' con 'cantidad' enteros aleatorios uniformes en [0, RANGO_MAX].
    Escribe en bloques fijos de 1.000.000 de números para reducir llamadas al sistema (I/O)
    manteniendo memoria auxiliar acotada O(B) (constante respecto de n).
    Complejidad temporal: O(n).
    """
    print(f"\nGenerando {fmt_num(cantidad)} números aleatorios en [0, {fmt_num(RANGO_MAX)}]...")
    inicio = time.perf_counter()
    bloque = 1_000_000
    generados = 0
    try:
        with open(ARCHIVO_DATOS, "w", encoding="utf-8") as archivo:
            while generados < cantidad:
                m = min(bloque, cantidad - generados)
                numeros = [str(random.randint(0, RANGO_MAX)) for _ in range(m)]
                archivo.write("\n".join(numeros) + "\n")
                generados += m
        t_total = time.perf_counter() - inicio
        tam = os.path.getsize(ARCHIVO_DATOS)
        registrar_tiempo("Generación de Datos.txt", cantidad, t_total)
        print(f"Archivo '{ARCHIVO_DATOS}' generado en {fmt_tiempo(t_total)}.")
        print(f"Tamaño en disco: {fmt_bytes(tam)} | Velocidad: {fmt_num(int(cantidad / max(t_total, 1e-9)))} núm/s")
    except Exception as e:
        print(f"[ERROR] Error al generar el archivo: {e}")


def buscar_max_min_y_frecuencia():
    """
    Consignas b) y c) Búsqueda de máximo, mínimo y top 10 de frecuencias en UN solo recorrido.

    Decisión de diseño sobre memoria:
        - Para archivos grandes (> 50 MB, p. ej. 100 M de datos), una tabla hash Counter()
          con ~63,2 M de claves distintas consumiría entre 6 y 7 GB de RAM. En su lugar se
          emplea un array('I') contiguo de k + 1 enteros sin signo (≈ 400 MB fijos), mucho
          más seguro en equipos de 8 GB de RAM.
        - Para archivos chicos (<= 50 MB), Counter() evita recorrer 10^8 posiciones al final.
    Complejidad temporal: O(n + k) con array compacto / O(n) con tabla hash.
    """
    if not archivo_existe(ARCHIVO_DATOS):
        return

    inicio = time.perf_counter()
    maximo = None
    minimo = None
    leidos = 0
    usar_arreglo = os.path.getsize(ARCHIVO_DATOS) > 50 * 1024 * 1024

    print("\nLeyendo archivo en modo streaming (un solo recorrido)...")
    try:
        if usar_arreglo:
            conteo = array.array("I", [0]) * (RANGO_MAX + 1)
            fuera_de_rango = Counter()
            with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
                for linea in archivo:
                    s = linea.strip()
                    if not s:
                        continue
                    num = int(s)
                    leidos += 1
                    if maximo is None or num > maximo:
                        maximo = num
                    if minimo is None or num < minimo:
                        minimo = num
                    if 0 <= num <= RANGO_MAX:
                        conteo[num] += 1
                    else:
                        fuera_de_rango[num] += 1

            if leidos == 0:
                print("[AVISO] El archivo está vacío.")
                return

            # Extraemos el Top 10 manteniendo un min-heap de tamaño fijo 10: O(k) tiempo, O(1) espacio.
            top_heap = []
            distintos = len(fuera_de_rango)
            for num, frec in fuera_de_rango.items():
                if len(top_heap) < 10:
                    heapq.heappush(top_heap, (frec, num))
                elif frec > top_heap[0][0]:
                    heapq.heapreplace(top_heap, (frec, num))

            umbral = top_heap[0][0] if len(top_heap) == 10 else 0
            for num in range(max(0, minimo), min(RANGO_MAX, maximo) + 1):
                c = conteo[num]
                if c:
                    distintos += 1
                    if c > umbral:
                        if len(top_heap) < 10:
                            heapq.heappush(top_heap, (c, num))
                            if len(top_heap) == 10:
                                umbral = top_heap[0][0]
                        else:
                            heapq.heapreplace(top_heap, (c, num))
                            umbral = top_heap[0][0]

            top10 = sorted(((num, frec) for frec, num in top_heap), key=lambda par: (-par[1], par[0]))
        else:
            contador = Counter()
            with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
                for linea in archivo:
                    s = linea.strip()
                    if not s:
                        continue
                    num = int(s)
                    leidos += 1
                    if maximo is None or num > maximo:
                        maximo = num
                    if minimo is None or num < minimo:
                        minimo = num
                    contador[num] += 1

            if leidos == 0:
                print("[AVISO] El archivo está vacío.")
                return

            distintos = len(contador)
            top10 = contador.most_common(10)

        t_total = time.perf_counter() - inicio
        registrar_tiempo("Máx, mín y frecuencias", leidos, t_total)

        print(f"\n--- Análisis finalizado (Tiempo: {fmt_tiempo(t_total)}) ---")
        print(f"Total de elementos leídos : {fmt_num(leidos)}")
        print(f"Valores distintos         : {fmt_num(distintos)}")
        print(f"Número Mayor              : {fmt_num(maximo)}")
        print(f"Número Menor              : {fmt_num(minimo)}")
        print("\nLos 10 números que más se repiten:")
        print(f"  {'Pos.':<6} {'Número':>15} {'Apariciones':>14}")
        print("  " + "-" * 37)
        for pos, (num, frec) in enumerate(top10, 1):
            print(f"  {pos:<6} {fmt_num(num):>15} {fmt_num(frec):>14}")
    except MemoryError:
        print("\n[ERROR] Memoria insuficiente para realizar el análisis de frecuencias.")
    except Exception as e:
        print(f"[ERROR] Error durante el análisis: {e}")


def ordenar_counting_sort():
    """
    Consigna d) Ordenamiento por conteo (Counting Sort).

    Funcionamiento:
        Algoritmo no comparativo que cuenta las apariciones de cada entero en un arreglo
        indexado directamente por su valor y luego reconstruye la secuencia ordenada.
        Rompe la cota inferior Ω(n log n) de los métodos basados en comparaciones cuando k = O(n).

    Complejidad:
        - Tiempo : O(n + k) en mejor, promedio y peor caso.
        - Espacio: O(k) ≈ 400 MB usando array('I') (4 bytes por contador).
    """
    if not archivo_existe(ARCHIVO_DATOS):
        return

    print(f"\nIniciando Counting Sort (reservando arreglo compacto de {fmt_num(RANGO_MAX + 1)} contadores)...")
    t_inicio = time.perf_counter()
    try:
        conteo = array.array("I", [0]) * (RANGO_MAX + 1)
        mem_conteo = sys.getsizeof(conteo)
        leidos = 0

        # Fase 1: Conteo en streaming
        t0_lectura = time.perf_counter()
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                s = linea.strip()
                if s:
                    val = int(s)
                    if 0 <= val <= RANGO_MAX:
                        conteo[val] += 1
                        leidos += 1
                    else:
                        raise ValueError(f"Valor fuera de rango [0, {RANGO_MAX}]: {val}")
        t_conteo = time.perf_counter() - t0_lectura

        # Fase 2: Escritura ordenada por bloques
        t0_escritura = time.perf_counter()
        paso = 1_000_000
        total_k = RANGO_MAX + 1
        with open(ARCHIVO_COUNTING, "w", encoding="utf-8") as archivo:
            for ini in range(0, total_k, paso):
                fin = min(ini + paso, total_k)
                partes = [f"{num}\n" * c for num, c in enumerate(conteo[ini:fin], ini) if c]
                if partes:
                    archivo.write("".join(partes))
        t_escritura = time.perf_counter() - t0_escritura
        t_total = time.perf_counter() - t_inicio

        registrar_tiempo("Counting Sort", leidos, t_total, t_conteo)
        print(f"Counting Sort finalizado en {fmt_tiempo(t_total)}.")
        print(f"  - Lectura + conteo : {fmt_tiempo(t_conteo)}")
        print(f"  - Escritura salida : {fmt_tiempo(t_escritura)}")
        print(f"  - Memoria conteo   : {fmt_bytes(mem_conteo)} | Elementos: {fmt_num(leidos)}")
        print(f"  - Guardado en      : {ARCHIVO_COUNTING}")
    except MemoryError:
        print("\n[ERROR] Memoria insuficiente para ejecutar Counting Sort.")
    except Exception as e:
        print(f"[ERROR] Error en Counting Sort: {e}")


def ordenar_selection_sort(limite):
    """
    Consigna e) Ordenamiento por selección (Selection Sort).

    Funcionamiento:
        En cada iteración i busca el elemento mínimo del subarreglo [i, n) y lo coloca
        en la posición i. Realiza exactamente n(n - 1)/2 comparaciones sin importar si
        la entrada ya está ordenada.

    Complejidad:
        - Tiempo : O(n²) en mejor, promedio y peor caso.
        - Espacio: O(1) auxiliar (in-place). No es estable.
    """
    if not archivo_existe(ARCHIVO_DATOS):
        return

    print(f"\nIniciando Selection Sort con {fmt_num(limite)} elementos...")
    t_inicio = time.perf_counter()
    datos = []
    try:
        t0_lec = time.perf_counter()
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                if len(datos) >= limite:
                    break
                s = linea.strip()
                if s:
                    datos.append(int(s))
        t_lectura = time.perf_counter() - t0_lec

        n = len(datos)
        if n == 0:
            print("[AVISO] No se leyeron datos del archivo.")
            return

        t0_sort = time.perf_counter()
        for i in range(n - 1):
            indice_min = i
            min_val = datos[i]
            for j in range(i + 1, n):
                if datos[j] < min_val:
                    min_val = datos[j]
                    indice_min = j
            if indice_min != i:
                datos[i], datos[indice_min] = datos[indice_min], datos[i]
        t_sort = time.perf_counter() - t0_sort

        t0_esc = time.perf_counter()
        escribir_lista_por_bloques(ARCHIVO_SELECTION, datos)
        t_escritura = time.perf_counter() - t0_esc
        t_total = time.perf_counter() - t_inicio

        comparaciones = n * (n - 1) // 2
        proy_100m = t_sort * (CANTIDAD_NUMEROS / n) ** 2

        registrar_tiempo("Selection Sort", n, t_total, t_sort)
        print(f"Selection Sort finalizado en {fmt_tiempo(t_total)} (cómputo puro: {fmt_tiempo(t_sort)}).")
        print(f"  - Lectura / Ordenamiento / Escritura: {fmt_tiempo(t_lectura)} / {fmt_tiempo(t_sort)} / {fmt_tiempo(t_escritura)}")
        print(f"  - Comparaciones realizadas: {fmt_num(comparaciones)}")
        print(f"  - Proyección cuadrática a 100 M datos: {fmt_duracion_larga(proy_100m)}")
        print(f"  - Guardado en: {ARCHIVO_SELECTION}")
    except Exception as e:
        print(f"[ERROR] Error en Selection Sort: {e}")


def _heapify_iterativo(arr, n, i):
    """
    Restaura la propiedad de Max Heap en el subárbol con raíz i sobre arr[0..n-1].
    Implementación iterativa: O(log n) en tiempo y O(1) en espacio auxiliar.
    """
    while True:
        mayor = i
        izq = (i << 1) + 1
        der = izq + 1
        if izq < n and arr[izq] > arr[mayor]:
            mayor = izq
        if der < n and arr[der] > arr[mayor]:
            mayor = der
        if mayor != i:
            arr[i], arr[mayor] = arr[mayor], arr[i]
            i = mayor
        else:
            break


def ordenar_heap_sort(limite):
    """
    Consigna k) Ordenamiento mediante Heap Sort.

    Funcionamiento:
        Fase 1 (Build-Max-Heap): aplica heapify bottom-up desde n//2 - 1 hasta 0 en O(n).
        Fase 2 (Extracción): n - 1 veces intercambia la raíz (máximo) con el último
        elemento activo, reduce el tamaño del heap y restaura con heapify en O(log n).

    Complejidad:
        - Tiempo : O(n log n) en mejor, promedio y peor caso.
        - Espacio: O(1) auxiliar (in-place, gracias a heapify iterativo). No es estable.
    """
    if not archivo_existe(ARCHIVO_DATOS):
        return

    print(f"\nIniciando Heap Sort con {fmt_num(limite)} elementos...")
    t_inicio = time.perf_counter()
    datos = []
    try:
        t0_lec = time.perf_counter()
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                if len(datos) >= limite:
                    break
                s = linea.strip()
                if s:
                    datos.append(int(s))
        t_lectura = time.perf_counter() - t0_lec

        n = len(datos)
        if n == 0:
            print("[AVISO] No se leyeron datos del archivo.")
            return

        # Fase 1: Construcción bottom-up del Max Heap — O(n)
        t0_build = time.perf_counter()
        for i in range(n // 2 - 1, -1, -1):
            _heapify_iterativo(datos, n, i)
        t_build = time.perf_counter() - t0_build

        # Fase 2: Extracciones sucesivas — O(n log n)
        t0_extract = time.perf_counter()
        for i in range(n - 1, 0, -1):
            datos[i], datos[0] = datos[0], datos[i]
            _heapify_iterativo(datos, i, 0)
        t_extract = time.perf_counter() - t0_extract
        t_sort = t_build + t_extract

        # Fase 3: Guardado en Datos_HeapSort.txt
        t0_esc = time.perf_counter()
        escribir_lista_por_bloques(ARCHIVO_HEAPSORT, datos)
        t_escritura = time.perf_counter() - t0_esc
        t_total = time.perf_counter() - t_inicio

        proy_100m = t_sort * (CANTIDAD_NUMEROS * math.log2(CANTIDAD_NUMEROS)) / (
            n * math.log2(max(n, 2))
        )

        registrar_tiempo("Heap Sort", n, t_total, t_sort)
        print(f"Heap Sort finalizado en {fmt_tiempo(t_total)} (cómputo puro: {fmt_tiempo(t_sort)}).")
        print(f"  - Lectura: {fmt_tiempo(t_lectura)} | Build-Heap O(n): {fmt_tiempo(t_build)} | "
              f"Extracción O(n log n): {fmt_tiempo(t_extract)} | Escritura: {fmt_tiempo(t_escritura)}")
        print(f"  - Proyección teórica n log n a 100 M datos: {fmt_duracion_larga(proy_100m)}")
        print(f"  - Guardado en: {ARCHIVO_HEAPSORT}")

        # Consigna k) requiere verificar que los elementos hayan quedado ordenados
        verificar_orden(ARCHIVO_HEAPSORT)
    except Exception as e:
        print(f"[ERROR] Error en Heap Sort: {e}")


def operar_arbol_avl(limite):
    """
    Consigna i) Implementación y operación interactiva del Árbol AVL.
    Construye el árbol insertando los primeros 'limite' números de Datos.txt y ofrece
    un submenú interactivo para insertar, buscar, eliminar, ver InOrden y verificar el balanceo.
    """
    if not archivo_existe(ARCHIVO_DATOS):
        return

    arbol = ArbolAVL()
    print(f"\n[ÁRBOL AVL] Cargando primeros {fmt_num(limite)} datos...")
    t0 = time.perf_counter()
    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                if arbol.total_nodos >= limite:
                    break
                s = linea.strip()
                if s:
                    arbol.raiz = arbol.insertar(arbol.raiz, int(s))
        t_carga = time.perf_counter() - t0
        registrar_tiempo("Construcción Árbol AVL", arbol.total_nodos, t_carga)

        altura = arbol.obtener_altura(arbol.raiz)
        cota_teorica = 1.44 * math.log2(arbol.total_nodos + 2) if arbol.total_nodos else 0
        print(f"AVL construido en {fmt_tiempo(t_carga)}.")
        print(f"  - Cantidad total de nodos : {fmt_num(arbol.total_nodos)}")
        print(f"  - Altura del árbol        : {altura} (cota teórica AVL ≤ {cota_teorica:.1f})")

        muestra = []
        arbol.in_orden(arbol.raiz, muestra, 10)
        print(f"  - Recorrido InOrden (10)  : {muestra}")

        while True:
            print("\n--- Submenú Árbol AVL ---")
            print("  1. Insertar un nuevo valor   [O(log n)]")
            print("  2. Buscar un valor           [O(log n)]")
            print("  3. Eliminar un valor         [O(log n)]")
            print("  4. Mostrar recorrido InOrden (primeros N elementos)")
            print("  5. Verificar invariante AVL  (ABB + factor de balance ∈ {-1, 0, 1})")
            print("  6. Volver al menú principal")
            sub = input("Opción AVL: ").strip()

            if sub == "1":
                val = leer_entero("Ingrese el valor a INSERTAR: ", minimo=0)
                t_op = time.perf_counter()
                arbol.raiz = arbol.insertar(arbol.raiz, val)
                dt = time.perf_counter() - t_op
                registrar_tiempo("AVL · Inserción", arbol.total_nodos, dt)
                print(f"Valor {fmt_num(val)} insertado en {fmt_tiempo(dt)}.")
                print(f"  Nodos: {fmt_num(arbol.total_nodos)} | Altura: {arbol.obtener_altura(arbol.raiz)}")
            elif sub == "2":
                val = leer_entero("Ingrese el valor a BUSCAR: ", minimo=0)
                t_op = time.perf_counter()
                nodo = arbol.buscar(arbol.raiz, val)
                dt = time.perf_counter() - t_op
                registrar_tiempo("AVL · Búsqueda", arbol.total_nodos, dt)
                estado = "ENCONTRADO" if nodo else "NO ENCONTRADO"
                print(f"Resultado búsqueda: {estado} (Tiempo: {fmt_tiempo(dt)})")
            elif sub == "3":
                val = leer_entero("Ingrese el valor a ELIMINAR: ", minimo=0)
                nodos_antes = arbol.total_nodos
                t_op = time.perf_counter()
                arbol.raiz = arbol.eliminar(arbol.raiz, val)
                dt = time.perf_counter() - t_op
                registrar_tiempo("AVL · Eliminación", arbol.total_nodos, dt)
                if arbol.total_nodos < nodos_antes:
                    print(f"Valor {fmt_num(val)} ELIMINADO en {fmt_tiempo(dt)}.")
                else:
                    print(f"Valor {fmt_num(val)} NO ENCONTRADO (el árbol no se modificó; Tiempo: {fmt_tiempo(dt)}).")
                print(f"  Nodos: {fmt_num(arbol.total_nodos)} | Altura: {arbol.obtener_altura(arbol.raiz)}")
            elif sub == "4":
                n_muestra = leer_entero("¿Cuántos elementos mostrar en InOrden? (defecto 20): ", defecto=20, minimo=1)
                muestra = []
                t_op = time.perf_counter()
                arbol.in_orden(arbol.raiz, muestra, n_muestra)
                dt = time.perf_counter() - t_op
                print(f"Primeros {len(muestra)} elementos InOrden ({fmt_tiempo(dt)}): {muestra}")
            elif sub == "5":
                t_op = time.perf_counter()
                valido = arbol.es_valido_avl()
                dt = time.perf_counter() - t_op
                estado = "VÁLIDO (ABB y balanceo AVL verificados)" if valido else "INVÁLIDO"
                print(f"Verificación de invariante AVL: {estado} (Tiempo: {fmt_tiempo(dt)})")
            elif sub == "6":
                break
            else:
                print("Opción inválida. Ingrese un número del 1 al 6.")
    except Exception as e:
        print(f"[ERROR] Error operando el AVL: {e}")


def operar_heap(limite, tipo="max"):
    """
    Consigna j) Implementación y operación interactiva de Heap Binario (Max Heap y Min Heap).

    Complejidades reales:
        - Consultar raíz (máximo/mínimo): O(1)
        - Inserción (sift-up)           : O(log n) peor caso; O(1) promedio en datos aleatorios
        - Extracción de raíz (sift-down): O(log n)
        - Búsqueda de valor arbitrario  : O(n) (el heap no mantiene orden entre hermanos)
    """
    if not archivo_existe(ARCHIVO_DATOS):
        return

    etiqueta = "Max Heap" if tipo == "max" else "Min Heap"
    rol_raiz = "Máximo" if tipo == "max" else "Mínimo"
    heap_obj = MaxHeap() if tipo == "max" else MinHeap()

    print(f"\n[{etiqueta.upper()}] Construyendo con los primeros {fmt_num(limite)} datos (inserciones sucesivas)...")
    t0 = time.perf_counter()
    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                if len(heap_obj.heap) >= limite:
                    break
                s = linea.strip()
                if s:
                    heap_obj.insertar(int(s))
        t_carga = time.perf_counter() - t0
        registrar_tiempo(f"Construcción {etiqueta}", len(heap_obj.heap), t_carga)

        print(f"{etiqueta} construido en {fmt_tiempo(t_carga)}.")
        print(f"  - Cantidad de elementos : {fmt_num(len(heap_obj.heap))}")
        print(f"  - Elemento raíz ({rol_raiz}): {fmt_num(heap_obj.obtener_raiz()) if heap_obj.heap else 'Vacío'}")
        print(f"  - Altura aproximada     : {heap_obj.altura_aristas()} aristas ({heap_obj.altura_niveles()} niveles)")

        while True:
            print(f"\n--- Submenú {etiqueta} ---")
            print("  1. Insertar un nuevo elemento         [O(log n)]")
            print("  2. Buscar un valor                    [O(n)]")
            print(f"  3. Eliminar el {rol_raiz.lower()} (raíz)          [O(log n)]")
            print("  4. Mostrar estado actual del heap     [raíz en O(1)]")
            print("  5. Verificar propiedad de heap        [O(n)]")
            print("  6. Volver al menú principal")
            sub = input(f"Opción {etiqueta}: ").strip()

            if sub == "1":
                val = leer_entero("Ingrese el valor a INSERTAR: ", minimo=0)
                t_op = time.perf_counter()
                heap_obj.insertar(val)
                dt = time.perf_counter() - t_op
                registrar_tiempo(f"{etiqueta} · Inserción", len(heap_obj.heap), dt)
                print(f"Valor {fmt_num(val)} insertado en {fmt_tiempo(dt)}.")
                print(f"  Elementos: {fmt_num(len(heap_obj.heap))} | Raíz ({rol_raiz}): {fmt_num(heap_obj.obtener_raiz())}")
            elif sub == "2":
                val = leer_entero("Ingrese el valor a BUSCAR: ", minimo=0)
                t_op = time.perf_counter()
                indice = heap_obj.buscar(val)
                dt = time.perf_counter() - t_op
                registrar_tiempo(f"{etiqueta} · Búsqueda O(n)", len(heap_obj.heap), dt)
                if indice != -1:
                    print(f"ENCONTRADO en el índice {fmt_num(indice)} (Tiempo: {fmt_tiempo(dt)})")
                else:
                    print(f"NO ENCONTRADO tras recorrer {fmt_num(len(heap_obj.heap))} elementos (Tiempo: {fmt_tiempo(dt)})")
            elif sub == "3":
                t_op = time.perf_counter()
                extraido = heap_obj.extraer_raiz()
                dt = time.perf_counter() - t_op
                registrar_tiempo(f"{etiqueta} · Extraer {rol_raiz.lower()}", len(heap_obj.heap), dt)
                if extraido is None:
                    print("El heap está vacío.")
                else:
                    nueva = fmt_num(heap_obj.obtener_raiz()) if heap_obj.heap else "Vacío"
                    print(f"{rol_raiz} extraído: {fmt_num(extraido)} (Tiempo: {fmt_tiempo(dt)})")
                    print(f"  Nueva raíz: {nueva} | Elementos restantes: {fmt_num(len(heap_obj.heap))}")
            elif sub == "4":
                raiz_txt = fmt_num(heap_obj.obtener_raiz()) if heap_obj.heap else "Vacío"
                print(f"  Elementos: {fmt_num(len(heap_obj.heap))} | Raíz ({rol_raiz}): {raiz_txt} | "
                      f"Altura: {heap_obj.altura_aristas()} aristas ({heap_obj.altura_niveles()} niveles)")
            elif sub == "5":
                t_op = time.perf_counter()
                valido = heap_obj.es_valido_heap()
                dt = time.perf_counter() - t_op
                estado = f"VÁLIDO (propiedad de {etiqueta} verificada)" if valido else "INVÁLIDO"
                print(f"Verificación de invariante Heap: {estado} (Tiempo: {fmt_tiempo(dt)})")
            elif sub == "6":
                break
            else:
                print("Opción inválida. Ingrese un número del 1 al 6.")
    except Exception as e:
        print(f"[ERROR] Error operando el {etiqueta}: {e}")


def verificar_orden(archivo_nombre):
    """
    Consignas f) y k) Verificación del ordenamiento ascendente en un solo recorrido.
    Comprueba a[i] <= a[i + 1] para todo i, deteniéndose ante la primera inversión.
    Complejidad: O(n) en tiempo, O(1) en espacio.
    """
    if not archivo_existe(archivo_nombre):
        return False

    inicio = time.perf_counter()
    anterior = None
    primero = None
    leidos = 0
    esta_ordenado = True
    try:
        with open(archivo_nombre, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                s = linea.strip()
                if not s:
                    continue
                actual = int(s)
                if primero is None:
                    primero = actual
                if anterior is not None and actual < anterior:
                    esta_ordenado = False
                    break
                anterior = actual
                leidos += 1
        dt = time.perf_counter() - inicio
        if leidos == 0:
            print(f"Verificación de '{archivo_nombre}': ERROR — ARCHIVO VACÍO ({fmt_tiempo(dt)})")
            return False
        estado = "ORDENADO" if esta_ordenado else "ERROR: NO ORDENADO"
        registrar_tiempo(f"Verificación {archivo_nombre}", leidos, dt)
        print(f"Verificación de '{archivo_nombre}': {estado} | "
              f"{fmt_num(leidos)} elementos [{fmt_num(primero)} .. {fmt_num(anterior)}] "
              f"(Tiempo: {fmt_tiempo(dt)})")
        return esta_ordenado
    except Exception as e:
        print(f"[ERROR] Error verificando '{archivo_nombre}': {e}")
        return False


def mostrar_comparativa():
    """
    Consignas g) y l) Muestra en pantalla los tiempos registrados en la sesión junto con
    el análisis comparativo teórico de estructuras (AVL vs Heap) y algoritmos de ordenamiento.
    """
    print("\n" + "=" * 78)
    print(" COMPARATIVA DE TIEMPOS REGISTRADOS EN ESTA SESIÓN (Consigna g)")
    print("=" * 78)
    if not REGISTRO_TIEMPOS:
        print("  (Todavía no se registraron mediciones en esta sesión. Ejecute opciones 1 a 8.)")
    else:
        print(f"  {'Operación':<32} {'n':>13} {'T. Total':>12} {'T. Cómputo':>12} {'Hora':>8}")
        print("  " + "-" * 74)
        for r in REGISTRO_TIEMPOS:
            print(f"  {r['operacion']:<32} {fmt_num(r['n']):>13} "
                  f"{fmt_tiempo(r['t_total']):>12} {fmt_tiempo(r['t_algoritmo']):>12} {r['hora']:>8}")

    print("\n" + "=" * 78)
    print(" ANÁLISIS COMPARATIVO TEÓRICO (Consigna l)")
    print("=" * 78)

    print("\n1) Estructuras de Datos: Árbol AVL vs Heap Binario")
    print(f"  {'Operación':<16} {'Árbol AVL':<26} {'Heap Binario (Max / Min)':<34}")
    print("  " + "-" * 74)
    print(f"  {'Inserción':<16} {'O(log n) + rotaciones':<26} {'O(log n) peor; O(1) promedio':<34}")
    print(f"  {'Búsqueda':<16} {'O(log n)':<26} {'O(n) (recorrido lineal)':<34}")
    print(f"  {'Eliminación':<16} {'O(log n) cualquier valor':<26} {'O(log n) raíz; O(n) arbitrario':<34}")
    print(f"  {'Acceso ext.':<16} {'O(log n) (mín / máx)':<26} {'O(1) (raíz inmediata)':<34}")
    print(f"  {'Memoria':<16} {'O(n) mayor cte. (nodos)':<26} {'O(n) arreglo contiguo compacto':<34}")

    print("\n2) Algoritmos de Ordenamiento: Counting Sort vs Selection Sort vs Heap Sort")
    print(f"  {'Algoritmo':<16} {'Mejor Caso':<12} {'Peor Caso':<12} {'Espacio Aux.':<13} {'In-Place':<9} {'Estable'}")
    print("  " + "-" * 74)
    print(f"  {'Counting Sort':<16} {'O(n + k)':<12} {'O(n + k)':<12} {'O(k)':<13} {'No':<9} {'Sí*'}")
    print(f"  {'Selection Sort':<16} {'O(n²)':<12} {'O(n²)':<12} {'O(1)':<13} {'Sí':<9} {'No'}")
    print(f"  {'Heap Sort':<16} {'O(n log n)':<12} {'O(n log n)':<12} {'O(1)':<13} {'Sí':<9} {'No'}")
    print("  * Counting Sort es estable en su versión general con sumas prefijas.")

    print("\n3) Conclusiones para grandes volúmenes de datos (n = 100.000.000):")
    print("  • Counting Sort es el más rápido para enteros en rango acotado (k ≈ n): costo lineal")
    print("    O(n + k), pero requiere memoria O(k) (≈ 400 MB con array('I')) y solo aplica a enteros.")
    print("  • Heap Sort es la mejor opción de propósito general: O(n log n) garantizado en todos")
    print("    los casos, in-place con O(1) auxiliar y sin depender del rango de valores.")
    print("  • Selection Sort (O(n²)) es inviable a gran escala: ordenar 100 M de datos tomaría años.")
    print("  • Para búsquedas frecuentes y orden dinámico conviene AVL; para colas de prioridad, Heap.")

    if REGISTRO_TIEMPOS:
        exportar = input("\n¿Desea exportar las mediciones de esta sesión a 'resultados_tp3.csv'? (s/N): ").strip().lower()
        if exportar == "s":
            try:
                with open(ARCHIVO_CSV, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f, delimiter=";")
                    w.writerow(["operacion", "n", "segundos_total", "segundos_algoritmo", "hora"])
                    for r in REGISTRO_TIEMPOS:
                        w.writerow([
                            r["operacion"],
                            r["n"],
                            f"{r['t_total']:.6f}".replace(".", ","),
                            f"{r['t_algoritmo']:.6f}".replace(".", ","),
                            r["hora"],
                        ])
                print(f"Mediciones exportadas correctamente a '{ARCHIVO_CSV}'.")
            except OSError as e:
                print(f"[ERROR] No se pudo guardar el CSV: {e}")


# ============================================================================
# MENÚ PRINCIPAL INTERACTIVO
# ============================================================================
def mostrar_menu():
    """Orquesta el menú interactivo de consola que cubre las consignas a) a l)."""
    while True:
        print("\n" + "=" * 68)
        print("  TP N.º 3 · ANÁLISIS Y DISEÑO DE ALGORITMOS · UNViMe 2026")
        print("  Transformar y Conquistar — Estructuras y Ordenamiento (100 M)")
        print("=" * 68)
        print("  1. Generar archivo de datos (100.000.000)         [Consigna a]")
        print("  2. Buscar Máximo, Mínimo y Top 10 Frecuencias     [Consignas b, c]")
        print("  3. Ordenar con Counting Sort — O(n + k)           [Consigna d]")
        print("  4. Ordenar con Selection Sort — O(n²)             [Consigna e]")
        print("  5. Operaciones de Árbol AVL                       [Consigna i]")
        print("  6. Operaciones de Heap Binario (Max / Min Heap)   [Consigna j]")
        print("  7. Ordenar con Heap Sort — O(n log n)             [Consigna k]")
        print("  8. Verificar ordenamiento de los archivos         [Consignas f, k]")
        print("  9. Comparativa de tiempos y análisis teórico      [Consignas g, l]")
        print(" 10. Limpiar consola")
        print(" 11. Salir")

        opcion = input("\nSeleccione una opción (1-11): ").strip()

        if opcion == "1":
            print(f"\n[INFO] Por defecto se generan {fmt_num(CANTIDAD_NUMEROS)} datos (≈ 1 GB en disco, ~35-55 s).")
            cantidad = leer_entero(
                f"Cantidad de números a generar (Enter = {fmt_num(CANTIDAD_NUMEROS)}): ",
                defecto=CANTIDAD_NUMEROS,
                minimo=1,
            )
            generar_archivo_datos(cantidad)
        elif opcion == "2":
            print("\n[INFO] Recorrido completo en streaming de Datos.txt (~60-70 s para 100 M).")
            buscar_max_min_y_frecuencia()
        elif opcion == "3":
            print("\n[INFO] Counting Sort sobre Datos.txt completo (≈ 400 MB RAM, ~60-75 s para 100 M).")
            ordenar_counting_sort()
        elif opcion == "4":
            print("\n[INFO] Selection Sort es O(n²). Para 100.000 datos tarda ~2,5 min (100 M tardaría ≈ 5 años).")
            limite = leer_entero("Tamaño de muestra (Enter = 100.000): ", defecto=100_000, minimo=2)
            ordenar_selection_sort(limite)
        elif opcion == "5":
            print("\n[INFO] Árbol AVL: con 1.000.000 de nodos tarda ~10 s.")
            limite = leer_entero("Cantidad de datos a cargar en el AVL (Enter = 1.000.000): ", defecto=1_000_000, minimo=1)
            operar_arbol_avl(limite)
        elif opcion == "6":
            print("\n[INFO] Heap Binario: con 10.000.000 de datos tarda ~8 s.")
            tipo_in = input("Tipo de Heap — [1] Max Heap (defecto) / [2] Min Heap: ").strip()
            tipo = "min" if tipo_in == "2" else "max"
            limite = leer_entero("Cantidad de datos a cargar en el Heap (Enter = 10.000.000): ", defecto=10_000_000, minimo=1)
            operar_heap(limite, tipo=tipo)
        elif opcion == "7":
            print("\n[INFO] Heap Sort O(n log n): con 10.000.000 de datos tarda ~45-60 s.")
            limite = leer_entero("Tamaño de muestra para Heap Sort (Enter = 10.000.000): ", defecto=10_000_000, minimo=2)
            ordenar_heap_sort(limite)
        elif opcion == "8":
            print("\n--- Verificación de archivos ordenados ---")
            verificar_orden(ARCHIVO_COUNTING)
            verificar_orden(ARCHIVO_SELECTION)
            verificar_orden(ARCHIVO_HEAPSORT)
        elif opcion == "9":
            mostrar_comparativa()
        elif opcion == "10":
            os.system("cls" if os.name == "nt" else "clear")
        elif opcion == "11":
            print("Saliendo del programa...")
            break
        else:
            print("[ERROR] Opción inválida. Ingrese un número del 1 al 11.")


if __name__ == "__main__":
    mostrar_menu()
