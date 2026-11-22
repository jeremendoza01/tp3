# -*- coding: utf-8 -*-
"""
Pruebas unitarias automatizadas para las estructuras de datos y algoritmos del TP N.º 3.
Usa únicamente la biblioteca estándar de Python (unittest).

Ejecución:
    python -m unittest discover -s tests -v
"""

import os
import random
import tempfile
import unittest

import tp3


class TestArbolAVL(unittest.TestCase):
    def test_insercion_busqueda_y_balance_aleatorio(self):
        rng = random.Random(42)
        valores = [rng.randint(0, 1000) for _ in range(500)]
        avl = tp3.ArbolAVL()
        for v in valores:
            avl.raiz = avl.insertar(avl.raiz, v)

        self.assertEqual(avl.total_nodos, len(valores))
        self.assertTrue(avl.es_valido_avl())

        inorden = []
        avl.in_orden(avl.raiz, inorden, len(valores))
        self.assertEqual(inorden, sorted(valores))

        # Cota teórica de altura AVL: h <= 1.44 * log2(n + 2)
        self.assertLessEqual(avl.obtener_altura(avl.raiz), 14)

        for v in valores[:25]:
            self.assertIsNotNone(avl.buscar(avl.raiz, v))
        self.assertIsNone(avl.buscar(avl.raiz, 999999))

    def test_duplicados_y_eliminacion_completa(self):
        valores = [50, 20, 70, 20, 50, 50, 10, 30, 60, 80, 25, 35, 50]
        avl = tp3.ArbolAVL()
        for v in valores:
            avl.raiz = avl.insertar(avl.raiz, v)
        self.assertTrue(avl.es_valido_avl())

        # Eliminar valor inexistente no altera la cantidad de nodos
        avl.raiz = avl.eliminar(avl.raiz, 999)
        self.assertEqual(avl.total_nodos, len(valores))
        self.assertTrue(avl.es_valido_avl())

        # Eliminar todos los valores uno a uno verificando el invariante en cada paso
        restantes = list(valores)
        for v in valores:
            avl.raiz = avl.eliminar(avl.raiz, v)
            restantes.remove(v)
            self.assertEqual(avl.total_nodos, len(restantes))
            self.assertTrue(avl.es_valido_avl())
            inorden = []
            avl.in_orden(avl.raiz, inorden, len(restantes) + 1)
            self.assertEqual(inorden, sorted(restantes))

        self.assertIsNone(avl.raiz)

    def test_insercion_ordenada_peor_caso_abb(self):
        avl = tp3.ArbolAVL()
        for v in range(1, 256):
            avl.raiz = avl.insertar(avl.raiz, v)
        self.assertTrue(avl.es_valido_avl())
        self.assertEqual(avl.obtener_altura(avl.raiz), 8)


class TestHeapBinario(unittest.TestCase):
    def test_max_heap_operaciones(self):
        rng = random.Random(123)
        valores = [rng.randint(0, 500) for _ in range(300)]
        h = tp3.MaxHeap()
        for v in valores:
            h.insertar(v)

        self.assertTrue(h.es_valido_heap())
        self.assertEqual(h.obtener_raiz(), max(valores))
        self.assertNotEqual(h.buscar(valores[0]), -1)
        self.assertEqual(h.buscar(999999), -1)

        extraidos = [h.extraer_maximo() for _ in range(len(valores))]
        self.assertEqual(extraidos, sorted(valores, reverse=True))
        self.assertIsNone(h.extraer_maximo())

    def test_min_heap_operaciones(self):
        rng = random.Random(456)
        valores = [rng.randint(0, 500) for _ in range(300)]
        h = tp3.MinHeap()
        for v in valores:
            h.insertar(v)

        self.assertTrue(h.es_valido_heap())
        self.assertEqual(h.obtener_raiz(), min(valores))

        extraidos = [h.extraer_minimo() for _ in range(len(valores))]
        self.assertEqual(extraidos, sorted(valores))
        self.assertIsNone(h.extraer_minimo())

    def test_construccion_bottom_up_floyd(self):
        valores = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        h_max = tp3.MaxHeap()
        h_max.construir_bottom_up(valores)
        self.assertTrue(h_max.es_valido_heap())
        self.assertEqual(h_max.obtener_raiz(), 9)

        h_min = tp3.MinHeap()
        h_min.construir_bottom_up(valores)
        self.assertTrue(h_min.es_valido_heap())
        self.assertEqual(h_min.obtener_raiz(), 1)


class TestOrdenamientoYVerificacion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.orig_datos = tp3.ARCHIVO_DATOS
        self.orig_counting = tp3.ARCHIVO_COUNTING
        self.orig_selection = tp3.ARCHIVO_SELECTION
        self.orig_heapsort = tp3.ARCHIVO_HEAPSORT
        self.orig_rango = tp3.RANGO_MAX

        tp3.ARCHIVO_DATOS = os.path.join(self.tmp.name, "Datos.txt")
        tp3.ARCHIVO_COUNTING = os.path.join(self.tmp.name, "Datos_CountingSort.txt")
        tp3.ARCHIVO_SELECTION = os.path.join(self.tmp.name, "Datos_SelectionSort.txt")
        tp3.ARCHIVO_HEAPSORT = os.path.join(self.tmp.name, "Datos_HeapSort.txt")
        tp3.RANGO_MAX = 10_000

    def tearDown(self):
        tp3.ARCHIVO_DATOS = self.orig_datos
        tp3.ARCHIVO_COUNTING = self.orig_counting
        tp3.ARCHIVO_SELECTION = self.orig_selection
        tp3.ARCHIVO_HEAPSORT = self.orig_heapsort
        tp3.RANGO_MAX = self.orig_rango
        self.tmp.cleanup()

    def test_pipeline_completo_pequeno(self):
        tp3.generar_archivo_datos(cantidad=500)
        self.assertTrue(os.path.exists(tp3.ARCHIVO_DATOS))

        with open(tp3.ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            originales = [int(x) for x in f if x.strip()]
        self.assertEqual(len(originales), 500)
        esperado = sorted(originales)

        tp3.buscar_max_min_y_frecuencia()
        tp3.ordenar_counting_sort()
        tp3.ordenar_selection_sort(500)
        tp3.ordenar_heap_sort(500)

        for ruta in (tp3.ARCHIVO_COUNTING, tp3.ARCHIVO_SELECTION, tp3.ARCHIVO_HEAPSORT):
            self.assertTrue(tp3.verificar_orden(ruta))
            with open(ruta, "r", encoding="utf-8") as f:
                obtenidos = [int(x) for x in f if x.strip()]
            self.assertEqual(obtenidos, esperado)

    def test_verificar_archivo_desordenado_y_vacio(self):
        desordenado = os.path.join(self.tmp.name, "mal.txt")
        with open(desordenado, "w", encoding="utf-8") as f:
            f.write("1\n2\n5\n3\n4\n")
        self.assertFalse(tp3.verificar_orden(desordenado))

        vacio = os.path.join(self.tmp.name, "vacio.txt")
        with open(vacio, "w", encoding="utf-8") as f:
            f.write("")
        self.assertFalse(tp3.verificar_orden(vacio))


class TestNucleoGUI(unittest.TestCase):
    def test_estructuras_gui_avl_y_heaps(self):
        import importlib.util
        ruta_gui = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ejecutable", "tp3_gui.py")
        spec = importlib.util.spec_from_file_location("tp3_gui", ruta_gui)
        gui = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gui)

        avl = gui.ArbolAVL()
        for v in [40, 20, 60, 20, 10, 30, 50, 70]:
            avl.raiz = avl.insertar(avl.raiz, v)
        self.assertTrue(avl.es_valido_avl())
        avl.raiz = avl.eliminar(avl.raiz, 20)
        self.assertTrue(avl.es_valido_avl())

        hmax = gui.MaxHeap()
        hmin = gui.MinHeap()
        datos = [15, 3, 27, 8, 1, 99, 42]
        for v in datos:
            hmax.insertar(v)
            hmin.insertar(v)
        self.assertTrue(hmax.es_valido_heap())
        self.assertTrue(hmin.es_valido_heap())
        self.assertEqual([hmax.extraer_raiz() for _ in datos], sorted(datos, reverse=True))
        self.assertEqual([hmin.extraer_raiz() for _ in datos], sorted(datos))


if __name__ == "__main__":
    unittest.main()
