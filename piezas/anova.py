# ============================================================
# Q2003B - Diseno de Experimentos
# Piezas del programa: ANOVA de un factor (lo que construiste en S2 y S3)
#
# Uso desde la Shell de Replit:
#   python piezas/anova.py datos/catalizadores.csv
#   python piezas/anova.py datos/catalizadores.csv catalizador minutos
#
# El CSV lleva una columna de texto con el factor (los grupos) y una
# columna numerica con la respuesta. Si no le dices cuales son, las
# encuentra solo: la primera columna de texto es el factor y la ultima
# numerica es la respuesta.
#
# Que hace, en orden (el mismo camino de anova_completo.py de la S3):
#   1. DESCRIPTIVAS: n, media y desviacion de cada grupo.
#   2. SUPUESTOS: Shapiro-Wilk por grupo (normalidad) y Levene
#      (varianzas iguales). Si alguno falla, lo dice y cambia de arma.
#   3. ANOVA de un factor (o Kruskal-Wallis si los supuestos fallaron).
#   4. POST-HOC Tukey HSD, solo si el ANOVA encontro diferencia:
#      dice CUALES grupos difieren, no solo que hay diferencia.
#   5. Un boxplot con las medias marcadas (anova_boxplot.png).
# ============================================================

import sys
import pandas as pd
import scipy.stats as stats
import matplotlib
matplotlib.use('Agg')  # Replit no tiene pantalla: la grafica se guarda como PNG
import matplotlib.pyplot as plt
from statsmodels.stats.multicomp import pairwise_tukeyhsd

ALPHA = 0.05

if len(sys.argv) < 2:
    print('Uso: python piezas/anova.py <archivo.csv> [factor] [respuesta]')
    sys.exit(1)

datos = pd.read_csv(sys.argv[1])

# ------------------------------------------------------------
# Que columna es el factor y cual la respuesta
# ------------------------------------------------------------
if len(sys.argv) >= 4:
    factor, respuesta = sys.argv[2], sys.argv[3]
else:
    columnas_texto = [c for c in datos.columns if datos[c].dtype == object]
    columnas_num = [c for c in datos.columns if datos[c].dtype != object]
    if not columnas_texto or not columnas_num:
        print('No encuentro una columna de texto (factor) y una numerica (respuesta).')
        print('Dimelas tu: python piezas/anova.py %s factor respuesta' % sys.argv[1])
        sys.exit(1)
    factor, respuesta = columnas_texto[0], columnas_num[-1]

grupos_nombres = sorted(datos[factor].unique())
grupos = [datos.loc[datos[factor] == g, respuesta] for g in grupos_nombres]

print('=' * 60)
print('ANOVA DE UN FACTOR')
print('=' * 60)
print('Archivo:   %s' % sys.argv[1])
print('Factor:    %s (%d grupos: %s)' % (factor, len(grupos_nombres), ', '.join(str(g) for g in grupos_nombres)))
print('Respuesta: %s' % respuesta)

# ------------------------------------------------------------
# 1. Descriptivas
# ------------------------------------------------------------
print()
print('DESCRIPTIVAS')
print('-' * 60)
print('%-12s %6s %10s %10s' % ('grupo', 'n', 'media', 'desv'))
for nombre, serie in zip(grupos_nombres, grupos):
    print('%-12s %6d %10.2f %10.2f' % (nombre, len(serie), serie.mean(), serie.std()))

# ------------------------------------------------------------
# 2. Supuestos
# ------------------------------------------------------------
print()
print('SUPUESTOS')
print('-' * 60)
normalidad_ok = True
for nombre, serie in zip(grupos_nombres, grupos):
    if len(serie) >= 3:
        _, p_sw = stats.shapiro(serie)
        veredicto = 'normal' if p_sw > ALPHA else 'NO normal'
        print('Shapiro-Wilk %-8s p = %.4f  -> %s' % (nombre, p_sw, veredicto))
        if p_sw <= ALPHA:
            normalidad_ok = False

_, p_lev = stats.levene(*grupos)
varianzas_ok = p_lev > ALPHA
print('Levene (varianzas)    p = %.4f  -> %s' % (p_lev, 'iguales' if varianzas_ok else 'NO iguales'))

# ------------------------------------------------------------
# 3. La prueba
# ------------------------------------------------------------
print()
if normalidad_ok and varianzas_ok:
    print('ANOVA (los supuestos se cumplen)')
    print('-' * 60)
    F, p = stats.f_oneway(*grupos)
    print('F = %.3f   valor p = %.5f' % (F, p))
    hay_diferencia = p < ALPHA
else:
    print('KRUSKAL-WALLIS (algun supuesto fallo: prueba no parametrica)')
    print('-' * 60)
    H, p = stats.kruskal(*grupos)
    print('H = %.3f   valor p = %.5f' % (H, p))
    hay_diferencia = p < ALPHA

if hay_diferencia:
    print('Con alfa = %.2f: HAY diferencia entre los grupos.' % ALPHA)
else:
    print('Con alfa = %.2f: no hay evidencia de diferencia entre los grupos.' % ALPHA)

# ------------------------------------------------------------
# 4. Post-hoc: cuales difieren
# ------------------------------------------------------------
if hay_diferencia and len(grupos_nombres) > 2:
    print()
    print('POST-HOC TUKEY HSD: cuales grupos difieren')
    print('-' * 60)
    tukey = pairwise_tukeyhsd(datos[respuesta], datos[factor], alpha=ALPHA)
    print(tukey)

# ------------------------------------------------------------
# 5. La grafica
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 5))
ax.boxplot([list(s) for s in grupos])
ax.set_xticks(range(1, len(grupos_nombres) + 1))
ax.set_xticklabels([str(g) for g in grupos_nombres])
for i, serie in enumerate(grupos, start=1):
    ax.plot(i, serie.mean(), marker='D', color='#e8590c', markersize=8, zorder=3)
ax.set_xlabel(factor)
ax.set_ylabel(respuesta)
ax.set_title('%s por %s (rombo = media)' % (respuesta, factor))
fig.tight_layout()
fig.savefig('anova_boxplot.png', dpi=120)
print()
print('Grafica guardada: anova_boxplot.png')
