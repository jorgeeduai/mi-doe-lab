# ============================================================
# Q2003B - Diseno de Experimentos
# REGISTRO DE PIEZAS: aqui se ensambla tu programa.
#
# Cada pieza es un script que TU ya construiste en una sesion del
# curso. Conectarla = descomentar su bloque y completar los huecos
# (los ____). Guarda el archivo, recarga la pagina del navegador y
# la tarjeta de esa pieza aparece en tu programa.
#
# La pieza 1 (ANOVA) ya viene conectada, para que veas el patron.
# Las claves de cada campo:
#   clave        una palabra, sin espacios (identifica la pieza)
#   nombre       lo que dira la tarjeta
#   sesion       en que sesion construiste esta pieza
#   pregunta     que pregunta contesta este analisis, CON TUS PALABRAS
#   script       la ruta del .py dentro de piezas/
#   csv_ejemplo  un CSV de datos/ con el que esta pieza sabe trabajar
# ============================================================

NOMBRE_DEL_PROGRAMA = 'Mi DOE Lab'   # bautiza tu programa: este es tu titulo

PIEZAS = [

    # --- PIEZA 1: conectada de fabrica, este es el patron -----------
    {
        'clave': 'anova',
        'nombre': 'ANOVA de un factor',
        'sesion': 'S2-S3',
        'pregunta': 'Hay diferencia entre los grupos? Y cuales difieren?',
        'script': 'piezas/anova.py',
        'csv_ejemplo': 'datos/catalizadores.csv',
    },

    # --- PIEZA 2: factorial completo (la construiste en la S5) ------
    # Descomenta el bloque y completa los ____ :
    # {
    #     'clave': 'factorial',
    #     'nombre': 'Factorial completo 2^k',
    #     'sesion': 'S5',
    #     'pregunta': '____',
    #     'script': 'piezas/____.py',
    #     'csv_ejemplo': 'datos/____.csv',
    # },

    # --- PIEZA 3: factorial fraccionado (la construiste en la S6) ---
    # {
    #     'clave': 'fraccionado',
    #     'nombre': 'Factorial fraccionado 2^(k-p)',
    #     'sesion': 'S6',
    #     'pregunta': '____',
    #     'script': 'piezas/____.py',
    #     'csv_ejemplo': 'datos/____.csv',
    # },

    # --- PIEZA 4: diseno en bloques (la construiste en la S7) --------
    # {
    #     'clave': 'bloques',
    #     'nombre': 'Diseno en bloques',
    #     'sesion': 'S7',
    #     'pregunta': '____',
    #     'script': 'piezas/____.py',
    #     'csv_ejemplo': 'datos/____.csv',
    # },

]

# --- PIEZA 5: el asistente ------------------------------------------
# El chat se enciende cuando esto diga True Y la llave MINIMAX_API_KEY
# este en los Secrets de Replit (el candado de la barra izquierda).
ASISTENTE_CONECTADO = False
