# ============================================================
# Q2003B - Diseno de Experimentos
# Sesion 7: analisis de un factorial 2^k corrido en bloques
#
# Uso desde la Shell de Replit:
#   python bloques.py catalisis_bloques.csv
#   python bloques.py catalisis_bloques.csv B:C      (solo esa interaccion)
#   python bloques.py esmalte_confundido.csv ninguna (solo efectos principales)
#
# Corre en el mismo Repl de la S4/S5/S6: su requirements.txt ya trae
# pandas, matplotlib y statsmodels, que es todo lo que este script pide.
#
# El CSV lleva una columna por factor (dos niveles cada uno; pueden venir
# como -1/1 o con sus nombres reales), una columna llamada 'bloque' con la
# etiqueta del bloque (dia1/dia2, lote1/lote2, horno1/horno2...) y una
# columna llamada 'respuesta'. Si ademas trae una columna 'corrida' con el
# orden en que se corrio el experimento, el script la ignora en las cuentas:
# esta ahi para que se vea que el orden dentro de cada bloque fue al azar.
#
# Que hace, en orden:
#   1. EL DISENO: cuantos factores, cuantas corridas, cuantos bloques y
#      cuantas corridas por bloque. Si cada bloque contiene una replica
#      completa del 2^k lo dice, y entonces no se sacrifica ningun efecto.
#      Si cada bloque trae solo una parte, busca que interaccion comparte
#      columna con el bloque (el producto de signos que no cambia dentro de
#      un bloque, el mismo truco con el que fraccionado.py encontraba el
#      generador) y avisa que ese efecto quedo confundido con la diferencia
#      entre bloques.
#   2. EFECTOS: promedio en + menos promedio en -, para cada factor, cada
#      par y el bloque, ordenados de mayor a menor, y un diagrama de Pareto
#      (efectos_pareto.png) con la barra del bloque marcada aparte.
#   3. TABLA ANOVA CON BLOQUE: el bloque entra al modelo como un termino
#      mas y su fila se imprime primero. Si algun efecto quedo confundido
#      con el bloque, no entra al modelo y el script lo dice.
#   4. Y SI NO HUBIERAS BLOQUEADO: el mismo modelo sin el bloque, con las
#      dos filas de residuales lado a lado y el valor p de cada termino en
#      los dos modelos. Esta es la comparacion de la sesion: la variacion
#      del dia (o del lote, o del horno) se va completa al error si no la
#      sacas del error, y ahi se pierden los efectos que si eran reales.
#   5. Un interaction plot por cada interaccion del modelo, y
#      bloques_medias.png con el promedio de la respuesta en cada bloque.
#
# Nota de sintaxis: el bloque entra a la formula como la columna 'bloque',
# que es texto, y por eso statsmodels la trata como categoria sin que haya
# que escribir C(bloque). Ademas no se puede escribir C(bloque) cuando uno
# de los factores se llama C, porque la columna le gana el nombre.
# ============================================================

import sys
from itertools import combinations
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Replit no tiene pantalla: las graficas se guardan como PNG
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols

datos = pd.read_csv(sys.argv[1])
if 'bloque' not in datos.columns:
    raise SystemExit('El CSV no tiene columna "bloque". Este script es para disenos en bloques; '
                     'para uno sin bloques usa factorial.py o fraccionado.py.')
if 'respuesta' not in datos.columns:
    raise SystemExit('El CSV no tiene columna "respuesta".')

factores = [col for col in datos.columns if col not in ('respuesta', 'bloque', 'corrida')]
for f in factores:  # codificar cada factor: nivel bajo = -1, nivel alto = +1
    bajo, alto = sorted(datos[f].unique())
    datos[f] = datos[f].map({bajo: -1, alto: 1})
datos['bloque'] = datos['bloque'].astype(str)
etiquetas = sorted(datos['bloque'].unique())


def normaliza(termino):  # acepta a:c, A:C o el nombre real del factor
    partes = []
    for p in termino.split(':'):
        iguales = [f for f in factores if f.lower() == p.strip().lower()]
        partes.append(iguales[0] if iguales else p.strip())
    return ':'.join(partes)


pedidas = [a for a in sys.argv[2:]]
sin_interacciones = any(a.lower() == 'ninguna' for a in pedidas)
interacciones = [normaliza(a) for a in pedidas if a.lower() != 'ninguna']

# ---------- 1. El diseno: bloques completos o efecto confundido ----------
print('EL DISENO')
k, n, nb = len(factores), len(datos), len(etiquetas)
print('%d factores en %d corridas, repartidas en %d bloques (%s)'
      % (k, n, nb, ', '.join(etiquetas)))
for b in etiquetas:
    print('  bloque %-10s %d corridas' % (b, (datos['bloque'] == b).sum()))

combinaciones_totales = 2 ** k
completo = all(datos.loc[datos['bloque'] == b, factores].drop_duplicates().shape[0]
               == combinaciones_totales for b in etiquetas)
confundidos = []
if completo:
    replicas = (datos['bloque'] == etiquetas[0]).sum() // combinaciones_totales
    print('Cada bloque trae las %d combinaciones del 2^%d (%s por bloque).'
          % (combinaciones_totales, k,
             '1 replica' if replicas == 1 else '%d replicas' % replicas))
    print('Cada bloque es una replica completa del factorial: no se sacrifica ningun efecto.')
else:
    for tam in range(2, k + 1):  # que producto de signos no cambia dentro de un bloque
        for grupo in combinations(factores, tam):
            producto = datos[list(grupo)].prod(axis=1)
            if all(producto[datos['bloque'] == b].nunique() == 1 for b in etiquetas):
                confundidos.append(''.join(grupo))
    if confundidos:
        for palabra in confundidos:
            print('El bloque comparte columna con %s: ese efecto queda confundido '
                  'con la diferencia entre bloques' % palabra)
        print('Se pago ese efecto para poder partir el experimento: es el precio del bloque.')
    else:
        print('Los bloques no traen replicas completas y ningun producto de signos coincide '
              'con ellos: el diseno esta desbalanceado y las cuentas de abajo hay que leerlas '
              'con cuidado.')

# ---------- 2. Efectos y Pareto ----------
print('\nEFECTOS (promedio en + menos promedio en -)')
efectos = {}
for f in factores:
    efectos[f] = (datos.loc[datos[f] == 1, 'respuesta'].mean()
                  - datos.loc[datos[f] == -1, 'respuesta'].mean())
for a, b in combinations(factores, 2):
    col = datos[a] * datos[b]
    efectos[a + ':' + b] = (datos.loc[col == 1, 'respuesta'].mean()
                            - datos.loc[col == -1, 'respuesta'].mean())
if nb == 2:
    efectos['bloque'] = (datos.loc[datos['bloque'] == etiquetas[1], 'respuesta'].mean()
                         - datos.loc[datos['bloque'] == etiquetas[0], 'respuesta'].mean())
    print('  (el efecto del bloque es el promedio de %s menos el de %s)'
          % (etiquetas[1], etiquetas[0]))
orden = sorted(efectos, key=lambda e: -abs(efectos[e]))
for e in orden:
    print('  %-8s %9.4f' % (e, efectos[e]))
plt.figure(figsize=(7, 4))
colores = ['#f97316' if e == 'bloque' else '#2563eb' for e in orden[::-1]]
plt.barh(orden[::-1], [abs(efectos[e]) for e in orden[::-1]], color=colores)
plt.xlabel('|efecto|')
plt.title('Pareto de efectos (el bloque, en naranja)')
plt.savefig('efectos_pareto.png', dpi=120, bbox_inches='tight')
print('grafica guardada: efectos_pareto.png')

print('\nPROMEDIO DE LA RESPUESTA EN CADA BLOQUE')
medias_bloque = datos.groupby('bloque')['respuesta'].agg(['count', 'mean'])
for b in etiquetas:
    print('  %-10s n = %2d   promedio = %9.4f'
          % (b, medias_bloque.loc[b, 'count'], medias_bloque.loc[b, 'mean']))
print('  %-10s n = %2d   promedio = %9.4f' % ('global', n, datos['respuesta'].mean()))

# ---------- 3. Tabla ANOVA con el bloque adentro ----------
pares = ['%s:%s' % par for par in combinations(factores, 2)]
if sin_interacciones:
    usar = []
elif interacciones:
    usar = list(interacciones)
else:
    usar = list(pares)
fuera = [t for t in usar
         if any(set(t.replace(':', '')) == set(w) for w in confundidos)]
usar = [t for t in usar if t not in fuera]
terminos = list(factores) + usar

print('\nTABLA ANOVA CON BLOQUE')
for t in fuera:
    print('%s no entra al modelo: comparte columna con el bloque y no se puede separar de el.' % t)
for palabra in confundidos:
    if not any(set(palabra) == set(t.replace(':', '')) for t in pares):
        print('%s no se puede estimar por separado: es la interaccion que se confundio '
              'con el bloque.' % palabra)
formula_con = 'respuesta ~ bloque + ' + ' + '.join(terminos)
print('modelo: ' + formula_con)
modelo_con = ols(formula_con, data=datos).fit()
if modelo_con.df_resid < 1:
    print('AVISO: con el bloque adentro no quedan grados de libertad para el error, y sin error')
    print('no hay F ni p. Vuelve a correr eligiendo solo las interacciones que el Pareto senala,')
    print('por ejemplo:  python bloques.py %s %s' % (sys.argv[1], pares[0]))
    print('o sin ninguna:  python bloques.py %s ninguna' % sys.argv[1])
    tabla_con = None
else:
    tabla_con = sm.stats.anova_lm(modelo_con, typ=2)
    tabla_con = tabla_con.reindex(['bloque'] + [i for i in tabla_con.index if i != 'bloque'])
    print(tabla_con.to_string(float_format=lambda x: '%.6g' % x))
    print('R2 = %.4f' % modelo_con.rsquared)

# ---------- 4. Y si no hubieras bloqueado ----------
print('\nY SI NO HUBIERAS BLOQUEADO')
formula_sin = 'respuesta ~ ' + ' + '.join(terminos)
print('modelo: ' + formula_sin)
modelo_sin = ols(formula_sin, data=datos).fit()
if tabla_con is None or modelo_sin.df_resid < 1:
    print('No se puede comparar: uno de los dos modelos se quedo sin grados de libertad para el error.')
else:
    tabla_sin = sm.stats.anova_lm(modelo_sin, typ=2)
    gl_con, sc_con = modelo_con.df_resid, tabla_con.loc['Residual', 'sum_sq']
    gl_sin, sc_sin = modelo_sin.df_resid, tabla_sin.loc['Residual', 'sum_sq']
    cm_con, cm_sin = sc_con / gl_con, sc_sin / gl_sin
    print('\nLa fila de residuales de los dos modelos:')
    print('  %-14s %6s %12s %12s' % ('', 'gl', 'SC', 'CM'))
    print('  %-14s %6d %12.4f %12.4f' % ('con bloque', gl_con, sc_con, cm_con))
    print('  %-14s %6d %12.4f %12.4f' % ('sin bloque', gl_sin, sc_sin, cm_sin))
    def fmt_p(v):  # un p de 2.7e-07 impreso a seis decimales se ve como 0.000000
        return '%12.6f' % v if v >= 1e-6 else '%12.2e' % v
    print('\nValor p de cada termino:')
    print('  %-10s %12s %12s' % ('termino', 'con bloque', 'sin bloque'))
    for t in terminos:
        print('  %-10s %s %s' % (t, fmt_p(tabla_con.loc[t, 'PR(>F)']),
                                 fmt_p(tabla_sin.loc[t, 'PR(>F)'])))
    sc_bloque = tabla_con.loc['bloque', 'sum_sq']
    print('\nLa suma de cuadrados del bloque (%.4f) se sumo completa al error:' % sc_bloque)
    print('  %.4f + %.4f = %.4f' % (sc_con, sc_bloque, sc_sin))
    print('El cuadrado medio del error paso de %.4f a %.4f: %.1f veces mas grande.'
          % (cm_con, cm_sin, cm_sin / cm_con))
    print('Ese es el precio de no bloquear: el mismo experimento, con mas ruido en el denominador')
    print('de todas las F.')

# ---------- 5. Interaction plots y medias por bloque ----------
print()
for inter in usar:
    a, b = inter.split(':')
    plt.figure()
    datos.groupby([a, b])['respuesta'].mean().unstack(a).plot(marker='o', ax=plt.gca())
    plt.title('Interaccion ' + a + ' x ' + b)
    plt.xlabel(b)
    plt.ylabel('respuesta')
    plt.savefig('interaccion_%s_%s.png' % (a, b), dpi=120, bbox_inches='tight')
    print('grafica guardada: interaccion_%s_%s.png' % (a, b))
plt.figure(figsize=(5, 4))
alturas = [datos.loc[datos['bloque'] == b, 'respuesta'].mean() for b in etiquetas]
plt.bar(etiquetas, alturas, color='#f97316')
plt.axhline(datos['respuesta'].mean(), color='#334155', linestyle='--', linewidth=1)
plt.ylabel('respuesta promedio')
plt.title('Promedio por bloque (la raya es el promedio global)')
plt.savefig('bloques_medias.png', dpi=120, bbox_inches='tight')
print('grafica guardada: bloques_medias.png')
