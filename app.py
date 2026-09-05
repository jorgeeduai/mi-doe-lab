# ============================================================
# Q2003B - Diseno de Experimentos
# EL CHASIS: el servidor web que une tus piezas en un programa.
#
# Este archivo NO se edita durante el ensamble. Tu trabajo esta en
# registro.py (conectar piezas) y en los Secrets (la llave del chat).
#
# Como funciona, en corto:
#   1. Lee registro.py en cada recarga: por eso conectar una pieza
#      es guardar ese archivo y recargar el navegador.
#   2. Cuando pides un analisis, corre TU script en la Shell, igual
#      que tu lo corrias a mano:  python piezas/xxx.py datos/yyy.csv
#      y captura lo que imprime y las graficas PNG que genera.
#   3. Cuando le escribes al asistente, le adjunta la salida del
#      ultimo analisis: por eso puede opinar sobre TUS resultados.
#      Con que motor habla (Gemini o MiniMax) lo decide la llave que
#      pusiste en los Secrets; eso se resuelve en piezas/asistente.py.
#   4. En "Disena tu experimento" no analiza nada: le pide la matriz a
#      piezas/disenar.py y la guarda en datos/ como un CSV con la
#      columna 'respuesta' vacia, listo para llenarse en el laboratorio.
#
# Correr:  python app.py   (Replit abre la vista web solo)
# ============================================================

import importlib
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata

from flask import Flask, jsonify, render_template, request, send_file

import registro

app = Flask(__name__)

CARPETA_DATOS = 'datos'
CARPETA_SALIDAS = os.path.join('static', 'salidas')
os.makedirs(CARPETA_SALIDAS, exist_ok=True)

# La memoria del programa: la salida del ultimo analisis que corriste.
# Es lo que el asistente recibe como contexto.
ULTIMO = {'texto': None, 'pieza': None, 'csv': None}


def motor_del_asistente():
    """El nombre del motor que va a contestar (Gemini o MiniMax), o None
    si no hay llave. La regla de cual toca vive en piezas/asistente.py."""
    try:
        from piezas import asistente
        return asistente.motor()
    except Exception:
        return None


def leer_registro():
    """Relee registro.py del disco: asi 'guardar y recargar' basta."""
    importlib.reload(registro)
    return registro


def piezas_con_estado(reg):
    """Cada pieza del registro, con su semaforo de archivos y su formato."""
    from piezas import formato
    lista = []
    for pieza in reg.PIEZAS:
        p = dict(pieza)
        p['formato'] = formato.ESPECIFICACIONES.get(p.get('clave'))
        falta = []
        if not os.path.exists(p.get('script', '')):
            falta.append('script')
        if not os.path.exists(p.get('csv_ejemplo', '')):
            falta.append('csv_ejemplo')
        if '____' in str(p.values()):
            falta.append('huecos ____ sin completar')
        p['lista'] = not falta
        p['falta'] = falta
        lista.append(p)
    return lista


@app.route('/')
def portada():
    reg = leer_registro()
    csvs = sorted(a for a in os.listdir(CARPETA_DATOS) if a.endswith('.csv'))
    return render_template(
        'index.html',
        nombre_programa=reg.NOMBRE_DEL_PROGRAMA,
        piezas=piezas_con_estado(reg),
        total_piezas=4,  # anova, factorial, fraccionado, bloques
        asistente_conectado=reg.ASISTENTE_CONECTADO,
        asistente_con_llave=bool(motor_del_asistente()),
        asistente_motor=motor_del_asistente(),
        csvs=csvs,
    )


@app.route('/correr', methods=['POST'])
def correr():
    reg = leer_registro()
    peticion = request.get_json(force=True)
    clave = peticion.get('clave', '')
    csv = peticion.get('csv', '')
    extra = peticion.get('extra', '').split()

    pieza = next((p for p in reg.PIEZAS if p.get('clave') == clave), None)
    if pieza is None:
        return jsonify({'error': 'Esa pieza no esta conectada en registro.py.'}), 400

    ruta_csv = os.path.join(CARPETA_DATOS, os.path.basename(csv))
    if not os.path.exists(ruta_csv):
        return jsonify({'error': 'No encuentro el archivo %s.' % ruta_csv}), 400

    # El inspector de formato revisa ANTES de correr: un error de forma
    # se explica en cristiano, no con un traceback de Python.
    from piezas import formato
    encabezado = ''
    if clave in formato.ESPECIFICACIONES:
        errores, avisos = formato.revisar(ruta_csv, clave)
        if errores:
            texto = 'EL FORMATO DE %s NO SIRVE PARA ESTA PIEZA\n' % os.path.basename(csv)
            texto += '-' * 60 + '\n'
            texto += '\n'.join('[ERROR] %s' % e for e in errores)
            texto += '\n\nLo que esta pieza espera:\n%s\n\nEjemplo:\n%s\n' % (
                formato.ESPECIFICACIONES[clave]['espera'],
                formato.ESPECIFICACIONES[clave]['ejemplo'])
            return jsonify({'salida': texto, 'imagenes': [], 'ok': False})
        if avisos:
            encabezado = '\n'.join('[aviso de formato] %s' % a for a in avisos) + '\n\n'

    inicio = time.time()
    try:
        proceso = subprocess.run(
            [sys.executable, pieza['script'], ruta_csv] + extra,
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'El analisis tardo mas de 2 minutos y se corto.'}), 500

    salida = encabezado + proceso.stdout
    if proceso.returncode != 0:
        salida += '\n[EL SCRIPT TERMINO CON ERROR]\n' + proceso.stderr[-2000:]

    # Recoger las graficas que el script acaba de generar en la carpeta raiz
    imagenes = []
    for archivo in sorted(os.listdir('.')):
        if archivo.endswith('.png') and os.path.getmtime(archivo) >= inicio:
            destino = '%d-%s' % (int(inicio), archivo)
            shutil.move(archivo, os.path.join(CARPETA_SALIDAS, destino))
            imagenes.append('/static/salidas/' + destino)

    ULTIMO['texto'] = salida
    ULTIMO['pieza'] = pieza['nombre']
    ULTIMO['csv'] = os.path.basename(csv)

    return jsonify({
        'salida': salida,
        'imagenes': imagenes,
        'ok': proceso.returncode == 0,
    })


@app.route('/subir', methods=['POST'])
def subir():
    archivo = request.files.get('archivo')
    if not archivo or not archivo.filename.endswith('.csv'):
        return jsonify({'error': 'Sube un archivo .csv.'}), 400
    nombre = os.path.basename(archivo.filename).replace(' ', '_')
    archivo.save(os.path.join(CARPETA_DATOS, nombre))
    return jsonify({'ok': True, 'nombre': nombre})


def nombre_de_archivo(nombre):
    """El nombre que escribio el usuario, vuelto nombre de archivo:
    'Sintesis de AgNP (piloto)' -> 'diseno_sintesis-de-agnp-piloto.csv'.
    Si ese ya existe, le pone -2, -3... para no pisar un diseno anterior."""
    limpio = unicodedata.normalize('NFKD', nombre)
    limpio = limpio.encode('ascii', 'ignore').decode('ascii').lower()
    limpio = re.sub(r'[^a-z0-9]+', '-', limpio).strip('-')
    base = 'diseno_' + (limpio or 'sin-nombre')
    candidato = base + '.csv'
    numero = 2
    while os.path.exists(os.path.join(CARPETA_DATOS, candidato)):
        candidato = '%s-%d.csv' % (base, numero)
        numero += 1
    return candidato


@app.route('/disenar', methods=['POST'])
def disenar():
    # La pieza se importa aqui adentro, no arriba: asi el programa
    # arranca aunque el archivo no este, igual que con el asistente.
    from piezas import disenar as disenador
    descripcion = request.get_json(force=True)
    try:
        columnas, renglones, notas = disenador.construir(descripcion)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    texto = disenador.a_csv(columnas, renglones)
    nombre = nombre_de_archivo(str(descripcion.get('nombre', '')))
    with open(os.path.join(CARPETA_DATOS, nombre), 'w', encoding='utf-8') as archivo:
        archivo.write(texto)

    return jsonify({
        'archivo': nombre,
        'corridas': len(renglones),
        'notas': notas,
        'preview': '\n'.join(texto.split('\n')[:8]),
    })


@app.route('/plantilla/<archivo>')
def plantilla(archivo):
    """Bajar a la computadora un CSV de datos/ (la plantilla recien hecha)."""
    nombre = os.path.basename(archivo)
    ruta = os.path.abspath(os.path.join(CARPETA_DATOS, nombre))
    if not nombre.endswith('.csv') or not os.path.exists(ruta):
        return jsonify({'error': 'No encuentro %s en datos/.' % nombre}), 404
    return send_file(ruta, as_attachment=True)


@app.route('/preguntar', methods=['POST'])
def preguntar():
    reg = leer_registro()
    if not reg.ASISTENTE_CONECTADO:
        return jsonify({'error': 'El asistente no esta conectado: pon '
                                 'ASISTENTE_CONECTADO = True en registro.py.'}), 400
    mensajes = request.get_json(force=True).get('mensajes', [])
    contexto = None
    if ULTIMO['texto']:
        contexto = ('Analisis: %s sobre %s\n\n%s'
                    % (ULTIMO['pieza'], ULTIMO['csv'], ULTIMO['texto']))
    try:
        from piezas import asistente
        respuesta = asistente.preguntar(mensajes, contexto)
    except Exception as error:
        return jsonify({'error': 'El asistente fallo: %s' % error}), 500
    return jsonify({'respuesta': respuesta,
                    'con_contexto': contexto is not None})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
