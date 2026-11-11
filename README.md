# 🚀 Análisis y Diseño de Algoritmos - Trabajo Práctico N° 3

> **Institución/Materia:** Análisis y Diseño de Algoritmos
> **Profesor:** Reinaldo Gomez
> **Alumno:** Jeremías Mendoza
> **Tema Central:** Transformación, Estructuras Avanzadas y Conquista[cite: 1]

Un proyecto desarrollado en **Python** 🐍 enfocado en el procesamiento de datos a gran escala (Big Data), la implementación de estructuras de datos avanzadas y el análisis empírico riguroso de la complejidad algorítmica espacial y temporal[cite: 1].

---

## 🎯 Características del Proyecto

El código resuelve las consignas del TP N° 3 manejando un volumen masivo de datos sin colapsar la memoria RAM, aplicando técnicas avanzadas de optimización y diseño[cite: 1]:

*   📝 **Generación Masiva de Datos:** Creación de 100.000.000 de registros secuenciales procesados por bloques para mantener una complejidad espacial auxiliar constante $O(1)$[cite: 1].
*   🔍 **Búsqueda y Frecuencia:** Algoritmo lineal de una sola pasada $O(n)$ para encontrar máximos y mínimos, junto con el uso de tablas Hash (`Counter`) para calcular frecuencias de repetición en tiempo constante $O(1)$[cite: 1].
*   ⏱️ **Ordenamiento y Análisis Empírico:** Comparación de rendimiento entre distintos paradigmas de algoritmos:
    *   **Counting Sort:** Algoritmo no comparativo de orden $O(n + k)$[cite: 1].
    *   **Selection Sort:** Algoritmo de fuerza bruta acotado por su complejidad cuadrática $O(n^2)$[cite: 1].
    *   **Heap Sort:** Enfoque de transformar y conquistar con eficiencia logarítmica $O(n \log n)$[cite: 1].
*   🌳 **Estructuras de Datos Avanzadas:** Implementación desde cero de un **Árbol AVL** (con auto-balanceo mediante rotaciones) y un **Max Heap** basado en arreglos[cite: 1].

---

## ⚙️ Entorno de Pruebas y Hardware

Para el análisis empírico del tiempo de ejecución plasmado en el informe técnico, las métricas fueron tomadas en el siguiente entorno de desarrollo[cite: 1]:

*   💻 **Procesador:** AMD Ryzen 5 5600GT with Radeon Graphics (3.60 GHz)[cite: 1]
*   🧠 **Memoria RAM:** 16,0 GB (15,4 GB utilizable)[cite: 1]
*   🖥️ **Sistema Operativo:** Windows 64 bits (Arquitectura x64)[cite: 1]

---

## 📈 Resultados Empíricos Destacados

El análisis demuestra cómo las estructuras avanzadas destrozan los límites teóricos de los algoritmos de fuerza bruta al escalar los datos[cite: 1]:

| Algoritmo | Volumen de Muestra | Tiempo de Ejecución | Complejidad Temporal | Paradigma |
| :--- | :---: | :---: | :---: | :--- |
| **Counting Sort** | 100.000.000 | ~71.03 s[cite: 1] | $O(n + k)$[cite: 1] | No comparativo[cite: 1] |
| **Heap Sort** | 10.000.000 | ~58.36 s[cite: 1] | $O(n \log n)$[cite: 1] | Transformar y Conquistar[cite: 1] |
| **Selection Sort** | 100.000 | ~157.25 s[cite: 1] | $O(n^2)$[cite: 1] | Fuerza Bruta[cite: 1] |

---

## 🛠️ Instrucciones de Uso y Ejecución

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/jeremendoza01/tp3.git](https://github.com/jeremendoza01/tp3.git)
