# ============================================================
# Q2003B - Diseno de Experimentos
# Sesion 6: analisis de un factorial fraccionado 2^(k-p)
#
# Uso desde la Shell de Replit:
#   python fraccionado.py tio2_fraccionado.csv
#   python fraccionado.py tio2_fraccionado.csv A:C      (con la interaccion que elegiste)
#
# Corre en el mismo Repl de la S4/S5: su requirements.txt ya trae
# pandas, matplotlib y statsmodels, que es todo lo que este script pide.
#
# El CSV lleva una columna por factor (dos niveles cada uno; pueden
# venir como -1/1 o con sus nombres reales) y una columna llamada
# 'respuesta'.
#
# Que hace, en orden:
#   1. LA FRACCION: descubre que columna es producto de las otras (el
#      generador), escribe la relacion de definicion y los alias, y
#      dice la resolucion del diseno. No se lo dices tu: lo lee del CSV.
#   2. EFECTOS: promedio en + menos promedio en -, para cada factor y
#      cada par, ordenados de mayor a menor, y un diagrama de Pareto
#      (efectos_pareto.png).
#   3. ANOVA del modelo reducido: los efectos principales mas las
#      interacciones que pases en la linea de comandos (por ejemplo A:C).
#      Sin replicas, el error sale de los terminos que dejaste fuera:
#      por eso primero lees el Pareto y despues eliges que meter.
#   4. Un interaction plot por cada interaccion que pediste.
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
interacciones = [arg.upper() for arg in sys.argv[2:]]  # por ejemplo A:C B:D
factores = [col for col in datos.columns if col != 'respuesta']
for f in factores:  # codificar cada factor: nivel bajo = -1, nivel alto = +1
    bajo, alto = sorted(datos[f].unique())
    datos[f] = datos[f].map({bajo: -1, alto: 1})
signo = lambda v: '+' if v > 0 else '-'

# ---------- 1. La fraccion: generador, relacion de definicion, alias ----------
print('LA FRACCION')
k, n = len(factores), len(datos)
p = 0
while 2 ** (k - p) > n:
    p += 1
print('%d factores en %d corridas: un 2^(%d-%d) (el completo pediria %d)' % (k, n, k, p, 2 ** k))
palabras = []
for tam in range(2, k + 1):  # que columna es el producto de otras
    for grupo in combinations(factores, tam):
        producto = datos[list(grupo)].prod(axis=1)
        if (producto == 1).all() or (producto == -1).all():
            palabra = ''.join(grupo)
            if not any(set(palabra) == set(w) for w in palabras):
                palabras.append(palabra)
if not palabras:
    print('Ninguna columna es producto de otras: es un factorial completo, no hay alias.')
else:
    # Un 2^(k-p) se arma con p generadores, no con uno. Los primeros k-p factores
    # son la base (llevan el diseno completo) y cada factor añadido sale de un
    # producto de la base: ese producto es su generador. Las 2^p - 1 palabras de
    # la relacion de definicion salen de multiplicarlos entre si, asi que hay mas
    # palabras que generadores, y las de sobra son las DERIVADAS.
    # (Corregido el 1-sep-2026: hasta entonces esta parte imprimia un solo
    #  generador, el de la primera palabra, y con p >= 2 se callaba los demas.)
    base = set(factores[:k - p])
    generadores, derivadas = [], []
    for w in palabras:
        anadidos = [c for c in w if c not in base]
        if len(anadidos) == 1:
            gen = anadidos[0]
            generadores.append((gen, ''.join(c for c in w if c != gen), w))
        else:
            derivadas.append(w)
    if len(generadores) == 1:
        print('Generador: %s = %s' % (generadores[0][0], generadores[0][1]))
    else:
        print('Generadores (%d, uno por cada vez que se partio el diseno):' % len(generadores))
        for gen, prod, w in generadores:
            print('  %s = %-6s  ->  I = %s' % (gen, prod, w))
    print('Relacion de definicion: I = ' + ' = '.join(palabras))
    if derivadas:
        print('  ojo: %s no %s de ningun generador. %s de multiplicar los de arriba' % (
            ' y '.join(derivadas),
            'salen' if len(derivadas) > 1 else 'sale',
            'Salen' if len(derivadas) > 1 else 'Sale'))
        if len(generadores) == 2 and len(derivadas) == 1:
            print('  %s x %s = %s  (las letras repetidas se cancelan)' % (
                generadores[0][2], generadores[1][2], derivadas[0]))
    resolucion = min(len(w) for w in palabras)
    print('Resolucion: %s (la palabra mas corta tiene %d letras)' % ('I' * resolucion if resolucion < 4 else {4: 'IV', 5: 'V', 6: 'VI', 7: 'VII'}.get(resolucion, str(resolucion)), resolucion))

    def alias(efecto):
        salida = []
        for w in palabras:
            letras = ''.join(sorted(c for c in set(efecto + w) if (efecto + w).count(c) % 2 == 1))
            salida.append(letras if letras else 'I')
        return salida
    print('Alias (cada efecto comparte columna con):')
    for f in factores:
        print('  %-3s = %s' % (f, ' = '.join(alias(f))))
    for a, b in combinations(factores, 2):
        print('  %-3s = %s' % (a + b, ' = '.join(alias(a + b))))

# ---------- 2. Efectos y Pareto ----------
print('\nEFECTOS (promedio en + menos promedio en -)')
efectos = {}
for f in factores:
    efectos[f] = datos.loc[datos[f] == 1, 'respuesta'].mean() - datos.loc[datos[f] == -1, 'respuesta'].mean()
for a, b in combinations(factores, 2):
    col = datos[a] * datos[b]
    efectos[a + ':' + b] = datos.loc[col == 1, 'respuesta'].mean() - datos.loc[col == -1, 'respuesta'].mean()
orden = sorted(efectos, key=lambda e: -abs(efectos[e]))
for e in orden:
    print('  %-6s %9.4f' % (e, efectos[e]))
plt.figure(figsize=(7, 4))
plt.barh(orden[::-1], [abs(efectos[e]) for e in orden[::-1]])
plt.xlabel('|efecto|')
plt.title('Pareto de efectos')
plt.savefig('efectos_pareto.png', dpi=120, bbox_inches='tight')
print('grafica guardada: efectos_pareto.png')

# ---------- 3. ANOVA del modelo reducido ----------
terminos = list(factores) + interacciones
modelo = ols('respuesta ~ ' + ' + '.join(terminos), data=datos).fit()
print('\nTABLA ANOVA (tipo 2) del modelo: respuesta ~ ' + ' + '.join(terminos))
if len(terminos) >= n - 1:
    print('AVISO: metiste tantos terminos como corridas; no queda nada para el error y no hay p.')
print(sm.stats.anova_lm(modelo, typ=2).to_string(float_format=lambda x: '%.6g' % x))
print('R2 = %.4f' % modelo.rsquared)

# ---------- 4. Interaction plots ----------
for inter in interacciones:
    a, b = inter.split(':')
    plt.figure()
    datos.groupby([a, b])['respuesta'].mean().unstack(a).plot(marker='o', ax=plt.gca())
    plt.title('Interaccion ' + a + ' x ' + b)
    plt.xlabel(b)
    plt.ylabel('respuesta')
    plt.savefig('interaccion_%s_%s.png' % (a, b), dpi=120, bbox_inches='tight')
    print('grafica guardada: interaccion_%s_%s.png' % (a, b))
