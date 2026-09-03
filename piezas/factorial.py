# ============================================================
# Q2003B - Diseno de Experimentos
# Sesion 5: analisis factorial completo, la herramienta principal de la sesion
#
# Uso desde la Shell de Replit:
#   python factorial.py catalizadores_factorial.csv
#   python factorial.py catalisis_bloques.csv        (trae bloques: ver abajo)
#
# Corre en el mismo Repl de la S4: su requirements.txt ya trae
# pandas, matplotlib y statsmodels, que es todo lo que este script pide.
#
# El CSV lleva una columna por factor (dos niveles cada uno)
# y una columna llamada 'respuesta'.
#
# El modelo es el mismo que ajusta el simulador del DOE Lab:
# efectos principales + interacciones de dos factores.
#
# ------------------------------------------------------------
# QUE COLUMNAS SON FACTORES Y CUALES NO (arreglo del 2-sep-2026)
# ------------------------------------------------------------
# Hasta hoy el script tomaba como factor TODA columna que no se
# llamara 'respuesta'. Con los CSV de la S7 eso reventaba:
#
#   ValueError: too many values to unpack (expected 2)
#
# porque intentaba tratar 'corrida' (16 valores distintos) como si
# fuera un factor de dos niveles. Ahora hay una lista explicita de
# columnas que NO son factores, y se ignoran.
#
# Si el CSV trae una columna 'bloque', el script ademas ajusta el
# modelo DOS VECES, con el bloque adentro y sin el, y pone las dos
# lecturas frente a frente. Eso es lo que hace visible el efecto de
# bloquear: la variacion del dia, del lote o del horno sale del error
# y los efectos reales aparecen.
# ============================================================

import sys
from itertools import combinations
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Replit no tiene pantalla: las graficas se guardan como PNG
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Columnas que existen en el CSV pero NO son factores del experimento.
# 'corrida' es solo el numero de renglon y 'bloque' es la etiqueta del dia,
# del lote o del horno: no es algo que el experimentador haya elegido variar.
NO_SON_FACTORES = ('respuesta', 'corrida', 'bloque', 'orden', 'replica')

datos = pd.read_csv(sys.argv[1])
factores = [col for col in datos.columns if col.lower() not in NO_SON_FACTORES]
hay_bloques = 'bloque' in (c.lower() for c in datos.columns)

for f in factores:  # codificar cada factor: nivel bajo = -1, nivel alto = +1
    niveles = sorted(datos[f].unique())
    if len(niveles) != 2:
        print('La columna "%s" tiene %d niveles distintos y este script solo maneja dos.'
              % (f, len(niveles)))
        print('Si no es un factor del experimento, agregala a NO_SON_FACTORES arriba.')
        sys.exit(1)
    bajo, alto = niveles
    datos[f + '_c'] = datos[f].map({bajo: -1, alto: 1})

print('FACTORES: ' + ', '.join(factores))
if hay_bloques:
    print('BLOQUE:   la columna "bloque", con %d bloques' % datos['bloque'].nunique())

terminos = [f + '_c' for f in factores] + ['%s_c:%s_c' % par for par in combinations(factores, 2)]
modelo = ols('respuesta ~ ' + ' + '.join(terminos), data=datos).fit()

# Sin grados de libertad no hay error que estimar, y sin error no hay F ni p.
# Pasa cuando el modelo pide tantos terminos como corridas hay: con cinco
# factores en dieciseis corridas son 5 principales + 10 parejas + el intercepto,
# o sea 16 parametros para 16 datos. Antes de este aviso, statsmodels tronaba
# con 'ValueError: array must not contain infs or NaNs', que no dice nada util.
if modelo.df_resid < 1:
    print('\nEste diseno no deja grados de libertad para el error: %d corridas y %d terminos'
          % (len(datos), len(terminos) + 1))
    print('en el modelo (%d efectos principales y %d interacciones de dos factores).'
          % (len(factores), len(terminos) - len(factores)))
    print('Sin error no hay F ni valor p.')
    print('Si el CSV es de un diseno fraccionado, el guion que le toca es fraccionado.py,')
    print('que sabe que efectos estan aliasados y no intenta estimarlos todos.')
    sys.exit(1)

print('\nEFECTOS (2 x coeficiente)')
print((2 * modelo.params.drop('Intercept')).round(4).to_string())
print('\nTABLA ANOVA (tipo 2)')
tabla = sm.stats.anova_lm(modelo, typ=2)
print(tabla.to_string(float_format=lambda x: '%.6g' % x))

# ------------------------------------------------------------
# Si hay bloques: el mismo modelo, con el bloque adentro, y la comparacion
# ------------------------------------------------------------
# OJO con la formula. Lo natural seria escribir C(bloque) para decirle a
# statsmodels que el bloque es categorico, pero si uno de los factores se
# llama 'C' (como la presion en catalisis_bloques.csv) la formula lo confunde
# con esa columna y falla con:
#     PatsyError: Error evaluating factor: TypeError: 'Series' object is not callable
# Como la columna 'bloque' es texto (dia1/dia2), basta con nombrarla: patsy la
# trata como categorica sola.
if hay_bloques:
    print('\n' + '=' * 60)
    print('EL EFECTO DE BLOQUEAR')
    print('=' * 60)

    print('\nMedias por bloque:')
    print(datos.groupby('bloque')['respuesta'].agg(['mean', 'count']).round(4).to_string())

    modelo_con = ols('respuesta ~ bloque + ' + ' + '.join(terminos), data=datos).fit()
    if modelo_con.df_resid < 1:
        print('\nCon el bloque adentro no quedan grados de libertad para el error.')
        print('Usa bloques.py, que permite elegir que interacciones entran al modelo.')
        sys.exit(0)

    tabla_con = sm.stats.anova_lm(modelo_con, typ=2)
    tabla_con = tabla_con.reindex(['bloque'] + [i for i in tabla_con.index if i != 'bloque'])
    print('\nTABLA ANOVA CON EL BLOQUE ADENTRO')
    print(tabla_con.to_string(float_format=lambda x: '%.6g' % x))

    cm_sin = tabla.loc['Residual', 'sum_sq'] / tabla.loc['Residual', 'df']
    cm_con = tabla_con.loc['Residual', 'sum_sq'] / tabla_con.loc['Residual', 'df']
    print('\nLa fila del error, en los dos modelos:')
    print('  %-22s %4s %12s %12s' % ('', 'gl', 'SC', 'CM'))
    print('  %-22s %4d %12.4f %12.4f'
          % ('sin bloquear', tabla.loc['Residual', 'df'], tabla.loc['Residual', 'sum_sq'], cm_sin))
    print('  %-22s %4d %12.4f %12.4f'
          % ('con el bloque adentro', tabla_con.loc['Residual', 'df'],
             tabla_con.loc['Residual', 'sum_sq'], cm_con))
    print('  el cuadrado medio del error se divide entre %.2f al meter el bloque'
          % (cm_sin / cm_con))

    print('\nEfecto por efecto, el valor p antes y despues:')
    print('  %-16s %10s %10s' % ('termino', 'sin', 'con'))
    rescatados = []
    for t in tabla.index:
        if t == 'Residual':
            continue
        p_sin, p_con = tabla.loc[t, 'PR(>F)'], tabla_con.loc[t, 'PR(>F)']
        nota = ''
        if p_con < 0.05 <= p_sin:
            nota = '  <-- lo rescata el bloque'
            rescatados.append(t.replace('_c', ''))
        elif p_sin < 0.05 <= p_con:
            nota = '  <-- se pierde'
        print('  %-16s %10.6f %10.6f%s' % (t.replace('_c', ''), p_sin, p_con, nota))

    if rescatados:
        print('\nSin bloquear, %s se habrian dado por no significativos.' % ', '.join(rescatados))
        print('La variacion entre bloques estaba dentro del error y tapaba efectos reales.')
    else:
        print('\nNingun efecto cambia de veredicto: aqui bloquear no cambia las conclusiones,')
        print('aunque el error si baje. Bloquear nunca hace dano; a veces no hace falta.')

for a, b in combinations(factores, 2):  # un interaction plot por par de factores
    datos.groupby([a, b])['respuesta'].mean().unstack(a).plot(marker='o')
    plt.title('Interaccion ' + a + ' x ' + b)
    plt.xlabel(b)
    plt.ylabel('respuesta')
    plt.savefig('interaccion_%s_%s.png' % (a, b), dpi=120, bbox_inches='tight')
    print('grafica guardada: interaccion_%s_%s.png' % (a, b))
