# ============================================================
# Q2003B - Diseno de Experimentos
# Piezas del programa: el inspector de formato
#
# Cada analisis espera su CSV con una forma concreta. Cuando el
# archivo no la tiene, el script truena con un error de Python que
# no dice que arreglar. Esta pieza revisa el CSV ANTES de correr y
# lo dice en cristiano: que columna falta, que columna sobra, que
# niveles estan mal.
#
# La usa app.py en dos momentos:
#   - al presionar "Correr analisis": si hay errores, no corre y
#     te los muestra; los avisos se anteponen al resultado.
#   - en la ficha "formato de datos" de cada tarjeta.
#
# Tambien se puede correr sola desde la Shell:
#   python piezas/formato.py datos/misdatos.csv factorial
# ============================================================

import sys
import pandas as pd

# Las mismas columnas que factorial.py ignora: estan en el CSV pero
# no son factores del experimento.
NO_SON_FACTORES = ('respuesta', 'corrida', 'bloque', 'orden', 'replica')

# Lo que cada analisis espera. 'ejemplo' son los dos primeros
# renglones de un CSV bien formado, para ensenarlo en la tarjeta.
ESPECIFICACIONES = {
    'anova': {
        'espera': ('Una columna de TEXTO con el grupo (el factor) y una '
                   'columna NUMERICA con la respuesta. Un renglon por medicion.'),
        'ejemplo': 'catalizador,minutos\nA,45\nA,48\nB,52',
    },
    'factorial': {
        'espera': ('Una columna por factor, cada una con DOS niveles '
                   '(-1/1 o sus nombres reales), y una columna llamada '
                   '"respuesta". Un renglon por corrida.'),
        'ejemplo': 'Catalizador,Temperatura,respuesta\nA,60,45\nB,80,52',
    },
    'fraccionado': {
        'espera': ('Igual que el factorial: factores de DOS niveles y columna '
                   '"respuesta". La fraccion se nota en el numero de corridas: '
                   'menos que 2^k. El generador no se declara: el script lo '
                   'descubre en los datos.'),
        'ejemplo': 'A,B,C,D,E,respuesta\n-1,-1,-1,-1,1,65.2\n1,-1,-1,-1,-1,82.1',
    },
    'bloques': {
        'espera': ('Factores de DOS niveles, columna "respuesta" y ademas una '
                   'columna llamada "bloque" con la etiqueta del dia, lote u '
                   'horno de cada corrida.'),
        'ejemplo': 'corrida,bloque,A,B,C,respuesta\n1,dia1,1,1,1,77.7\n2,dia1,-1,1,1,67.4',
    },
}


def revisar(ruta_csv, clave):
    """Revisa el CSV para ese analisis. Regresa (errores, avisos):
    con errores el analisis NO debe correr; los avisos solo se anteponen."""
    errores, avisos = [], []

    try:
        datos = pd.read_csv(ruta_csv)
    except Exception as error:
        return (['El archivo no se puede leer como CSV: %s' % error], [])

    if datos.empty:
        return (['El CSV no tiene renglones de datos.'], [])

    columnas = list(datos.columns)
    if any(c.strip() != c for c in columnas):
        avisos.append('Hay encabezados con espacios alrededor: %s. Mejor sin espacios.'
                      % [c for c in columnas if c.strip() != c])

    incompletas = [c for c in columnas if datos[c].isna().any()]
    if incompletas:
        errores.append('Hay celdas vacias en: %s. Cada renglon lleva todos sus datos.'
                       % ', '.join(incompletas))

    if clave == 'anova':
        de_texto = [c for c in columnas if datos[c].dtype == object]
        numericas = [c for c in columnas if datos[c].dtype != object]
        if not de_texto:
            errores.append('No hay columna de texto para el grupo (el factor). '
                           'Ejemplo: una columna "catalizador" con A, B, C.')
        if not numericas:
            errores.append('No hay columna numerica para la respuesta.')
        if de_texto and numericas:
            grupos = datos[de_texto[0]].value_counts()
            if len(grupos) < 2:
                errores.append('La columna "%s" tiene un solo grupo: no hay que comparar.'
                               % de_texto[0])
            elif (grupos < 3).any():
                avisos.append('Algun grupo tiene menos de 3 datos: la prueba de '
                              'normalidad no se puede hacer ahi.')
        return (errores, avisos)

    # factorial, fraccionado y bloques comparten la base
    if 'respuesta' not in columnas:
        errores.append('Falta la columna "respuesta" (asi, con ese nombre exacto). '
                       'Columnas encontradas: %s.' % ', '.join(columnas))
    elif datos['respuesta'].dtype == object:
        errores.append('La columna "respuesta" trae texto: tiene que ser numerica.')

    factores = [c for c in columnas if c.lower() not in NO_SON_FACTORES]
    if not factores:
        errores.append('No encuentro columnas de factores (todas son respuesta/'
                       'corrida/bloque/orden/replica).')
    for f in factores:
        niveles = datos[f].nunique()
        if niveles != 2:
            errores.append('El factor "%s" tiene %d niveles y estos analisis piden '
                           'exactamente 2 (-1/1 o dos nombres). Si "%s" no es un '
                           'factor, renombralo a corrida, bloque, orden o replica '
                           'para que se ignore.' % (f, niveles, f))
        else:
            conteo = datos[f].value_counts()
            if conteo.iloc[0] != conteo.iloc[-1]:
                avisos.append('El factor "%s" no esta balanceado (%d y %d corridas '
                              'por nivel).' % (f, conteo.iloc[0], conteo.iloc[-1]))

    if clave == 'fraccionado' and factores and not errores:
        if len(datos) >= 2 ** len(factores):
            avisos.append('Con %d factores y %d corridas esto es un factorial '
                          'COMPLETO (o mas): la pieza de fraccionado no va a '
                          'encontrar generador. Prueba la pieza de factorial.'
                          % (len(factores), len(datos)))

    if clave == 'bloques':
        con_bloque = next((c for c in columnas if c.lower() == 'bloque'), None)
        if con_bloque is None:
            errores.append('Falta la columna "bloque" (el dia, lote u horno de cada '
                           'corrida). Sin ella no hay nada que separar: usa la pieza '
                           'de factorial.')
        elif datos[con_bloque].nunique() < 2:
            errores.append('La columna "bloque" tiene un solo valor: todo se corrio '
                           'en el mismo bloque y no hay nada que separar.')

    return (errores, avisos)


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[2] not in ESPECIFICACIONES:
        print('Uso: python piezas/formato.py <archivo.csv> <%s>'
              % '|'.join(ESPECIFICACIONES))
        sys.exit(1)
    errores, avisos = revisar(sys.argv[1], sys.argv[2])
    print('FORMATO PARA %s: %s' % (sys.argv[2].upper(), sys.argv[1]))
    print('-' * 60)
    for e in errores:
        print('[ERROR] %s' % e)
    for a in avisos:
        print('[aviso] %s' % a)
    if not errores and not avisos:
        print('El formato esta bien: ese CSV se puede analizar con esa pieza.')
    sys.exit(1 if errores else 0)
