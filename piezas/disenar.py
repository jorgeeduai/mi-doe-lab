# ============================================================
# Q2003B - Diseno de Experimentos
# Piezas del programa: el disenador (la matriz ANTES de medir)
#
# Las otras cuatro piezas analizan datos que YA existen. Esta hace lo
# que en el trabajo real va PRIMERO: escribe la lista de corridas que
# tienes que hacer en el laboratorio, con la columna 'respuesta'
# VACIA, para que la llenes con lo que midas.
#
# Que arma:
#   - factorial 2^k con 2 a 6 factores, con replicas, con bloques
#     (cada bloque es una replica completa) o en media fraccion;
#   - un factor con varios niveles, para analizarlo con ANOVA.
#
# Dos cosas que hace por ti y que a mano se olvidan:
#   1. ALEATORIZA el orden de las corridas (y dentro de cada bloque,
#      si corriste en bloques). La columna 'corrida' es el orden en
#      que hay que hacerlas, no el orden bonito de la tabla.
#   2. Escribe los niveles con SUS ETIQUETAS (25 y 60, citrato y
#      borohidruro), no con -1 y 1: la hoja se lee en la mesa del
#      laboratorio, donde nadie mide en unidades codificadas.
#
# Esta pieza NO usa pandas: solo biblioteca estandar. Es la unica del
# kit que corre en cualquier python sin instalar nada.
#
# Uso desde la Shell:
#   python piezas/disenar.py      (imprime como se usa y un diseno de muestra)
# Y la usa app.py cuando aprietas "Generar mi CSV" en la pagina.
# ============================================================

import csv
import io
import pprint
import random

# Nombres que el resto del kit usa para otra cosa: los analisis los
# ignoran como columna de factor, asi que un factor no puede llamarse asi.
NOMBRES_RESERVADOS = ('respuesta', 'corrida', 'bloque', 'orden', 'replica')

MINIMO_FACTORES = 2
MAXIMO_FACTORES = 6
MAXIMO_REPLICAS = 4
MINIMO_NIVELES = 2
MAXIMO_NIVELES = 6
MINIMO_MEDICIONES = 2
MAXIMO_MEDICIONES = 10


def construir(descripcion):
    """Arma la matriz del experimento que describe el diccionario.

    Regresa tres cosas:
      nombre_columnas  los encabezados del CSV, en orden
      renglones        una lista por corrida, ya aleatorizada
      notas            lo que hay que saber de este diseno, en texto

    Un diseno mal descrito levanta ValueError con el motivo en
    cristiano: app.py se lo ensena al usuario tal cual.
    """
    if not isinstance(descripcion, dict):
        raise ValueError('La descripcion del experimento tiene que ser un '
                         'diccionario con la llave "tipo".')
    tipo = str(descripcion.get('tipo', '')).strip().lower()
    if tipo == 'factorial':
        return _factorial(descripcion)
    if tipo == 'anova':
        return _un_factor(descripcion)
    raise ValueError('No se que diseno armar con tipo "%s". Los dos que esta '
                     'pieza sabe hacer son "factorial" y "anova".' % tipo)


def a_csv(nombre_columnas, renglones):
    """El texto del CSV, listo para guardarse en datos/."""
    papel = io.StringIO()
    escritor = csv.writer(papel, lineterminator='\n')
    escritor.writerow(nombre_columnas)
    escritor.writerows(renglones)
    return papel.getvalue()


# ------------------------------------------------------------------
# Revisar lo que llego: nombres, etiquetas y numeros
# ------------------------------------------------------------------

def _nombre_de_factor(valor, numero):
    """El nombre de un factor se vuelve encabezado de columna: tiene que
    poder vivir en un CSV y no chocar con las columnas del programa."""
    nombre = ('' if valor is None else str(valor)).strip()
    if not nombre:
        raise ValueError('El factor %d se quedo sin nombre.' % numero)
    if len(nombre) > 20:
        raise ValueError('El nombre "%s" es larguisimo para un encabezado. '
                         'Con 20 letras alcanza.' % nombre)
    for prohibido in (',', ';', '"', "'", ' ', '\t', '\n'):
        if prohibido in nombre:
            raise ValueError('El nombre "%s" trae comas, comillas o espacios, y '
                             'eso rompe el CSV. Usa una sola palabra: A, '
                             'temperatura, tiempo_horno.' % nombre)
    if nombre.lower() in NOMBRES_RESERVADOS:
        raise ValueError('"%s" es un nombre que el programa usa para otra cosa '
                         '(%s). Ponle otro al factor, o los analisis lo van a '
                         'ignorar.' % (nombre, ', '.join(NOMBRES_RESERVADOS)))
    return nombre


def _etiqueta(valor, de_donde):
    """Un nivel puede llegar como texto ('citrato') o como numero (25):
    de las dos formas termina siendo el texto que se escribe en el CSV."""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)   # 25.0 se escribe 25, que es como se lee en la mesa
    texto = ('' if valor is None else str(valor)).strip()
    if not texto:
        raise ValueError('Falta %s.' % de_donde)
    if len(texto) > 30:
        raise ValueError('%s es larguisimo ("%s"). Con 30 letras alcanza.'
                         % (de_donde, texto))
    if ',' in texto or '\n' in texto:
        raise ValueError('%s no puede llevar comas ni saltos de linea, y llego '
                         '"%s".' % (de_donde, texto))
    return texto


def _entero(valor, de_donde, minimo, maximo, defecto):
    if valor is None or valor == '':
        return defecto
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValueError('%s tiene que ser un numero entero, y llego "%s".'
                         % (de_donde, valor))
    if numero < minimo or numero > maximo:
        raise ValueError('%s va de %d a %d, y llego %d.'
                         % (de_donde, minimo, maximo, numero))
    return numero


# ------------------------------------------------------------------
# El factorial 2^k
# ------------------------------------------------------------------

def _combinaciones(cuantos_factores, media_fraccion):
    """Los signos de cada combinacion: -1 (nivel bajo) y 1 (nivel alto).

    El diseno completo son las 2^k combinaciones: el numero de corrida
    en binario da los signos, un bit por factor. Con media fraccion se
    generan solo las del completo de los PRIMEROS factores y el ultimo
    sale del producto de los demas: ese producto es el generador, y es
    lo mismo que fraccionado.py va a encontrar despues en los datos.
    """
    base = cuantos_factores - 1 if media_fraccion else cuantos_factores
    combinaciones = []
    for numero in range(2 ** base):
        signos = [1 if (numero >> posicion) & 1 else -1 for posicion in range(base)]
        if media_fraccion:
            producto = 1
            for signo in signos:
                producto *= signo
            signos.append(producto)
        combinaciones.append(signos)
    return combinaciones


def _lo_leen_al_reves(menos, mas):
    """Las piezas de analisis ordenan solas los dos niveles de cada factor
    (sorted) y le llaman 'bajo' al primero. Con numeros eso coincide con lo
    que uno espera; con texto manda el alfabeto, y entonces 'borohidruro'
    entra como nivel bajo aunque aqui se haya escrito como el nivel +."""
    try:
        return float(menos) > float(mas)
    except ValueError:
        return menos > mas


def _renglon(signos, niveles):
    """Los signos de una corrida, escritos con las etiquetas reales."""
    return [niveles[posicion][0 if signo == -1 else 1]
            for posicion, signo in enumerate(signos)]


def _factorial(descripcion):
    factores = descripcion.get('factores') or []
    if not isinstance(factores, (list, tuple)):
        raise ValueError('Los factores tienen que venir en una lista, uno por '
                         'renglon de la tabla.')
    if len(factores) < MINIMO_FACTORES or len(factores) > MAXIMO_FACTORES:
        raise ValueError('Un factorial lleva de %d a %d factores, y llegaron %d. '
                         'Con mas de %d el diseno completo se vuelve enorme: ahi '
                         'toca fraccionar.'
                         % (MINIMO_FACTORES, MAXIMO_FACTORES, len(factores),
                            MAXIMO_FACTORES))

    nombres = []
    niveles = []
    for numero, factor in enumerate(factores, start=1):
        if not isinstance(factor, dict):
            raise ValueError('El factor %d no trae su nombre y sus dos niveles.'
                             % numero)
        nombre = _nombre_de_factor(factor.get('nombre'), numero)
        if nombre.lower() in [puesto.lower() for puesto in nombres]:
            raise ValueError('Hay dos factores llamados "%s". Cada factor lleva '
                             'su propio nombre: si no, no se sabria de cual es '
                             'cada columna.' % nombre)
        menos = _etiqueta(factor.get('menos'), 'el nivel - del factor "%s"' % nombre)
        mas = _etiqueta(factor.get('mas'), 'el nivel + del factor "%s"' % nombre)
        if menos == mas:
            raise ValueError('Los dos niveles del factor "%s" dicen "%s". Un '
                             'factor que no cambia no se puede estudiar.'
                             % (nombre, menos))
        nombres.append(nombre)
        niveles.append((menos, mas))

    replicas = _entero(descripcion.get('replicas'), 'El numero de replicas',
                       1, MAXIMO_REPLICAS, 1)
    en_bloques = bool(descripcion.get('bloques'))
    media_fraccion = bool(descripcion.get('mitad'))
    notas = []

    if media_fraccion:
        if len(nombres) < 3:
            raise ValueError('La media fraccion pide 3 factores o mas. Con 2 el '
                             'diseno completo son 4 corridas y no hay nada que '
                             'recortar.')
        if replicas > 1 or en_bloques:
            raise ValueError('La media fraccion no se junta con replicas ni con '
                             'bloques en esta pieza: la media fraccion existe '
                             'para correr POCO, una vez cada combinacion. Deja '
                             'una de las dos cosas.')

    if en_bloques and replicas < 2:
        replicas = 2
        notas.append('Un bloque solo no separa nada: se subio a 2 replicas, que '
                     'son 2 bloques. Si vas a correr en tres dias o tres lotes, '
                     'sube las replicas a 3.')

    combinaciones = _combinaciones(len(nombres), media_fraccion)

    nombre_columnas = ['corrida']
    if en_bloques:
        nombre_columnas.append('bloque')
    nombre_columnas.extend(nombres)
    nombre_columnas.append('respuesta')

    renglones = []
    if en_bloques:
        # Cada bloque lleva el diseno completo, y el sorteo es DENTRO del
        # bloque: entre bloques no se mezcla, porque el bloque es el dia
        # (o el lote, o el horno) y ese no se puede barajar.
        for numero_bloque in range(1, replicas + 1):
            del_bloque = list(combinaciones)
            random.shuffle(del_bloque)
            for signos in del_bloque:
                renglones.append(['bloque%d' % numero_bloque]
                                 + _renglon(signos, niveles))
    else:
        todas = []
        for _ in range(replicas):
            todas.extend(combinaciones)
        random.shuffle(todas)
        for signos in todas:
            renglones.append(_renglon(signos, niveles))

    # La columna 'corrida' se numera hasta el final, cuando el sorteo ya
    # decidio quien va primero: por eso vale como orden de ejecucion.
    for indice, renglon in enumerate(renglones, start=1):
        renglon.insert(0, str(indice))
        renglon.append('')

    if media_fraccion:
        producto = '·'.join(nombres[:-1])
        notas.append('Media fraccion 2^(%d-1): %d corridas de las %d que pide el '
                     'diseno completo.'
                     % (len(nombres), len(renglones), 2 ** len(nombres)))
        notas.append('La regla que se uso (el generador): %s = %s. El nivel del '
                     'ultimo factor sale del producto de los signos de los otros.'
                     % (nombres[-1], producto))
        notas.append('Lo que cuesta: %s queda confundido con la interaccion %s, y '
                     'con toda interaccion que incluya ese producto. Si ahi sale '
                     'un efecto grande, los datos no dicen cual de los dos lo hizo.'
                     % (nombres[-1], producto))
    else:
        notas.append('Factorial completo 2^%d: %d combinaciones%s, %d corridas en '
                     'total.'
                     % (len(nombres), len(combinaciones),
                        '' if replicas == 1 else ' por replica', len(renglones)))

    if en_bloques:
        notas.append('%d bloques (bloque1 a bloque%d), cada uno con una replica '
                     'completa. Asi no se sacrifica ningun efecto, y el analisis '
                     'le toca a la pieza de bloques.' % (replicas, replicas))
    elif replicas > 1:
        notas.append('%d replicas del diseno entero: repetir es lo que da error '
                     'puro, y sin error puro la tabla ANOVA no puede probar nada.'
                     % replicas)
    else:
        notas.append('Una sola replica: no hay error puro. Los efectos se juzgan '
                     'con el grafico de Pareto, o usando las interacciones chicas '
                     'como error.')

    al_reves = [nombre for nombre, dos in zip(nombres, niveles)
                if _lo_leen_al_reves(dos[0], dos[1])]
    if al_reves:
        notas.append('Para cuando leas el analisis: las piezas ordenan solas los '
                     'dos niveles de cada factor y le llaman "bajo" al primero. En '
                     '%s eso deja como bajo el nivel que aqui pusiste de +, asi que '
                     'ese efecto va a salir con el signo cambiado. El tamano es el '
                     'mismo.' % ', '.join(al_reves))

    notas.append('El orden de la columna corrida se sorteo ahora, y ese es el '
                 'orden en que hay que hacerlas: correr en orden bonito deja que '
                 'lo que cambia con el tiempo se meta en tus efectos.')
    notas.append('La columna respuesta va vacia a proposito: es tu plantilla. '
                 'Llenala con lo que midas en cada corrida y entonces analizala.')
    return nombre_columnas, renglones, notas


# ------------------------------------------------------------------
# Un factor con varios niveles (para el ANOVA)
# ------------------------------------------------------------------

def _un_factor(descripcion):
    factor = descripcion.get('factor') or {}
    if not isinstance(factor, dict):
        raise ValueError('El factor tiene que traer su nombre y sus niveles.')
    nombre = _nombre_de_factor(factor.get('nombre'), 1)

    crudos = factor.get('niveles') or []
    if isinstance(crudos, str):
        crudos = [parte for parte in crudos.split(',') if parte.strip()]
    if not isinstance(crudos, (list, tuple)):
        raise ValueError('Los niveles vienen en una lista, o escritos separados '
                         'por comas: A, B, C.')

    niveles = []
    for numero, crudo in enumerate(crudos, start=1):
        etiqueta = _etiqueta(crudo, 'el nivel %d del factor "%s"' % (numero, nombre))
        if etiqueta in niveles:
            raise ValueError('El nivel "%s" esta repetido. Cada nivel se escribe '
                             'una vez: las repeticiones son las mediciones.'
                             % etiqueta)
        niveles.append(etiqueta)

    if len(niveles) < MINIMO_NIVELES or len(niveles) > MAXIMO_NIVELES:
        raise ValueError('Un ANOVA de un factor compara de %d a %d niveles, y '
                         'llegaron %d.'
                         % (MINIMO_NIVELES, MAXIMO_NIVELES, len(niveles)))

    mediciones = _entero(descripcion.get('mediciones_por_nivel'),
                         'Las mediciones por nivel',
                         MINIMO_MEDICIONES, MAXIMO_MEDICIONES, 3)

    nombre_columnas = ['corrida', nombre, 'respuesta']

    # Todas las mediciones entran a la misma tombola: en un diseno de un
    # factor no hay bloques, asi que se aleatoriza todo junto.
    todas = []
    for etiqueta in niveles:
        todas.extend([etiqueta] * mediciones)
    random.shuffle(todas)
    renglones = [[str(indice), etiqueta, '']
                 for indice, etiqueta in enumerate(todas, start=1)]

    notas = ['Un factor ("%s") con %d niveles y %d mediciones por nivel: %d '
             'corridas en total.'
             % (nombre, len(niveles), mediciones, len(renglones)),
             'Los niveles que vas a comparar: %s.' % ', '.join(niveles)]
    if mediciones < 3:
        notas.append('Con %d mediciones por nivel la prueba de normalidad no se '
                     'puede hacer por grupo (pide 3 o mas). Si puedes, sube a 3.'
                     % mediciones)
    notas.append('El orden de la columna corrida se sorteo ahora: haz las '
                 'mediciones en ese orden, no todas las de un nivel seguidas.')
    notas.append('La columna respuesta va vacia a proposito: es tu plantilla. '
                 'Llenala con lo que midas en cada corrida y entonces analizala.')
    return nombre_columnas, renglones, notas


# ------------------------------------------------------------------
# Correrla sola, desde la Shell: como se usa y un diseno de muestra
# ------------------------------------------------------------------

if __name__ == '__main__':
    ejemplo = {
        'tipo': 'factorial',
        'factores': [
            {'nombre': 'temperatura', 'menos': '25', 'mas': '60'},
            {'nombre': 'reductor', 'menos': 'citrato', 'mas': 'borohidruro'},
            {'nombre': 'agitacion', 'menos': '300', 'mas': '900'},
        ],
        'replicas': 2,
        'bloques': True,
    }

    print('EL DISENADOR: la matriz de tu experimento, ANTES de medir')
    print('-' * 60)
    print('Normalmente se usa desde la pagina del programa, en la seccion')
    print('"Disena tu experimento". Desde codigo se usa asi:')
    print()
    print('    from piezas import disenar')
    print('    columnas, renglones, notas = disenar.construir(descripcion)')
    print('    print(disenar.a_csv(columnas, renglones))')
    print()
    print('Esta es la descripcion del diseno de muestra de abajo:')
    print()
    for linea in pprint.pformat(ejemplo, width=68).split('\n'):
        print('    ' + linea)
    print()

    columnas_muestra, renglones_muestra, notas_muestra = construir(ejemplo)
    print('NOTAS DEL DISENO')
    print('-' * 60)
    for nota in notas_muestra:
        print('- %s' % nota)
    print()
    print('EL CSV (asi mismo se guarda en datos/)')
    print('-' * 60)
    print(a_csv(columnas_muestra, renglones_muestra), end='')
