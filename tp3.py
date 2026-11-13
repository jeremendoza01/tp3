import random
import time
import os
from collections import Counter
import sys
import math

# Aumentamos el límite de recursión para el Árbol AVL
sys.setrecursionlimit(2000000)

ARCHIVO_DATOS = "Datos.txt"
CANTIDAD_NUMEROS = 100000000 # 100 millones de números (n)
RANGO_MAX = 100000000        # Rango de valores (k)

# ==========================================
# CLASES DE ESTRUCTURAS DE DATOS
# ==========================================

class NodoAVL:
    # Nodo para el Árbol AVL que almacena valor, altura y punteros.
    def __init__(self, valor):
        self.valor = valor
        self.izquierdo = None
        self.derecho = None
        self.altura = 1

class ArbolAVL:
    #Es un Árbol de Búsqueda Equilibrado (AVL) que mantiene la propiedad de altura balanceada.
    #Organiza los datos jerárquicamente y controla la altura de sus ramas para garantizar que las operaciones de búsqueda,
    #inserción y eliminación sean siempre rápidas, evitando que se vuelva lento como una lista.

 
    def __init__(self):
        self.raiz = None
        self.total_nodos = 0

    #Devuelve la altura actual del nodo; 0 si es nulo.
    def obtener_altura(self, nodo): 
        if not nodo: return 0
        return nodo.altura
 
    #Calcula la diferencia de altura entre la rama izquierda y la derecha; 0 si es nulo.
    def obtener_balance(self, nodo):
        if not nodo: return 0
        return self.obtener_altura(nodo.izquierdo) - self.obtener_altura(nodo.derecho)

    #Giran los nodos afectados para restaurar el equilibrio de alturas, sin romper la regla: los menores a la izquierda, los mayores a la derecha.
    def rotacion_derecha(self, y):
        x = y.izquierdo
        T2 = x.derecho
        x.derecho = y
        y.izquierdo = T2
        y.altura = 1 + max(self.obtener_altura(y.izquierdo), self.obtener_altura(y.derecho))
        x.altura = 1 + max(self.obtener_altura(x.izquierdo), self.obtener_altura(x.derecho))
        return x
 
    def rotacion_izquierda(self, x):
        y = x.derecho
        T2 = y.izquierdo
        y.izquierdo = x
        x.derecho = T2
        x.altura = 1 + max(self.obtener_altura(x.izquierdo), self.obtener_altura(x.derecho))
        y.altura = 1 + max(self.obtener_altura(y.izquierdo), self.obtener_altura(y.derecho))
        return y

    #Rebalancea el nodo actual y aplica la rotación necesaria (casos LL, RR, LR, RL).
    def rebalancear(self, raiz):
        raiz.altura = 1 + max(self.obtener_altura(raiz.izquierdo), self.obtener_altura(raiz.derecho))
        balance = self.obtener_balance(raiz)
 
        if balance > 1:
            if self.obtener_balance(raiz.izquierdo) < 0:      # caso Izquierda-Derecha
                raiz.izquierdo = self.rotacion_izquierda(raiz.izquierdo)
            return self.rotacion_derecha(raiz)                 # caso Izquierda-Izquierda
        if balance < -1:
            if self.obtener_balance(raiz.derecho) > 0:         # caso Derecha-Izquierda
                raiz.derecho = self.rotacion_derecha(raiz.derecho)
            return self.rotacion_izquierda(raiz)               # caso Derecha-Derecha
        return raiz

    #Inserta un valor en el árbol y rebalancea si es necesario.
    def insertar(self, raiz, valor):
        if not raiz:
            self.total_nodos += 1
            return NodoAVL(valor)
        elif valor < raiz.valor:
            raiz.izquierdo = self.insertar(raiz.izquierdo, valor)
        else:
            raiz.derecho = self.insertar(raiz.derecho, valor)
        return self.rebalancear(raiz)

    #Busca un valor en el árbol; devuelve el nodo si se encuentra, o None si no.
    def buscar(self, raiz, valor):
        if raiz is None or raiz.valor == valor:
            return raiz
        if raiz.valor < valor:
            return self.buscar(raiz.derecho, valor)
        return self.buscar(raiz.izquierdo, valor)

    #Encuentra el nodo con el valor mínimo en el subárbol dado.
    def nodo_minimo(self, nodo):
        if nodo is None or nodo.izquierdo is None:
            return nodo
        return self.nodo_minimo(nodo.izquierdo)
 
    #Elimina un valor del árbol y rebalancea si es necesario.
    def eliminar(self, raiz, valor):
        if not raiz: return raiz
 
        if valor < raiz.valor:
            raiz.izquierdo = self.eliminar(raiz.izquierdo, valor)
        elif valor > raiz.valor:
            raiz.derecho = self.eliminar(raiz.derecho, valor)
        else:
            if raiz.izquierdo is None:
                self.total_nodos -= 1
                return raiz.derecho
            elif raiz.derecho is None:
                self.total_nodos -= 1
                return raiz.izquierdo
            temp = self.nodo_minimo(raiz.derecho)
            raiz.valor = temp.valor
            raiz.derecho = self.eliminar(raiz.derecho, temp.valor)
 
        return self.rebalancear(raiz)

    #Recorrido InOrden del árbol, agregando valores a la lista resultado hasta alcanzar el límite.
    def in_orden(self, raiz, resultado, limite):
        if raiz and len(resultado) < limite:
            self.in_orden(raiz.izquierdo, resultado, limite)
            if len(resultado) < limite: resultado.append(raiz.valor)
            self.in_orden(raiz.derecho, resultado, limite)

class MaxHeap:
    #Implementación de Max Heap usando un arreglo (array-based).
    def __init__(self):
        self.heap = []

    #Acá no hay punteros que consuman RAM extra. 
    def padre(self, i): return (i - 1) // 2
    def hijo_izq(self, i): return 2 * i + 1
    def hijo_der(self, i): return 2 * i + 2

    #Agrega el número al final del arreglo y lo hace 'flotar' (sift-up)
    def insertar(self, valor):
        self.heap.append(valor)
        i = len(self.heap) - 1
        while i != 0 and self.heap[self.padre(i)] < self.heap[i]:
            self.heap[i], self.heap[self.padre(i)] = self.heap[self.padre(i)], self.heap[i]
            i = self.padre(i)

    #Extrae el valor máximo del montículo y lo reorganiza.
    def extraer_maximo(self):
        if len(self.heap) == 0: return None
        if len(self.heap) == 1: return self.heap.pop()
        
        raiz = self.heap[0]
        self.heap[0] = self.heap.pop()
        self.heapify_down(0)
        return raiz

    #Reorganiza el montículo desde la raíz hacia abajo (sift-down) para mantener la propiedad de Max Heap.
    def heapify_down(self, i):
        izq = self.hijo_izq(i)
        der = self.hijo_der(i)
        mayor = i
        n = len(self.heap)

        if izq < n and self.heap[izq] > self.heap[mayor]: mayor = izq
        if der < n and self.heap[der] > self.heap[mayor]: mayor = der

        if mayor != i:
            self.heap[i], self.heap[mayor] = self.heap[mayor], self.heap[i]
            self.heapify_down(mayor)

    #Busca un valor en el heap; devuelve el índice si se encuentra, o -1 si no.
    def buscar(self, valor):
        for i, val in enumerate(self.heap):
            if val == valor: return i
        return -1

# FUNCION AUXILIAR

def archivo_existe(nombre_archivo):
    #Verifica si el archivo existe antes de operar sobre él.
    if not os.path.exists(nombre_archivo):
        print(f"\n[ERROR] El archivo '{nombre_archivo}' no existe.")
        print("Por favor, genera primero el archivo de datos seleccionando la opción 1.")
        return False
    return True

# ==========================================
# FUNCIONES DE LAS CONSIGNAS (a - k)
# ==========================================
def generar_archivo_datos():
    #Genera un archivo de texto con 100 millones de números aleatorios entre 0 y 100 millones.
    #En vez de crear los 100 millones de números en la memoria de golpe, los genera y escribe en el disco duro por bloques de a un millón. Complejidad espacial O(1).
    #Consigna a) Generación de datos.
    print(f"\nGenerando {CANTIDAD_NUMEROS} números. Esto puede tardar...")
    inicio = time.time()
    try:
        with open(ARCHIVO_DATOS, 'w') as archivo:
            bloque = 1000000
            for _ in range(CANTIDAD_NUMEROS // bloque):
                numeros = [str(random.randint(0, RANGO_MAX)) for _ in range(bloque)]
                archivo.write('\n'.join(numeros) + '\n')
        print(f"Archivo generado en {time.time() - inicio:.2f} segundos.")
    except Exception as e:
        print(f"Error al generar el archivo: {e}")

def buscar_max_min_y_frecuencia():
    #Lee el archivo de texto línea por línea.
    #Para contar las frecuencias a esa velocidad usa Counter, que por debajo es una Tabla Hash que registra y actualiza datos en tiempo constante O(1).
    #Consignas b y c) Análisis empírico de complejidad O(n).
    if not archivo_existe(ARCHIVO_DATOS): return
        
    inicio = time.time()
    maximo = -1
    minimo = RANGO_MAX + 1
    contador = Counter()
    
    print("\nLeyendo archivo (esto tomará unos segundos)...")
    try:
        with open(ARCHIVO_DATOS, 'r') as archivo:
            for linea in archivo:
                if linea.strip():
                    num = int(linea.strip())
                    if num > maximo: maximo = num
                    if num < minimo: minimo = num
                    contador[num] += 1
                    
        print(f"--- Búsqueda finalizada (Tiempo: {time.time() - inicio:.2f}s) ---")
        print(f"Número Mayor: {maximo}")
        print(f"Número Menor: {minimo}")
        print("\nLos 10 números que más se repiten:")
        for num, frec in contador.most_common(10):
            print(f"Número: {num} - Apariciones: {frec}")
    except Exception as e:
        print(f"Error durante el análisis: {e}")

def ordenar_counting_sort():
    # Algoritmo no comparativo ultra rápido O(n+k) que cuenta la frecuencia de cada número en lugar de compararlos.
    # Ideal para enteros masivos porque vence la barrera de O(n log n), aunque consume memoria proporcional al valor máximo.
    #Consigna d)
    if not archivo_existe(ARCHIVO_DATOS): return
        
    inicio = time.time()
    conteo = [0] * (RANGO_MAX + 1)
    
    print("\nIniciando Counting Sort...")
    try:
        with open(ARCHIVO_DATOS, 'r') as archivo:
            for linea in archivo:
                if linea.strip():
                    conteo[int(linea.strip())] += 1
                    
        archivo_salida = "Datos_CountingSort.txt"
        with open(archivo_salida, 'w') as archivo:
            for num, cantidad in enumerate(conteo):
                if cantidad > 0:
                    archivo.write(f"{num}\n" * cantidad)
                    
        print(f"Counting Sort finalizado en {time.time() - inicio:.2f} s. Guardado en {archivo_salida}")
    except MemoryError:
        print("\n[ERROR] Memoria insuficiente para ejecutar Counting Sort.")
    except Exception as e:
        print(f"Error en Counting Sort: {e}")

def ordenar_selection_sort(limite):
    #Ordenamiento por fuerza bruta O(n^2). Busca exhaustivamente el elemento mínimo del subarreglo restante en cada iteración.
    #Consigna e). Acotado por seguridad
    if not archivo_existe(ARCHIVO_DATOS): return
        
    inicio = time.time()
    datos = []
    print(f"\nIniciando Selection Sort con {limite} elementos...")
    
    try:
        with open(ARCHIVO_DATOS, 'r') as archivo:
            for i, linea in enumerate(archivo):
                if i >= limite: break
                if linea.strip(): datos.append(int(linea.strip()))
                
        n = len(datos)
        for i in range(n):
            indice_min = i
            for j in range(i + 1, n):
                if datos[j] < datos[indice_min]:
                    indice_min = j
            datos[i], datos[indice_min] = datos[indice_min], datos[i]
            
        archivo_salida = "Datos_SelectionSort.txt"
        with open(archivo_salida, 'w') as archivo:
            for num in datos: archivo.write(f"{num}\n")
                
        print(f"Selection Sort finalizado en {time.time() - inicio:.2f} s. Guardado en {archivo_salida}")
    except Exception as e:
        print(f"Error en Selection Sort: {e}")

def operar_arbol_avl(limite):
    #Construye un Árbol AVL leyendo datos del archivo y luego te permite buscar y eliminar números de forma interactiva para medir los tiempos.
    #Consigna i) Árbol AVL: construcción, inserción, búsqueda y eliminación.
    if not archivo_existe(ARCHIVO_DATOS): return
 
    arbol = ArbolAVL()
    print(f"\n[ÁRBOL AVL] Cargando primeros {limite} datos...")
 
    inicio_carga = time.perf_counter()
    try:
        with open(ARCHIVO_DATOS, 'r') as archivo:
            for i, linea in enumerate(archivo):
                if i >= limite: break
                if linea.strip():
                    arbol.raiz = arbol.insertar(arbol.raiz, int(linea.strip()))
        print(f"AVL construido en {time.perf_counter() - inicio_carga:.2f} segundos.")
        print(f"Altura del árbol: {arbol.obtener_altura(arbol.raiz)}")
        print(f"Cantidad total de nodos: {arbol.total_nodos}")
 
        muestra = []
        arbol.in_orden(arbol.raiz, muestra, 10)
        print(f"Muestra InOrden (primeros 10 elementos): {muestra}")
 
        # --- Inserción de un nuevo valor (consigna i) ---
        val_insertar = int(input("\nIngrese un número para INSERTAR en el AVL: "))
        t0 = time.perf_counter()
        arbol.raiz = arbol.insertar(arbol.raiz, val_insertar)
        print(f"Insertado. (Tiempo: {time.perf_counter() - t0:.6f}s)")
        print(f"Nueva cantidad total de nodos: {arbol.total_nodos} | Altura: {arbol.obtener_altura(arbol.raiz)}")
 
        # --- Búsqueda ---
        val_buscar = int(input("\nIngrese un número para BUSCAR en el AVL: "))
        t0 = time.perf_counter()
        encontrado = arbol.buscar(arbol.raiz, val_buscar)
        tiempo_busqueda = time.perf_counter() - t0
        print(f"Resultado Búsqueda: {'ENCONTRADO' if encontrado else 'NO ENCONTRADO'} (Tiempo: {tiempo_busqueda:.6f}s)")
 
        # --- Eliminación ---
        val_eliminar = int(input("Ingrese un número para ELIMINAR en el AVL: "))
        t0 = time.perf_counter()
        arbol.raiz = arbol.eliminar(arbol.raiz, val_eliminar)
        print(f"Operación de eliminación finalizada. (Tiempo: {time.perf_counter() - t0:.6f}s)")
        print(f"Nueva cantidad total de nodos: {arbol.total_nodos}")
    except ValueError:
        print("Entrada inválida. Operación cancelada.")
    except Exception as e:
        print(f"Error operando el AVL: {e}")

def operar_heap(limite):
    # Opera el Max-Heap interactivamente: permite buscar e insertar datos O(log n), y extraer el máximo absoluto en tiempo constante O(1).
    # Utiliza un arreglo plano sin punteros, demostrando que es ideal para gestionar prioridades ahorrando memoria, pero ineficiente para búsquedas O(n).
    #Consigna j) Max Heap.
    if not archivo_existe(ARCHIVO_DATOS): return
        
    heap_obj = MaxHeap()
    print(f"\n[MAX HEAP] Construyendo Heap con primeros {limite} datos...")
    
    inicio_carga = time.time()
    try:
        with open(ARCHIVO_DATOS, 'r') as archivo:
            for i, linea in enumerate(archivo):
                if i >= limite: break
                if linea.strip():
                    heap_obj.insertar(int(linea.strip()))
        print(f"Heap construido en {time.time() - inicio_carga:.2f} segundos.")
        print(f"Cantidad de elementos: {len(heap_obj.heap)}")
        print(f"Elemento Raíz (Máximo): {heap_obj.heap[0] if heap_obj.heap else 'Ninguno'}")
        
        altura_aprox = int(math.log2(len(heap_obj.heap))) if heap_obj.heap else 0
        print(f"Altura aproximada del Heap: {altura_aprox}")

        # Pruebas interactivas
        val_insertar = int(input("\nIngrese un número para INSERTAR en el Heap: "))
        inicio_ins = time.time()
        heap_obj.insertar(val_insertar)
        print(f"Insertado. (Tiempo: {time.time() - inicio_ins:.6f}s)")

        val_buscar = int(input("Ingrese un número para BUSCAR en el Heap: "))
        inicio_bus = time.time()
        indice = heap_obj.buscar(val_buscar)
        tiempo_bus = time.time() - inicio_bus
        print(f"Búsqueda O(n): {'Encontrado en índice ' + str(indice) if indice != -1 else 'No encontrado'} (Tiempo: {tiempo_bus:.6f}s)")

        print("Eliminando el MÁXIMO (Raíz)...")
        inicio_elim = time.time()
        max_extraido = heap_obj.extraer_maximo()
        print(f"Máximo extraído: {max_extraido} (Tiempo: {time.time() - inicio_elim:.6f}s)")
        print(f"Nueva Raíz: {heap_obj.heap[0] if heap_obj.heap else 'Ninguno'}")
    except ValueError:
        print("Entrada inválida. Operación cancelada.")
    except Exception as e:
        print(f"Error operando el Heap: {e}")

def ordenar_heap_sort(limite): 
    # Fase 1: Usa 'Heapify' para convertir el arreglo en un Max-Heap O(n).
    # Fase 2: Extrae la raíz repetidamente (el máximo) y la mueve al final, ordenando In-Place en O(n log n).
    if not archivo_existe(ARCHIVO_DATOS): return
        
    inicio = time.time()
    print(f"\nIniciando Heap Sort con {limite} elementos...")
    
    datos = []
    try:
        with open(ARCHIVO_DATOS, 'r') as archivo:
            for i, linea in enumerate(archivo):
                if i >= limite: break
                if linea.strip(): datos.append(int(linea.strip()))
                
        n = len(datos)
        
        def heapify(arr, n, i):
            mayor = i
            izq = 2 * i + 1
            der = 2 * i + 2
            if izq < n and arr[izq] > arr[mayor]: mayor = izq
            if der < n and arr[der] > arr[mayor]: mayor = der
            if mayor != i:
                arr[i], arr[mayor] = arr[mayor], arr[i]
                heapify(arr, n, mayor)
                
        for i in range(n // 2 - 1, -1, -1):
            heapify(datos, n, i)
            
        for i in range(n - 1, 0, -1):
            datos[i], datos[0] = datos[0], datos[i]
            heapify(datos, i, 0)
            
        archivo_salida = "Datos_HeapSort.txt"
        with open(archivo_salida, 'w') as archivo:
            for num in datos:
                archivo.write(f"{num}\n")
                
        print(f"Heap Sort finalizado en {time.time() - inicio:.2f} s. Guardado en {archivo_salida}")
    except Exception as e:
        print(f"Error en Heap Sort: {e}")
    
def verificar_orden(archivo_nombre):
    # Valida el ordenamiento mediante un recorrido secuencial O(n), comparando cada número con su predecesor.
    # Es altamente eficiente porque interrumpe la lectura al instante si detecta un error, ahorrando tiempo.
    #Consigna f y k) Verificación lineal O(n).
    if not archivo_existe(archivo_nombre): return
        
    inicio = time.time()
    anterior = -1
    esta_ordenado = True
    try:
        with open(archivo_nombre, 'r') as archivo:
            for linea in archivo:
                if linea.strip():
                    actual = int(linea.strip())
                    if actual < anterior:
                        esta_ordenado = False
                        break
                    anterior = actual
        estado = "ORDENADO" if esta_ordenado else "ERROR: NO ORDENADO"
        print(f"Verificación de '{archivo_nombre}': {estado} (Tiempo: {time.time() - inicio:.2f}s)")
    except Exception as e:
        print(f"Error verificando '{archivo_nombre}': {e}")

def mostrar_menu():
    # Muestra un menú de consola que permite al usuario interactuar y ejecutar todos los algoritmos del TP3.
    # Funciona como un orquestador para gestionar la secuencia del trabajo práctico.
    while True:
        print("\n" + "="*60)
        print(" TP3 - TRANSFORMACIÓN, ESTRUCTURAS AVANZADAS Y CONQUISTA")
        print("="*60)
        print("1. Generar archivo de datos (100 millones completos)")
        print("2. Buscar Máximo, Mínimo y Frecuencias")
        print("3. Ordenar con Counting Sort (100 millones completos - O(n+k))")
        print("4. Ordenar con Selection Sort (Muestra de 100.000 datos - O(n^2))")
        print("5. Operaciones de Árbol AVL ")
        print("6. Operaciones de Max Heap")
        print("7. Ordenar con Heap Sort")
        print("8. Verificar ordenamiento de todos los archivos generados")
        print("9. Limpiar consola")
        print("10. Salir")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == '1': 
            print(f"\n[INFO] Se generarán {CANTIDAD_NUMEROS} datos. Tiempo aprox: ~37s.")
            generar_archivo_datos()
        elif opcion == '2': 
            print(f"\n[INFO] Se procesarán {CANTIDAD_NUMEROS} datos. Tiempo aprox: ~68s.")
            buscar_max_min_y_frecuencia()
        elif opcion == '3': 
            print(f"\n[INFO] Se procesarán {CANTIDAD_NUMEROS} datos. Tiempo aprox: ~71s.")
            ordenar_counting_sort()
        elif opcion == '4': 
            print("\n[INFO] Tiempo aprox para 100.000 datos: ~157s.")
            entrada = input("Ingrese el número de entrada (100000 es un valor óptimo para evitar que se cuelgue): ")
            limite = int(entrada) if entrada.isdigit() else 100000
            ordenar_selection_sort(limite)
        elif opcion == '5': 
            print("\n[INFO] Tiempo aprox para 1.000.000 datos: ~10s.")
            entrada = input("Ingrese el número de entrada (1000000 es un valor óptimo para evitar que se cuelgue): ")
            limite = int(entrada) if entrada.isdigit() else 1000000
            operar_arbol_avl(limite)
        elif opcion == '6': 
            print("\n[INFO] Tiempo aprox para 10.000.000 datos: ~8s.")
            entrada = input("Ingrese el número de entrada (10000000 es un valor óptimo para evitar que se cuelgue): ")
            limite = int(entrada) if entrada.isdigit() else 10000000
            operar_heap(limite)
        elif opcion == '7': 
            print("\n[INFO] Tiempo aprox para 10.000.000 datos: ~58s.")
            entrada = input("Ingrese el número de entrada (10.000.000 es un valor óptimo para evitar que se cuelgue): ")
            limite = int(entrada) if entrada.isdigit() else 10000000
            ordenar_heap_sort(limite)
        elif opcion == '8': 
            verificar_orden("Datos_CountingSort.txt")
            verificar_orden("Datos_SelectionSort.txt")
            verificar_orden("Datos_HeapSort.txt")
        elif opcion == '9':
            os.system('cls' if os.name == 'nt' else 'clear')
        elif opcion == '10':
            print("Saliendo del programa...")
            break
        else: 
            print("Opción inválida. Ingrese un número del 1 al 10.")

if __name__ == "__main__":
    mostrar_menu()