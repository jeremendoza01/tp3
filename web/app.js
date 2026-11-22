"use strict";

/**
 * TP N.º 3 · Análisis y Diseño de Algoritmos · UNViMe 2026
 * Laboratorio Web Interactivo (100 % Cliente · Compatible con Vercel / GitHub Pages)
 * Alumno: Jeremías Mendoza · Profesor: Reinaldo Gómez
 */

// ============================================================================
// ESTADO GLOBAL Y UTILIDADES DE FORMATO
// ============================================================================
const STATE = {
  datos: null,          // Int32Array con los números de Datos.txt
  rangoMax: 100000000,  // k
  salidas: {
    counting: null,     // Int32Array ordenado por Counting Sort
    selection: null,    // Int32Array ordenado por Selection Sort
    heapsort: null      // Int32Array ordenado por Heap Sort
  },
  avl: null,
  heap: null,
  historial: []
};

const fmtNum = (n) => Number(n).toLocaleString("es-AR");
const fmtDec = (x, dec = 2) => Number(x).toLocaleString("es-AR", { minimumFractionDigits: dec, maximumFractionDigits: dec });

function fmtTiempo(ms) {
  const s = ms / 1000;
  if (s < 1e-3) return `${(s * 1e6).toFixed(1)} µs`;
  if (s < 1) return `${fmtDec(s * 1e3, 2)} ms`;
  if (s < 60) return `${fmtDec(s, 2)} s`;
  const m = Math.floor(s / 60);
  const rem = s - m * 60;
  return `${m} min ${rem.toFixed(0)} s`;
}

function fmtDuracionLarga(segundos) {
  if (segundos < 86400) return fmtTiempo(segundos * 1000);
  if (segundos < 86400 * 365) return `≈ ${fmtDec(segundos / 86400, 1)} días`;
  return `≈ ${fmtDec(segundos / (86400 * 365), 1)} años`;
}

function fmtBytes(bytes) {
  let b = bytes;
  for (const u of ["B", "KB", "MB", "GB"]) {
    if (b < 1024 || u === "GB") {
      return `${fmtDec(b, u === "MB" || u === "GB" ? 2 : 0)} ${u}`;
    }
    b /= 1024;
  }
  return `${bytes} B`;
}

function ahoraHora() {
  return new Date().toTimeString().slice(0, 8);
}

function logConsola(texto, tipo = "info") {
  const box = document.getElementById("console-log");
  const div = document.createElement("div");
  div.className = "log-line";
  const clase = tipo === "ok" ? "log-ok" : tipo === "warn" ? "log-warn" : tipo === "error" ? "log-err" : tipo === "titulo" ? "log-title" : "";
  div.innerHTML = `<span class="log-time">[${ahoraHora()}]</span> <span class="${clase}">${texto}</span>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function setProgreso(fraccion, texto) {
  const pct = Math.min(100, Math.max(0, Math.round(fraccion * 100)));
  document.getElementById("progressbar-fill").style.width = `${pct}%`;
  document.getElementById("status-pct").textContent = `${pct} %`;
  if (texto) document.getElementById("status-text").textContent = texto;
}

function cederHilo() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

function registrarMedicion(op, n, ms, origen = "Sesión Web") {
  STATE.historial.push({ op, n, ms, hora: `${origen} · ${ahoraHora()}` });
  refrescarComparativa();
}

function descargarArchivoTexto(nombre, arr, maxLineas = 200000) {
  if (!arr || arr.length === 0) return;
  const limite = Math.min(arr.length, maxLineas);
  const lineas = [];
  for (let i = 0; i < limite; i++) lineas.push(arr[i]);
  const contenido = lineas.join("\n") + "\n";
  const blob = new Blob([contenido], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  a.click();
  URL.revokeObjectURL(url);
  const nota = arr.length > maxLineas ? ` (muestra de ${fmtNum(limite)} líneas para descarga instantánea)` : "";
  logConsola(`✔ Descargado ${nombre}${nota}.`, "ok");
}

function requiereDatos() {
  if (STATE.datos && STATE.datos.length > 0) return true;
  logConsola("⚠ Primero debés generar Datos.txt en la opción 1.", "warn");
  mostrarPanel("generar");
  return false;
}

// ============================================================================
// ESTRUCTURAS DE DATOS: ÁRBOL AVL Y HEAP BINARIO (MAX / MIN)
// ============================================================================
class NodoAVL {
  constructor(valor) {
    this.valor = valor;
    this.izquierdo = null;
    this.derecho = null;
    this.altura = 1;
  }
}

class ArbolAVL {
  constructor() {
    this.raiz = null;
    this.totalNodos = 0;
  }

  obtenerAltura(n) {
    return n ? n.altura : 0;
  }

  obtenerBalance(n) {
    return n ? this.obtenerAltura(n.izquierdo) - this.obtenerAltura(n.derecho) : 0;
  }

  rotacionDerecha(y) {
    const x = y.izquierdo;
    const t2 = x.derecho;
    x.derecho = y;
    y.izquierdo = t2;
    y.altura = 1 + Math.max(this.obtenerAltura(y.izquierdo), this.obtenerAltura(y.derecho));
    x.altura = 1 + Math.max(this.obtenerAltura(x.izquierdo), this.obtenerAltura(x.derecho));
    return x;
  }

  rotacionIzquierda(x) {
    const y = x.derecho;
    const t2 = y.izquierdo;
    y.izquierdo = x;
    x.derecho = t2;
    x.altura = 1 + Math.max(this.obtenerAltura(x.izquierdo), this.obtenerAltura(x.derecho));
    y.altura = 1 + Math.max(this.obtenerAltura(y.izquierdo), this.obtenerAltura(y.derecho));
    return y;
  }

  rebalancear(raiz) {
    raiz.altura = 1 + Math.max(this.obtenerAltura(raiz.izquierdo), this.obtenerAltura(raiz.derecho));
    const balance = this.obtenerBalance(raiz);
    if (balance > 1) {
      if (this.obtenerBalance(raiz.izquierdo) < 0) {
        raiz.izquierdo = this.rotacionIzquierda(raiz.izquierdo);
      }
      return this.rotacionDerecha(raiz);
    }
    if (balance < -1) {
      if (this.obtenerBalance(raiz.derecho) > 0) {
        raiz.derecho = this.rotacionDerecha(raiz.derecho);
      }
      return this.rotacionIzquierda(raiz);
    }
    return raiz;
  }

  insertar(raiz, valor) {
    if (!raiz) {
      this.totalNodos++;
      return new NodoAVL(valor);
    }
    if (valor < raiz.valor) {
      raiz.izquierdo = this.insertar(raiz.izquierdo, valor);
    } else {
      raiz.derecho = this.insertar(raiz.derecho, valor);
    }
    return this.rebalancear(raiz);
  }

  buscar(raiz, valor) {
    let act = raiz;
    while (act !== null) {
      if (valor === act.valor) return act;
      act = valor > act.valor ? act.derecho : act.izquierdo;
    }
    return null;
  }

  nodoMinimo(nodo) {
    let act = nodo;
    while (act && act.izquierdo !== null) act = act.izquierdo;
    return act;
  }

  eliminar(raiz, valor) {
    if (!raiz) return null;
    if (valor < raiz.valor) {
      raiz.izquierdo = this.eliminar(raiz.izquierdo, valor);
    } else if (valor > raiz.valor) {
      raiz.derecho = this.eliminar(raiz.derecho, valor);
    } else {
      if (!raiz.izquierdo) {
        this.totalNodos--;
        return raiz.derecho;
      }
      if (!raiz.derecho) {
        this.totalNodos--;
        return raiz.izquierdo;
      }
      const sucesor = this.nodoMinimo(raiz.derecho);
      raiz.valor = sucesor.valor;
      raiz.derecho = this.eliminar(raiz.derecho, sucesor.valor);
    }
    return this.rebalancear(raiz);
  }

  inOrden(raiz, res, limite = 15) {
    if (!raiz || res.length >= limite) return;
    this.inOrden(raiz.izquierdo, res, limite);
    if (res.length < limite) res.push(raiz.valor);
    this.inOrden(raiz.derecho, res, limite);
  }

  esValidoAVL() {
    const validar = (nodo, min, max) => {
      if (!nodo) return { ok: true, h: 0, cnt: 0 };
      if ((min !== null && nodo.valor < min) || (max !== null && nodo.valor > max)) {
        return { ok: false, h: 0, cnt: 0 };
      }
      const izq = validar(nodo.izquierdo, min, nodo.valor);
      if (!izq.ok) return izq;
      const der = validar(nodo.derecho, nodo.valor, max);
      if (!der.ok) return der;
      if (Math.abs(izq.h - der.h) > 1) return { ok: false, h: 0, cnt: 0 };
      const h = 1 + Math.max(izq.h, der.h);
      if (nodo.altura !== h) return { ok: false, h: 0, cnt: 0 };
      return { ok: true, h, cnt: 1 + izq.cnt + der.cnt };
    };
    const r = validar(this.raiz, null, null);
    return r.ok && r.cnt === this.totalNodos;
  }
}

class HeapBinario {
  constructor(tipo = "max") {
    this.tipo = tipo;
    this.esMax = tipo === "max";
    this.heap = [];
  }

  insertar(valor) {
    const arr = this.heap;
    arr.push(valor);
    let i = arr.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      const subir = this.esMax ? arr[i] > arr[p] : arr[i] < arr[p];
      if (!subir) break;
      const tmp = arr[i];
      arr[i] = arr[p];
      arr[p] = tmp;
      i = p;
    }
  }

  heapifyDown(i) {
    const arr = this.heap;
    const n = arr.length;
    while (true) {
      let prio = i;
      const izq = i * 2 + 1;
      const der = izq + 1;
      if (this.esMax) {
        if (izq < n && arr[izq] > arr[prio]) prio = izq;
        if (der < n && arr[der] > arr[prio]) prio = der;
      } else {
        if (izq < n && arr[izq] < arr[prio]) prio = izq;
        if (der < n && arr[der] < arr[prio]) prio = der;
      }
      if (prio !== i) {
        const tmp = arr[i];
        arr[i] = arr[prio];
        arr[prio] = tmp;
        i = prio;
      } else {
        break;
      }
    }
  }

  extraerRaiz() {
    if (this.heap.length === 0) return null;
    if (this.heap.length === 1) return this.heap.pop();
    const raiz = this.heap[0];
    this.heap[0] = this.heap.pop();
    this.heapifyDown(0);
    return raiz;
  }

  buscar(valor) {
    for (let i = 0; i < this.heap.length; i++) {
      if (this.heap[i] === valor) return i;
    }
    return -1;
  }

  alturaAristas() {
    return this.heap.length > 0 ? Math.floor(Math.log2(this.heap.length)) : 0;
  }

  alturaNiveles() {
    return this.heap.length > 0 ? Math.floor(Math.log2(this.heap.length)) + 1 : 0;
  }

  esValidoHeap() {
    const arr = this.heap;
    const n = arr.length;
    const limite = Math.floor(n / 2);
    for (let i = 0; i < limite; i++) {
      const izq = 2 * i + 1;
      const der = 2 * i + 2;
      if (this.esMax) {
        if ((izq < n && arr[izq] > arr[i]) || (der < n && arr[der] > arr[i])) return false;
      } else {
        if ((izq < n && arr[izq] < arr[i]) || (der < n && arr[der] < arr[i])) return false;
      }
    }
    return true;
  }
}

// ============================================================================
// DIBUJO SVG DE ÁRBOLES (AVL Y HEAP)
// ============================================================================
function dibujarArbolSVG(svgId, obtenerRaizInfo) {
  const svg = document.getElementById(svgId);
  svg.innerHTML = "";
  const raiz = obtenerRaizInfo();
  if (!raiz) {
    svg.innerHTML = `<text x="320" y="120" fill="#8b949e" text-anchor="middle" font-size="13">Estructura vacía</text>`;
    return;
  }

  const niveles = [[{ nodo: raiz, x: 320, y: 32, spread: 145 }]];
  const maxProf = 3; // muestra hasta 4 niveles (15 nodos)
  const lineas = [];
  const circulos = [];

  for (let d = 0; d <= maxProf; d++) {
    const fila = niveles[d];
    if (!fila) break;
    const sig = [];
    for (const item of fila) {
      const { nodo, x, y, spread } = item;
      circulos.push({ x, y, etiqueta: nodo.etiqueta, sub: nodo.sub, color: nodo.color });
      if (d < maxProf) {
        if (nodo.izq) {
          const nx = x - spread;
          const ny = y + 58;
          lineas.push({ x1: x, y1: y, x2: nx, y2: ny });
          sig.push({ nodo: nodo.izq, x: nx, y: ny, spread: spread / 2 });
        }
        if (nodo.der) {
          const nx = x + spread;
          const ny = y + 58;
          lineas.push({ x1: x, y1: y, x2: nx, y2: ny });
          sig.push({ nodo: nodo.der, x: nx, y: ny, spread: spread / 2 });
        }
      }
    }
    if (sig.length > 0) niveles.push(sig);
  }

  let html = "";
  for (const l of lineas) {
    html += `<line x1="${l.x1}" y1="${l.y1}" x2="${l.x2}" y2="${l.y2}" stroke="#30363d" stroke-width="2" />`;
  }
  for (const c of circulos) {
    html += `
      <g>
        <circle cx="${c.x}" cy="${c.y}" r="18" fill="#161b22" stroke="${c.color}" stroke-width="2.2" />
        <text x="${c.x}" y="${c.y + 3}" fill="#e6edf3" text-anchor="middle" font-size="10.5" font-weight="700">${c.etiqueta}</text>
        <text x="${c.x}" y="${c.y + 29}" fill="#8b949e" text-anchor="middle" font-size="9.5">${c.sub}</text>
      </g>`;
  }
  svg.innerHTML = html;
}

function adaptarNodoAVL(arbol, nodo, prof = 0) {
  if (!nodo || prof > 3) return null;
  const bf = arbol.obtenerBalance(nodo);
  return {
    etiqueta: nodo.valor > 99999 ? `${Math.round(nodo.valor / 1000)}k` : String(nodo.valor),
    sub: `h:${nodo.altura} bf:${bf}`,
    color: Math.abs(bf) <= 1 ? "#3fb950" : "#f85149",
    izq: adaptarNodoAVL(arbol, nodo.izquierdo, prof + 1),
    der: adaptarNodoAVL(arbol, nodo.derecho, prof + 1)
  };
}

function adaptarNodoHeap(heapObj, idx = 0, prof = 0) {
  if (idx >= heapObj.heap.length || prof > 3) return null;
  const val = heapObj.heap[idx];
  return {
    etiqueta: val > 99999 ? `${Math.round(val / 1000)}k` : String(val),
    sub: `[${idx}]`,
    color: idx === 0 ? "#a371f7" : "#1f6feb",
    izq: adaptarNodoHeap(heapObj, idx * 2 + 1, prof + 1),
    der: adaptarNodoHeap(heapObj, idx * 2 + 2, prof + 1)
  };
}

// ============================================================================
// CONSIGNA a) GENERACIÓN DE DATOS
// ============================================================================
async function ejecutarGenerar() {
  const n = parseInt(document.getElementById("gen-preset").value, 10);
  const rango = parseInt(document.getElementById("gen-rango").value, 10);
  const btn = document.getElementById("btn-generar");
  btn.disabled = true;

  logConsola(`Generando ${fmtNum(n)} números aleatorios en [0, ${fmtNum(rango)}]…`, "titulo");
  setProgreso(0.02, "Reservando memoria tipada Int32Array…");
  await cederHilo();

  try {
    const t0 = performance.now();
    const arr = new Int32Array(n);
    const bloque = 2_500_000;
    const maxPlus1 = rango + 1;

    for (let ini = 0; ini < n; ini += bloque) {
      const fin = Math.min(ini + bloque, n);
      for (let i = ini; i < fin; i++) {
        arr[i] = Math.floor(Math.random() * maxPlus1);
      }
      setProgreso(fin / n, `Generados ${fmtNum(fin)} de ${fmtNum(n)} números…`);
      await cederHilo();
    }

    const dt = performance.now() - t0;
    STATE.datos = arr;
    STATE.rangoMax = rango;
    STATE.salidas = { counting: null, selection: null, heapsort: null };

    const bytesRam = arr.byteLength;
    const bytesDiscoEst = n * 9.5;
    document.getElementById("gen-t").textContent = fmtTiempo(dt);
    document.getElementById("gen-count").textContent = fmtNum(n);
    document.getElementById("gen-mem").textContent = `${fmtBytes(bytesRam)} (≈ ${fmtBytes(bytesDiscoEst)} txt)`;
    document.getElementById("gen-speed").textContent = `${fmtNum(Math.round(n / Math.max(dt / 1000, 1e-6)))} /s`;

    const muestra = Array.from(arr.slice(0, 30)).map((v, i) => `${String(i + 1).padStart(2, "0")}: ${fmtNum(v)}`).join("   ");
    document.getElementById("gen-preview").textContent = muestra;
    document.getElementById("btn-descargar-datos").disabled = false;

    const chip = document.getElementById("status-chip");
    chip.textContent = `● Datos.txt en memoria · ${fmtNum(n)} núm.`;
    chip.className = "chip chip-ok";
    document.getElementById("home-datos-estado").textContent = `✔ ${fmtNum(n)} datos`;

    registrarMedicion("Generación de Datos.txt", n, dt);
    setProgreso(1, "✔ Datos.txt generado correctamente.");
    logConsola(`✔ Datos.txt generado: ${fmtNum(n)} números en ${fmtTiempo(dt)}.`, "ok");
  } catch (err) {
    logConsola(`✖ Error de memoria al generar: ${err.message}. Probá un tamaño menor.`, "error");
    setProgreso(0, "Error al reservar memoria.");
  } finally {
    btn.disabled = false;
  }
}

// ============================================================================
// CONSIGNAS b, c) MÁXIMO, MÍNIMO Y TOP 10 FRECUENCIAS
// ============================================================================
async function ejecutarAnalizar() {
  if (!requiereDatos()) return;
  const arr = STATE.datos;
  const n = arr.length;
  const k = STATE.rangoMax;
  const btn = document.getElementById("btn-analizar");
  btn.disabled = true;

  logConsola(`Analizando ${fmtNum(n)} datos en un solo recorrido O(n)…`, "titulo");
  setProgreso(0.05, "Recorriendo arreglo y contando frecuencias…");
  await cederHilo();

  try {
    const t0 = performance.now();
    let max = -1;
    let min = k + 1;
    let distintos = 0;
    let top10 = [];

    // Si k <= 25.000.000 o n >= 2.000.000 usamos Uint32Array directo; si no, Map
    const usarTablaDirecta = k <= 25_000_000 || n >= 5_000_000;
    if (usarTablaDirecta) {
      const conteo = new Uint32Array(k + 1);
      const paso = 5_000_000;
      for (let ini = 0; ini < n; ini += paso) {
        const fin = Math.min(ini + paso, n);
        for (let i = ini; i < fin; i++) {
          const v = arr[i];
          if (v > max) max = v;
          if (v < min) min = v;
          conteo[v]++;
        }
        setProgreso((fin / n) * 0.7, `Analizados ${fmtNum(fin)} de ${fmtNum(n)}…`);
        await cederHilo();
      }

      let minTop = 0;
      for (let num = min; num <= max; num++) {
        const c = conteo[num];
        if (c > 0) {
          distintos++;
          if (top10.length < 10) {
            top10.push([num, c]);
            top10.sort((a, b) => b[1] - a[1] || a[0] - b[0]);
            minTop = top10[top10.length - 1][1];
          } else if (c > minTop) {
            top10[9] = [num, c];
            top10.sort((a, b) => b[1] - a[1] || a[0] - b[0]);
            minTop = top10[9][1];
          }
        }
      }
    } else {
      const mapa = new Map();
      for (let i = 0; i < n; i++) {
        const v = arr[i];
        if (v > max) max = v;
        if (v < min) min = v;
        mapa.set(v, (mapa.get(v) || 0) + 1);
      }
      distintos = mapa.size;
      top10 = Array.from(mapa.entries())
        .sort((a, b) => b[1] - a[1] || a[0] - b[0])
        .slice(0, 10);
    }

    const dt = performance.now() - t0;
    document.getElementById("ana-max").textContent = fmtNum(max);
    document.getElementById("ana-min").textContent = fmtNum(min);
    document.getElementById("ana-t").textContent = fmtTiempo(dt);
    document.getElementById("ana-dist").textContent = `${fmtNum(distintos)} (${fmtDec((distintos / n) * 100, 1)} %)`;

    const tbody = document.getElementById("ana-tbody");
    tbody.innerHTML = top10
      .map(([num, ap], idx) => `<tr><td>#${idx + 1}</td><td><strong>${fmtNum(num)}</strong></td><td>${fmtNum(ap)}</td></tr>`)
      .join("");

    const lambda = n / (k + 1);
    const pobEsperada = (k + 1) * (1 - Math.exp(-lambda));
    document.getElementById("poi-lambda").textContent = fmtDec(lambda, 4);
    document.getElementById("poi-teorico").textContent = `≈ ${fmtNum(Math.round(pobEsperada))} valores`;
    document.getElementById("poi-obs").textContent = `${fmtNum(distintos)} valores`;
    document.getElementById("poi-maxf").textContent = top10.length ? `${top10[0][1]} apariciones` : "—";

    registrarMedicion("Máx, mín y frecuencias", n, dt);
    setProgreso(1, "✔ Análisis de máximo, mínimo y frecuencias completado.");
    logConsola(`✔ Mayor: ${fmtNum(max)} · Menor: ${fmtNum(min)} · Distintos: ${fmtNum(distintos)} (${fmtTiempo(dt)}).`, "ok");
  } finally {
    btn.disabled = false;
  }
}

// ============================================================================
// CONSIGNA d) COUNTING SORT
// ============================================================================
async function ejecutarCountingSort() {
  if (!requiereDatos()) return;
  const arr = STATE.datos;
  const n = arr.length;
  const k = STATE.rangoMax;
  const btn = document.getElementById("btn-counting");
  btn.disabled = true;

  logConsola(`Counting Sort sobre ${fmtNum(n)} elementos (k = ${fmtNum(k)})…`, "titulo");
  setProgreso(0.05, "Reservando arreglo de conteo Uint32Array(k + 1)…");
  await cederHilo();

  try {
    const t0 = performance.now();
    const conteo = new Uint32Array(k + 1);
    const salida = new Int32Array(n);

    // Fase 1: conteo
    const paso = 5_000_000;
    for (let ini = 0; ini < n; ini += paso) {
      const fin = Math.min(ini + paso, n);
      for (let i = ini; i < fin; i++) conteo[arr[i]]++;
      setProgreso((fin / n) * 0.5, `Contando frecuencias… ${fmtNum(fin)} / ${fmtNum(n)}`);
      await cederHilo();
    }

    // Fase 2: reconstrucción ordenada
    let pos = 0;
    const pasoK = 10_000_000;
    for (let ini = 0; ini <= k; ini += pasoK) {
      const fin = Math.min(ini + pasoK, k + 1);
      for (let num = ini; num < fin; num++) {
        let c = conteo[num];
        while (c > 0) {
          salida[pos++] = num;
          c--;
        }
      }
      setProgreso(0.5 + (fin / (k + 1)) * 0.5, `Escribiendo salida ordenada…`);
      await cederHilo();
    }

    const dt = performance.now() - t0;
    STATE.salidas.counting = salida;

    document.getElementById("cs-t").textContent = fmtTiempo(dt);
    document.getElementById("cs-n").textContent = fmtNum(n);
    document.getElementById("cs-mem").textContent = fmtBytes(conteo.byteLength);
    document.getElementById("cs-us").textContent = `${fmtDec((dt * 1000) / n, 3)} µs`;

    const primeros = Array.from(salida.slice(0, 15)).map(fmtNum).join(", ");
    const ultimos = Array.from(salida.slice(Math.max(0, n - 15))).map(fmtNum).join(", ");
    document.getElementById("cs-preview").textContent =
      `Primeros 15: [${primeros}]\nÚltimos 15 : [${ultimos}]`;
    document.getElementById("btn-dl-counting").disabled = false;

    registrarMedicion("Counting Sort", n, dt);
    setProgreso(1, "✔ Counting Sort finalizado.");
    logConsola(`✔ Counting Sort ordenó ${fmtNum(n)} datos en ${fmtTiempo(dt)}.`, "ok");
  } catch (err) {
    logConsola(`✖ Error en Counting Sort: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
  }
}

// ============================================================================
// CONSIGNA e) SELECTION SORT
// ============================================================================
async function ejecutarSelectionSort() {
  if (!requiereDatos()) return;
  const limite = Math.min(parseInt(document.getElementById("sel-n").value, 10), STATE.datos.length);
  const btn = document.getElementById("btn-selection");
  btn.disabled = true;

  logConsola(`Selection Sort sobre muestra de ${fmtNum(limite)} elementos (O(n²))…`, "titulo");
  setProgreso(0.02, "Copiando muestra de Datos.txt…");
  await cederHilo();

  try {
    const datos = new Int32Array(STATE.datos.subarray(0, limite));
    const n = datos.length;
    const t0 = performance.now();
    const paso = Math.max(500, Math.floor(n / 30));

    for (let i = 0; i < n - 1; i++) {
      let minIdx = i;
      let minVal = datos[i];
      for (let j = i + 1; j < n; j++) {
        if (datos[j] < minVal) {
          minVal = datos[j];
          minIdx = j;
        }
      }
      if (minIdx !== i) {
        datos[minIdx] = datos[i];
        datos[i] = minVal;
      }
      if (i % paso === 0) {
        setProgreso(i / n, `Selection Sort: posición ${fmtNum(i)} de ${fmtNum(n)}…`);
        await cederHilo();
      }
    }

    const dt = performance.now() - t0;
    STATE.salidas.selection = datos;

    const comparaciones = (n * (n - 1)) / 2;
    const nsPorCmp = (dt * 1e6) / comparaciones;
    const proySeg = (dt / 1000) * Math.pow(100_000_000 / n, 2);

    document.getElementById("sel-t").textContent = fmtTiempo(dt);
    document.getElementById("sel-cmp").textContent = fmtNum(comparaciones);
    document.getElementById("sel-ns").textContent = `${fmtDec(nsPorCmp, 2)} ns`;
    document.getElementById("sel-proy").textContent = fmtDuracionLarga(proySeg);

    const primeros = Array.from(datos.slice(0, 15)).map(fmtNum).join(", ");
    const ultimos = Array.from(datos.slice(Math.max(0, n - 15))).map(fmtNum).join(", ");
    document.getElementById("sel-preview").textContent =
      `Primeros 15: [${primeros}]\nÚltimos 15 : [${ultimos}]\n` +
      `Nota: en Python interpretado (n = 100.000) toma 157,25 s (~5 años para 100 M).`;
    document.getElementById("btn-dl-selection").disabled = false;

    registrarMedicion("Selection Sort", n, dt);
    setProgreso(1, "✔ Selection Sort finalizado.");
    logConsola(`✔ Selection Sort (${fmtNum(n)} datos) en ${fmtTiempo(dt)} · Proyección a 100 M: ${fmtDuracionLarga(proySeg)}.`, "ok");
  } finally {
    btn.disabled = false;
  }
}

// ============================================================================
// CONSIGNA i) ÁRBOL AVL
// ============================================================================
async function construirAVL() {
  if (!requiereDatos()) return;
  const limite = Math.min(parseInt(document.getElementById("avl-n").value, 10), STATE.datos.length);
  const btn = document.getElementById("btn-avl-build");
  btn.disabled = true;

  logConsola(`Construyendo Árbol AVL con ${fmtNum(limite)} elementos…`, "titulo");
  setProgreso(0.05, "Insertando y balanceando nodos…");
  await cederHilo();

  try {
    const avl = new ArbolAVL();
    const t0 = performance.now();
    const paso = 100_000;
    for (let i = 0; i < limite; i++) {
      avl.raiz = avl.insertar(avl.raiz, STATE.datos[i]);
      if (i > 0 && i % paso === 0) {
        setProgreso(i / limite, `Insertados ${fmtNum(i)} de ${fmtNum(limite)} nodos en el AVL…`);
        await cederHilo();
      }
    }
    const dt = performance.now() - t0;
    STATE.avl = avl;

    document.getElementById("avl-t").textContent = fmtTiempo(dt);
    document.getElementById("avl-ops-tbody").innerHTML = "";
    for (const id of ["btn-avl-ins", "btn-avl-bus", "btn-avl-eli", "btn-avl-ver"]) {
      document.getElementById(id).disabled = false;
    }
    refrescarVistaAVL();

    registrarMedicion("Construcción Árbol AVL", avl.totalNodos, dt);
    setProgreso(1, "✔ Árbol AVL construido.");
    logConsola(`✔ AVL construido: ${fmtNum(avl.totalNodos)} nodos, altura ${avl.obtenerAltura(avl.raiz)} (${fmtTiempo(dt)}).`, "ok");
  } finally {
    btn.disabled = false;
  }
}

function refrescarVistaAVL() {
  const avl = STATE.avl;
  if (!avl) return;
  const h = avl.obtenerAltura(avl.raiz);
  const cota = avl.totalNodos > 0 ? 1.44 * Math.log2(avl.totalNodos + 2) : 0;
  document.getElementById("avl-altura").textContent = String(h);
  document.getElementById("avl-nodos").textContent = fmtNum(avl.totalNodos);
  document.getElementById("avl-cota").textContent = `≤ ${fmtDec(cota, 1)}`;

  const muestra = [];
  avl.inOrden(avl.raiz, muestra, 15);
  document.getElementById("avl-inorden").textContent = muestra.length ? `[${muestra.map(fmtNum).join(", ")}]` : "vacío";
  dibujarArbolSVG("avl-svg", () => adaptarNodoAVL(avl, avl.raiz));
}

function logOperacionTabla(tbodyId, op, val, res, ms) {
  const tbody = document.getElementById(tbodyId);
  const tr = document.createElement("tr");
  tr.innerHTML = `<td><strong>${op}</strong></td><td>${val}</td><td>${res}</td><td><code>${fmtTiempo(ms)}</code></td>`;
  tbody.prepend(tr);
}

function leerInputEntero(inputId) {
  const raw = document.getElementById(inputId).value.trim();
  if (raw === "") {
    logConsola("⚠ Ingresá un valor entero en el campo de operación.", "warn");
    return null;
  }
  const v = parseInt(raw, 10);
  if (Number.isNaN(v) || v < 0) {
    logConsola("⚠ El valor debe ser un entero mayor o igual a 0.", "warn");
    return null;
  }
  return v;
}

function operarAVL(accion) {
  const avl = STATE.avl;
  if (!avl) return;

  if (accion === "verificar") {
    const t0 = performance.now();
    const ok = avl.esValidoAVL();
    const dt = performance.now() - t0;
    const msg = ok ? "✔ VÁLIDO (ABB + factor de balance ∈ {-1, 0, 1})" : "✖ INVÁLIDO";
    logOperacionTabla("avl-ops-tbody", "Verificar AVL", "—", msg, dt);
    logConsola(`AVL · Verificación de invariante: ${msg} (${fmtTiempo(dt)}).`, ok ? "ok" : "error");
    return;
  }

  const v = leerInputEntero("avl-input");
  if (v === null) return;

  if (accion === "insertar") {
    const t0 = performance.now();
    avl.raiz = avl.insertar(avl.raiz, v);
    const dt = performance.now() - t0;
    refrescarVistaAVL();
    logOperacionTabla("avl-ops-tbody", "Inserción", fmtNum(v), `Insertado · Nodos: ${fmtNum(avl.totalNodos)} · Alt: ${avl.obtenerAltura(avl.raiz)}`, dt);
    logConsola(`AVL · Insertado ${fmtNum(v)} en ${fmtTiempo(dt)}.`, "ok");
  } else if (accion === "buscar") {
    const t0 = performance.now();
    const nodo = avl.buscar(avl.raiz, v);
    const dt = performance.now() - t0;
    const res = nodo ? "✔ ENCONTRADO" : "✖ NO ENCONTRADO";
    logOperacionTabla("avl-ops-tbody", "Búsqueda O(log n)", fmtNum(v), res, dt);
    logConsola(`AVL · Búsqueda de ${fmtNum(v)}: ${res} (${fmtTiempo(dt)}).`, nodo ? "ok" : "warn");
  } else if (accion === "eliminar") {
    const antes = avl.totalNodos;
    const t0 = performance.now();
    avl.raiz = avl.eliminar(avl.raiz, v);
    const dt = performance.now() - t0;
    const eliminado = avl.totalNodos < antes;
    refrescarVistaAVL();
    const res = eliminado ? `✔ ELIMINADO · Nodos: ${fmtNum(avl.totalNodos)}` : "✖ NO ENCONTRADO (sin cambios)";
    logOperacionTabla("avl-ops-tbody", "Eliminación O(log n)", fmtNum(v), res, dt);
    logConsola(`AVL · Eliminación de ${fmtNum(v)}: ${res} (${fmtTiempo(dt)}).`, eliminado ? "ok" : "warn");
  }
}

// ============================================================================
// CONSIGNA j) HEAP BINARIO (MAX HEAP Y MIN HEAP)
// ============================================================================
async function construirHeap() {
  if (!requiereDatos()) return;
  const tipo = document.getElementById("heap-tipo").value;
  const limite = Math.min(parseInt(document.getElementById("heap-n").value, 10), STATE.datos.length);
  const btn = document.getElementById("btn-heap-build");
  btn.disabled = true;

  const nombre = tipo === "max" ? "Max Heap" : "Min Heap";
  logConsola(`Construyendo ${nombre} con ${fmtNum(limite)} elementos…`, "titulo");
  setProgreso(0.05, `Insertando elementos en el ${nombre}…`);
  await cederHilo();

  try {
    const h = new HeapBinario(tipo);
    const t0 = performance.now();
    const paso = 1_000_000;
    for (let i = 0; i < limite; i++) {
      h.insertar(STATE.datos[i]);
      if (i > 0 && i % paso === 0) {
        setProgreso(i / limite, `Insertados ${fmtNum(i)} de ${fmtNum(limite)} en ${nombre}…`);
        await cederHilo();
      }
    }
    const dt = performance.now() - t0;
    STATE.heap = h;

    document.getElementById("heap-t").textContent = fmtTiempo(dt);
    document.getElementById("heap-ops-tbody").innerHTML = "";
    for (const id of ["btn-heap-ins", "btn-heap-bus", "btn-heap-ext", "btn-heap-ver"]) {
      document.getElementById(id).disabled = false;
    }
    refrescarVistaHeap();

    registrarMedicion(`Construcción ${nombre}`, h.heap.length, dt);
    setProgreso(1, `✔ ${nombre} construido.`);
    logConsola(`✔ ${nombre} construido con ${fmtNum(h.heap.length)} elementos en ${fmtTiempo(dt)}.`, "ok");
  } finally {
    btn.disabled = false;
  }
}

function refrescarVistaHeap() {
  const h = STATE.heap;
  if (!h) return;
  const rol = h.esMax ? "Máximo" : "Mínimo";
  document.getElementById("heap-root-label").textContent = `Elemento raíz (${rol})`;
  document.getElementById("btn-heap-ext").textContent = h.esMax ? "⬆ Eliminar Máximo (Raíz)" : "⬇ Eliminar Mínimo (Raíz)";
  document.getElementById("heap-count").textContent = fmtNum(h.heap.length);
  document.getElementById("heap-root").textContent = h.heap.length ? fmtNum(h.heap[0]) : "Vacío";
  document.getElementById("heap-height").textContent = h.heap.length
    ? `${h.alturaAristas()} aristas (${h.alturaNiveles()} niv.)`
    : "0";
  dibujarArbolSVG("heap-svg", () => adaptarNodoHeap(h, 0));
}

function operarHeap(accion) {
  const h = STATE.heap;
  if (!h) return;
  const rol = h.esMax ? "Máximo" : "Mínimo";

  if (accion === "verificar") {
    const t0 = performance.now();
    const ok = h.esValidoHeap();
    const dt = performance.now() - t0;
    const msg = ok ? `✔ VÁLIDO (propiedad de ${h.esMax ? "Max Heap" : "Min Heap"})` : "✖ INVÁLIDO";
    logOperacionTabla("heap-ops-tbody", "Verificar Heap", "—", msg, dt);
    logConsola(`Heap · Verificación: ${msg} (${fmtTiempo(dt)}).`, ok ? "ok" : "error");
    return;
  }

  if (accion === "extraer") {
    const t0 = performance.now();
    const ext = h.extraerRaiz();
    const dt = performance.now() - t0;
    refrescarVistaHeap();
    const nueva = h.heap.length ? fmtNum(h.heap[0]) : "Vacío";
    logOperacionTabla("heap-ops-tbody", `Eliminar ${rol}`, ext !== null ? fmtNum(ext) : "—", `Nueva raíz: ${nueva}`, dt);
    logConsola(`Heap · ${rol} eliminado: ${ext !== null ? fmtNum(ext) : "—"} (${fmtTiempo(dt)}).`, "ok");
    return;
  }

  const v = leerInputEntero("heap-input");
  if (v === null) return;

  if (accion === "insertar") {
    const t0 = performance.now();
    h.insertar(v);
    const dt = performance.now() - t0;
    refrescarVistaHeap();
    logOperacionTabla("heap-ops-tbody", "Inserción O(log n)", fmtNum(v), `Raíz actual: ${fmtNum(h.heap[0])}`, dt);
    logConsola(`Heap · Insertado ${fmtNum(v)} en ${fmtTiempo(dt)}.`, "ok");
  } else if (accion === "buscar") {
    const t0 = performance.now();
    const idx = h.buscar(v);
    const dt = performance.now() - t0;
    const res = idx !== -1 ? `✔ Encontrado en índice ${fmtNum(idx)}` : `✖ No encontrado (recorrió ${fmtNum(h.heap.length)} celdas)`;
    logOperacionTabla("heap-ops-tbody", "Búsqueda O(n)", fmtNum(v), res, dt);
    logConsola(`Heap · Búsqueda lineal O(n) de ${fmtNum(v)}: ${res} (${fmtTiempo(dt)}).`, idx !== -1 ? "ok" : "warn");
  }
}

// ============================================================================
// CONSIGNA k) HEAP SORT (ITERATIVO IN-PLACE + VERIFICACIÓN AUTOMÁTICA)
// ============================================================================
function heapifyIterativo(arr, tam, i) {
  while (true) {
    let mayor = i;
    const izq = (i << 1) + 1;
    const der = izq + 1;
    if (izq < tam && arr[izq] > arr[mayor]) mayor = izq;
    if (der < tam && arr[der] > arr[mayor]) mayor = der;
    if (mayor !== i) {
      const tmp = arr[i];
      arr[i] = arr[mayor];
      arr[mayor] = tmp;
      i = mayor;
    } else {
      break;
    }
  }
}

async function ejecutarHeapSort() {
  if (!requiereDatos()) return;
  const limite = Math.min(parseInt(document.getElementById("hs-n").value, 10), STATE.datos.length);
  const btn = document.getElementById("btn-heapsort");
  btn.disabled = true;

  logConsola(`Heap Sort in-place sobre ${fmtNum(limite)} elementos…`, "titulo");
  setProgreso(0.05, "Copiando muestra de Datos.txt…");
  await cederHilo();

  try {
    const datos = new Int32Array(STATE.datos.subarray(0, limite));
    const n = datos.length;
    const t0 = performance.now();

    // Fase 1: Build-Max-Heap bottom-up O(n)
    const paso = 500_000;
    for (let i = (n >> 1) - 1; i >= 0; i--) {
      heapifyIterativo(datos, n, i);
      if (i % paso === 0) {
        setProgreso(0.05 + 0.15 * (1 - i / Math.max(1, n >> 1)), "Fase 1: Construyendo Max Heap bottom-up O(n)…");
        await cederHilo();
      }
    }

    // Fase 2: Extracción repetida de la raíz O(n log n)
    for (let i = n - 1; i > 0; i--) {
      const tmp = datos[0];
      datos[0] = datos[i];
      datos[i] = tmp;
      heapifyIterativo(datos, i, 0);
      if (i % paso === 0) {
        setProgreso(0.2 + 0.75 * (1 - i / n), `Fase 2: Extrayendo máximos… restan ${fmtNum(i)}`);
        await cederHilo();
      }
    }

    const dt = performance.now() - t0;
    STATE.salidas.heapsort = datos;

    // Verificación automática (Consigna k)
    let ordenado = true;
    for (let i = 0; i < n - 1; i++) {
      if (datos[i] > datos[i + 1]) {
        ordenado = false;
        break;
      }
    }

    const proySeg = (dt / 1000) * ((1e8 * Math.log2(1e8)) / (n * Math.log2(Math.max(n, 2))));
    document.getElementById("hs-t").textContent = fmtTiempo(dt);
    document.getElementById("hs-verif").textContent = ordenado ? "✔ ORDENADO" : "✖ ERROR";
    document.getElementById("hs-us").textContent = `${fmtDec((dt * 1000) / n, 3)} µs`;
    document.getElementById("hs-proy").textContent = fmtDuracionLarga(proySeg);

    const primeros = Array.from(datos.slice(0, 15)).map(fmtNum).join(", ");
    const ultimos = Array.from(datos.slice(Math.max(0, n - 15))).map(fmtNum).join(", ");
    document.getElementById("hs-preview").textContent =
      `Primeros 15: [${primeros}]\nÚltimos 15 : [${ultimos}]\n` +
      `Verificación Datos_HeapSort.txt: ${ordenado ? "✔ ORDENADO ASCENDENTE" : "✖ NO ORDENADO"}`;
    document.getElementById("btn-dl-heapsort").disabled = false;

    registrarMedicion("Heap Sort", n, dt);
    setProgreso(1, "✔ Heap Sort finalizado y verificado.");
    logConsola(`✔ Heap Sort (${fmtNum(n)} datos) en ${fmtTiempo(dt)} · Verificación: ${ordenado ? "ORDENADO" : "ERROR"}.`, "ok");
  } finally {
    btn.disabled = false;
  }
}

// ============================================================================
// CONSIGNA f) VERIFICACIÓN DE ORDENAMIENTO
// ============================================================================
function verificarArreglo(arr) {
  if (!arr || arr.length === 0) return { existe: false };
  const t0 = performance.now();
  let ordenado = true;
  let falloIdx = -1;
  for (let i = 0; i < arr.length - 1; i++) {
    if (arr[i] > arr[i + 1]) {
      ordenado = false;
      falloIdx = i;
      break;
    }
  }
  const dt = performance.now() - t0;
  return {
    existe: true,
    n: arr.length,
    min: arr[0],
    max: arr[arr.length - 1],
    ordenado,
    falloIdx,
    dt
  };
}

function ejecutarVerificar(incluirSimulacionFallo = false) {
  const defs = [
    { archivo: "Datos_CountingSort.txt", alg: "Counting Sort (d)", arr: STATE.salidas.counting },
    { archivo: "Datos_SelectionSort.txt", alg: "Selection Sort (e)", arr: STATE.salidas.selection },
    { archivo: "Datos_HeapSort.txt", alg: "Heap Sort (k)", arr: STATE.salidas.heapsort }
  ];

  if (incluirSimulacionFallo) {
    defs.push({
      archivo: "Prueba_Desordenado.txt",
      alg: "Simulación con inversión",
      arr: new Int32Array([10, 25, 40, 99, 12, 150])
    });
  }

  const tbody = document.getElementById("ver-tbody");
  tbody.innerHTML = "";

  for (const d of defs) {
    const r = verificarArreglo(d.arr);
    const tr = document.createElement("tr");
    if (!r.existe) {
      tr.innerHTML = `<td><code>${d.archivo}</code></td><td>${d.alg}</td><td>—</td><td>—</td>
        <td><span class="badge badge-yellow">No generado aún</span></td><td>—</td>`;
    } else {
      const badge = r.ordenado
        ? `<span class="badge badge-green">✔ ORDENADO</span>`
        : `<span class="badge badge-red">✖ NO ORDENADO (índice ${r.falloIdx})</span>`;
      tr.innerHTML = `<td><code>${d.archivo}</code></td><td>${d.alg}</td><td>${fmtNum(r.n)}</td>
        <td>[${fmtNum(r.min)} .. ${fmtNum(r.max)}]</td><td>${badge}</td><td><code>${fmtTiempo(r.dt)}</code></td>`;
      logConsola(`Verificación de ${d.archivo}: ${r.ordenado ? "ORDENADO" : "ERROR: NO ORDENADO"} (${fmtTiempo(r.dt)}).`, r.ordenado ? "ok" : "error");
    }
    tbody.appendChild(tr);
  }
  setProgreso(1, "✔ Verificación de archivos completada.");
}

// ============================================================================
// CONSIGNAS g, l) COMPARATIVA, GRÁFICO Y EXPORTACIÓN CSV
// ============================================================================
function colorOperacion(op) {
  if (op.includes("Counting")) return "#3fb950";
  if (op.includes("Selection")) return "#f85149";
  if (op.includes("Heap Sort")) return "#1f6feb";
  if (op.includes("AVL")) return "#d29922";
  if (op.includes("Heap")) return "#a371f7";
  return "#58a6ff";
}

function refrescarComparativa() {
  const cont = document.getElementById("chart-container");
  const tbody = document.getElementById("hist-tbody");
  const logScale = document.getElementById("chk-log-scale").checked;

  if (STATE.historial.length === 0) {
    cont.innerHTML = `<p class="muted">Todavía no hay mediciones en la sesión. Ejecutá alguna opción o presioná "📥 Cargar mediciones de 100 M del Informe".</p>`;
    tbody.innerHTML = `<tr><td colspan="5" class="muted">Sin registros.</td></tr>`;
    return;
  }

  const transformar = (ms) => (logScale ? Math.log10(ms + 1) : ms);
  const maxVal = Math.max(...STATE.historial.map((r) => transformar(r.ms)), 1e-6);

  cont.innerHTML = STATE.historial
    .slice(-10)
    .map((r) => {
      const pct = Math.max(2, Math.round((transformar(r.ms) / maxVal) * 100));
      return `
        <div class="chart-row">
          <div class="chart-label" title="${r.op} (n=${fmtNum(r.n)})">${r.op} · <span class="muted">${fmtNum(r.n)}</span></div>
          <div class="chart-bar-wrap"><div class="chart-bar" style="width:${pct}%; background:${colorOperacion(r.op)}"></div></div>
          <div class="chart-val">${fmtTiempo(r.ms)}</div>
        </div>`;
    })
    .join("");

  tbody.innerHTML = STATE.historial
    .slice()
    .reverse()
    .map((r) => {
      const usElem = r.n > 0 ? fmtDec((r.ms * 1000) / r.n, 3) : "—";
      return `<tr><td><strong>${r.op}</strong></td><td>${fmtNum(r.n)}</td><td><code>${fmtTiempo(r.ms)}</code></td><td>${usElem} µs</td><td class="muted">${r.hora}</td></tr>`;
    })
    .join("");
}

function cargarMedicionesInforme100M() {
  const oficiales = [
    { op: "Generación de Datos.txt", n: 100_000_000, ms: 36_770 },
    { op: "Máx, mín y frecuencias", n: 100_000_000, ms: 67_840 },
    { op: "Counting Sort", n: 100_000_000, ms: 71_030 },
    { op: "Selection Sort", n: 100_000, ms: 157_250 },
    { op: "Heap Sort (1 M)", n: 1_000_000, ms: 5_170 },
    { op: "Heap Sort (10 M)", n: 10_000_000, ms: 58_360 },
    { op: "Construcción Árbol AVL", n: 1_000_000, ms: 9_840 },
    { op: "Construcción Max Heap", n: 10_000_000, ms: 7_700 }
  ];
  for (const item of oficiales) {
    STATE.historial.push({ ...item, hora: "Informe Python (Ryzen 5)" });
  }
  refrescarComparativa();
  mostrarPanel("comparativa");
  logConsola("✔ Se cargaron las mediciones reales sobre 100.000.000 de datos del informe.", "ok");
}

function exportarCSV() {
  if (STATE.historial.length === 0) {
    logConsola("⚠ No hay mediciones para exportar.", "warn");
    return;
  }
  const filas = ["operacion;n;milisegundos;microsegundos_por_elemento;origen"];
  for (const r of STATE.historial) {
    const us = r.n ? ((r.ms * 1000) / r.n).toFixed(4).replace(".", ",") : "";
    filas.push(`${r.op};${r.n};${r.ms.toFixed(3).replace(".", ",")};${us};${r.hora}`);
  }
  const blob = new Blob(["\uFEFF" + filas.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "resultados_tp3.csv";
  a.click();
  URL.revokeObjectURL(url);
  logConsola("✔ Exportado archivo resultados_tp3.csv.", "ok");
}

// ============================================================================
// NAVEGACIÓN Y EVENTOS
// ============================================================================
function mostrarPanel(clave) {
  document.querySelectorAll(".nav-item").forEach((b) => {
    b.classList.toggle("active", b.dataset.panel === clave);
  });
  document.querySelectorAll(".panel").forEach((p) => {
    p.classList.toggle("active", p.id === `panel-${clave}`);
  });
  if (clave === "comparativa") refrescarComparativa();
}

window.addEventListener("DOMContentLoaded", () => {
  // Navegación lateral y tarjetas de inicio
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => mostrarPanel(btn.dataset.panel));
  });
  document.querySelectorAll(".step-item").forEach((item) => {
    item.addEventListener("click", () => mostrarPanel(item.dataset.goto));
  });

  // Botones por consigna
  document.getElementById("btn-generar").addEventListener("click", ejecutarGenerar);
  document.getElementById("btn-descargar-datos").addEventListener("click", () =>
    descargarArchivoTexto("Datos.txt", STATE.datos)
  );
  document.getElementById("btn-analizar").addEventListener("click", ejecutarAnalizar);
  document.getElementById("btn-counting").addEventListener("click", ejecutarCountingSort);
  document.getElementById("btn-dl-counting").addEventListener("click", () =>
    descargarArchivoTexto("Datos_CountingSort.txt", STATE.salidas.counting)
  );
  document.getElementById("btn-selection").addEventListener("click", ejecutarSelectionSort);
  document.getElementById("btn-dl-selection").addEventListener("click", () =>
    descargarArchivoTexto("Datos_SelectionSort.txt", STATE.salidas.selection)
  );

  // AVL
  document.getElementById("btn-avl-build").addEventListener("click", construirAVL);
  document.getElementById("btn-avl-ins").addEventListener("click", () => operarAVL("insertar"));
  document.getElementById("btn-avl-bus").addEventListener("click", () => operarAVL("buscar"));
  document.getElementById("btn-avl-eli").addEventListener("click", () => operarAVL("eliminar"));
  document.getElementById("btn-avl-ver").addEventListener("click", () => operarAVL("verificar"));

  // Heap (Max / Min)
  document.getElementById("btn-heap-build").addEventListener("click", construirHeap);
  document.getElementById("btn-heap-ins").addEventListener("click", () => operarHeap("insertar"));
  document.getElementById("btn-heap-bus").addEventListener("click", () => operarHeap("buscar"));
  document.getElementById("btn-heap-ext").addEventListener("click", () => operarHeap("extraer"));
  document.getElementById("btn-heap-ver").addEventListener("click", () => operarHeap("verificar"));

  // Heap Sort & Verificación
  document.getElementById("btn-heapsort").addEventListener("click", ejecutarHeapSort);
  document.getElementById("btn-dl-heapsort").addEventListener("click", () =>
    descargarArchivoTexto("Datos_HeapSort.txt", STATE.salidas.heapsort)
  );
  document.getElementById("btn-verificar-todos").addEventListener("click", () => ejecutarVerificar(false));
  document.getElementById("btn-simular-fallo").addEventListener("click", () => ejecutarVerificar(true));

  // Comparativa
  document.getElementById("btn-cargar-100m").addEventListener("click", cargarMedicionesInforme100M);
  document.getElementById("btn-cargar-benchmark-home").addEventListener("click", cargarMedicionesInforme100M);
  document.getElementById("btn-exportar-csv").addEventListener("click", exportarCSV);
  document.getElementById("btn-limpiar-hist").addEventListener("click", () => {
    STATE.historial = [];
    refrescarComparativa();
  });
  document.getElementById("chk-log-scale").addEventListener("change", refrescarComparativa);

  dibujarArbolSVG("avl-svg", () => null);
  dibujarArbolSVG("heap-svg", () => null);
  refrescarComparativa();
  logConsola("Aplicación web inicializada. Podés generar datos en vivo o cargar las mediciones de 100 M del informe.", "info");
});
