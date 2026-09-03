# Mi DOE Lab — ensambla tu programa

Durante ocho sesiones construiste, script por script, las herramientas de un
analista de experimentos: ANOVA, factorial completo, fraccionado y bloques.
Hoy las unes en **un programa con interfaz web**, con un asistente de IA que
conoce **tus** resultados. Las piezas ya las tienes: hoy toca el ensamble.

## El mapa del kit

```
mi-doe-lab/
├── app.py          el chasis: el servidor web que une todo (NO se edita hoy)
├── registro.py     ★ AQUÍ ENSAMBLAS: conecta cada pieza
├── piezas/         tus scripts del curso, uno por sesión
│   ├── anova.py        S2-S3   ¿hay diferencia entre grupos?
│   ├── factorial.py    S5      efectos e interacciones de un 2^k
│   ├── fraccionado.py  S6      generadores, alias y resolución
│   ├── bloques.py      S7      el bloque separado del error
│   ├── asistente.py    S8      el chatbot que lee tus resultados
│   └── formato.py      S8      el inspector: revisa tu CSV antes de correr
├── datos/          los CSV del curso (y los que tú subas)
├── templates/ y static/   la interfaz web
└── requirements.txt
```

## Paso 0 — arranca el motor

En la Shell de Replit:

```
pip install -r requirements.txt
python app.py
```

Replit abre la vista web. Vas a ver **1 pieza conectada de 4** (el ANOVA ya
viene puesto, para que veas el patrón) y tres espacios libres.

## Paso 1 — prueba la pieza que ya está

En la tarjeta **ANOVA de un factor**, deja `catalizadores.csv` y presiona
**Correr análisis**. Lo que aparece en el panel de resultado es lo mismo que
imprimía tu script en la Shell: el programa lo corre por ti.

## Pasos 2, 3 y 4 — conecta tus piezas

Abre `registro.py`. Cada pieza es un bloque comentado con huecos `____`:

1. Quita los `#` del bloque de la pieza.
2. Completa los huecos: qué script es, con qué CSV de `datos/` trabaja y
   **qué pregunta contesta ese análisis, con tus palabras** (revisa el
   encabezado del script si dudas).
3. Guarda y **recarga la página** del navegador. La tarjeta aparece.
4. Córrela con su CSV para verificar que quedó bien conectada.

Orden sugerido: **factorial** (S5) → **fraccionado** (S6) → **bloques** (S7).
Pista: `fraccionado.py` y `bloques.py` aceptan argumentos extra (por ejemplo
`A:C`), igual que cuando los corrías a mano.

## Paso 5 — bautiza tu programa

En `registro.py`, cambia `NOMBRE_DEL_PROGRAMA`. Ya no es "el script de la
clase": es tu software, ponle nombre.

## Paso 6 — enciende el asistente

1. En Replit, abre **Secrets** (el candado de la barra izquierda).
2. Agrega la llave: nombre `MINIMAX_API_KEY`, valor el que te da el profesor.
   **Nunca la pegues en el código.**
3. En `registro.py`, pon `ASISTENTE_CONECTADO = True`. Recarga.

Corre un análisis y pregúntale algo sobre **ese** resultado: el asistente
recibe la salida de tu último análisis antes de contestar.

## Paso 7 — el estreno

Analiza `sintesis_nanoparticulas.csv` **con tu programa**: decide qué pieza
le toca, córrela, lee el resultado y discútelo con tu asistente.

El caso: síntesis de nanopartículas de plata; el laboratorio quiere el
tamaño de partícula (nm) **más chico** posible. Los factores, en codificado:

| Columna | Factor | Nivel − | Nivel + |
|---|---|---|---|
| A | temperatura de síntesis | 25 °C | 60 °C |
| B | agente reductor | citrato | borohidruro |
| C | velocidad de agitación | 300 rpm | 900 rpm |
| bloque | lote de precursor | lote1 | lote2 |

Cada lote corrió una réplica completa del 2³, en orden aleatorio.

## Si algo truena

| Síntoma | Causa típica |
|---|---|
| La página da error al recargar | Falta una coma o una comilla en `registro.py` (revisa la Shell) |
| La tarjeta sale naranja | Quedó un hueco `____` sin completar, o la ruta del script/CSV está mal escrita |
| El chat dice que no encuentra la llave | El Secret no se llama exactamente `MINIMAX_API_KEY`, o falta reiniciar `python app.py` |
| El resultado dice "EL FORMATO ... NO SIRVE" | No es una falla: el inspector (`piezas/formato.py`) revisó tu CSV antes de correr y te está diciendo qué arreglar. Cada tarjeta trae su ficha "formato de datos" con un ejemplo |
| El análisis marca error | Corre el script a mano en la Shell (`python piezas/xxx.py datos/yyy.csv`) y lee el mensaje completo |
