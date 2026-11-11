# 🚀 Trabajo Práctico N° 3 - Análisis y Diseño de Algoritmos

**Procesamiento de Big Data, Estructuras Avanzadas y Análisis Empírico**

> 🎓 **Institución / Materia:** Análisis y Diseño de Algoritmos
> 
> 
> 👨‍🏫 **Profesor:** Reinaldo Gomez
> 🧑‍💻 **Alumno:** Jeremías Mendoza
> 🧠 **Paradigma Central:** Transformación, Estructuras Avanzadas y Conquista.
> 
> 

---

## 🎯 Descripción del Proyecto

Este repositorio contiene la implementación en **Python** de la resolución del Trabajo Práctico N° 3 mediante el script principal del proyecto. El sistema está diseñado para procesar un volumen masivo de datos (**100.000.000 de registros**) asegurando que el equipo no colapse por falta de memoria (`MemoryError`), logrando una complejidad espacial auxiliar constante $O(1)$ al procesar por bloques.

El programa cuenta con un menú interactivo que permite configurar los tamaños de entrada, medir empíricamente los tiempos de ejecución y comparar la eficiencia entre algoritmos de distintos paradigmas.

---

## ✨ Características y Lógica Implementada

* 📝 **Generación y Búsqueda Masiva:** Creación de 100 millones de datos optimizada en bloques. Algoritmo de búsqueda lineal $O(n)$ de una sola pasada que encuentra el máximo y mínimo de forma eficiente.


* 🔍 **Análisis de Frecuencia con Tablas Hash:** Uso de la estructura `Counter` para procesar inserciones en tiempo constante promedio $O(1)$, comprobando estadísticamente la distribución uniforme de los datos aleatorios.


* 🌳 **Implementación de Árbol AVL:** Estructura dinámica basada en nodos con punteros, auto-balanceada mediante rotaciones.


* 🏗️ **Implementación de Heap (Montículo):** Estructura avanzada representada en un arreglo (array) contiguo sin punteros, lo que optimiza significativamente la memoria RAM requerida.



---

## 📊 Análisis Empírico de Ordenamiento

El proyecto demuestra empíricamente cómo las estructuras avanzadas superan los límites teóricos de los algoritmos de fuerza bruta al escalar los datos:

| Algoritmo | Volumen de Datos | Tiempo Empírico | Complejidad Temporal | Análisis y Comportamiento |
| --- | --- | --- | --- | --- |
| **Counting Sort** | 100.000.000 | ~71.03 s

 | $O(n + k)$

 | **No comparativo:** Ordenó el total masivo casi al mismo tiempo de lectura. Rompe el límite inferior $\Omega(n \log n)$ sacrificando memoria auxiliar $O(k)$.

 |
| **Heap Sort** | 1.000.000 | ~5.17 s

 | $O(n \log n)$

 | **Transformar y Conquistar:** Muestra una escalabilidad superior, procesando muestras grandes de manera sumamente eficiente.

 |
| **Selection Sort** | 100.000 | ~157.25 s

 | $O(n^2)$

 | **Fuerza Bruta:** Inviable para Big Data. Procesar los 100 millones de registros requeriría años de procesamiento ininterrumpido.

 |

---

## ⚙️ Entorno de Hardware (Banco de Pruebas)

Todas las métricas de tiempo expresadas en este README y en el informe técnico fueron cronometradas en el siguiente entorno físico de desarrollo:

* 💻 **Procesador:** AMD Ryzen 5 5600GT with Radeon Graphics (3.60 GHz).


* 🧠 **Memoria RAM:** 16,0 GB (15,4 GB utilizable).


* 🖥️ **Sistema Operativo:** Windows de 64 bits (Arquitectura x64).



---

## 🛠️ Cómo instalar y ejecutar

1. **Clona el repositorio** en tu entorno local:
```bash
git clone https://github.com/jeremendoza01/tp3.git

```


2. **Navega al directorio** del proyecto:
```bash
cd tp3

```


3. **Ejecuta el script principal:**
```bash
python tp3_transformar_conquistar.py

```


4. **Interacción:** Sigue el menú en la consola de comandos. El sistema te sugerirá tamaños de entrada óptimos antes de cada ejecución para evitar colapsos en tu PC.



> ⚠️ **Aviso de Almacenamiento:** Los archivos `.txt` generados superan ampliamente los límites de GitHub y han sido excluidos vía `.gitignore`. Se generarán automáticamente en tu computadora de forma local al utilizar la opción correspondiente del menú interactivo. Asegúrate de contar con suficiente espacio libre en disco.
