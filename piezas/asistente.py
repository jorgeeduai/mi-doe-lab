# ============================================================
# Q2003B - Diseno de Experimentos
# Piezas del programa: el asistente (un chatbot que conoce TUS resultados)
#
# Esta pieza no se corre sola: la usa app.py cuando escribes en el chat.
#
# La diferencia con un chatbot normal: antes de contestar, este recibe
# la salida del ultimo analisis que corriste en tu programa. Por eso
# puede contestar "por que mi factor B no es significativo" sobre TU
# tabla, no sobre teoria general.
#
# ---------------------------------------------------------------
# TU ASISTENTE PUEDE HABLAR CON DOS MOTORES DISTINTOS.
#
# Elige solo, segun la llave que encuentre en los Secrets de Replit
# (el candado de la barra izquierda):
#
#   GEMINI_API_KEY   -> Google Gemini   (SDK google-genai, el nativo)
#   MINIMAX_API_KEY  -> MiniMax         (SDK de OpenAI, otra direccion)
#
# La llave de Gemini la sacas tu en aistudio.google.com/apikey; es
# gratis y es TUYA. La de MiniMax la reparte el profesor cuando toca.
# Si pones las dos, gana Gemini. Para forzar la otra, agrega un Secret
# mas:  PROVEEDOR = minimax
#
# Que un mismo programa cambie de motor cambiando una llave no es un
# detalle: es como se prueba si tu analisis depende del modelo o no.
#
# NUNCA pegues una llave en el codigo. Para eso existen los Secrets.
# ============================================================

import logging
import os
import re

# Que modelo usa cada motor.
#
# Ojo con los modelos fijos: caducan. 'gemini-2.5-flash' dejo de aceptar
# llaves nuevas y un kit que lo tuviera cableado hoy tronaria con un 404.
# El alias '-latest' apunta siempre al flash vigente, asi que no se muere.
MODELO_GEMINI = os.environ.get('GEMINI_MODEL', 'gemini-flash-latest')
MODELO_MINIMAX = os.environ.get('MINIMAX_MODEL', 'MiniMax-M3')
MINIMAX_BASE_URL = os.environ.get('MINIMAX_BASE_URL', 'https://api.minimax.io/v1')

INSTRUCCIONES = """Eres el asistente de un programa de analisis de disenos \
experimentales construido por un estudiante de nanotecnologia del curso Q2003B \
(Diseno de Experimentos). Contesta SIEMPRE en espanol, breve y concreto.

Sabes de: ANOVA de un factor, supuestos (Shapiro-Wilk, Levene), post-hoc Tukey, \
factoriales 2^k, efectos e interacciones, fraccionados 2^(k-p) (generadores, \
alias, resolucion) y disenos en bloques (y que pasa si no bloqueas).

Si te comparten la salida de un analisis, contesta SOBRE ESOS numeros: cita las \
cifras del resultado, no inventes otras. Si te preguntan algo que la salida no \
contiene, dilo y explica que analisis lo contestaria. No des sermones: al grano.

Escribe en TEXTO PLANO: nada de markdown (ni asteriscos, ni tablas, ni titulos).
Para listas usa guiones simples. Tu respuesta se muestra tal cual en un chat."""


def proveedor():
    """Cual de los dos motores toca, con lo que hay en los Secrets.

    Regresa 'gemini', 'minimax', o None si no hay ninguna llave.
    """
    forzado = os.environ.get('PROVEEDOR', '').strip().lower()
    if forzado in ('gemini', 'minimax'):
        return forzado
    if os.environ.get('GEMINI_API_KEY'):
        return 'gemini'
    if os.environ.get('MINIMAX_API_KEY'):
        return 'minimax'
    return None


def motor():
    """El nombre del motor encendido, para mostrarlo en la pantalla."""
    return {'gemini': 'Gemini', 'minimax': 'MiniMax'}.get(proveedor())


def _sin_llave(nombre):
    return ('No encuentro la llave. Agrega %s en los Secrets de Replit '
            '(el candado de la barra izquierda) y vuelve a intentar.' % nombre)


def _limpiar(texto):
    """Algunos modelos razonan en voz alta entre <think>...</think>.
    Eso es su borrador, no su respuesta: no se muestra."""
    return re.sub(r'<think>.*?</think>', '', texto or '', flags=re.DOTALL).strip()


def _preguntar_gemini(sistema, mensajes):
    llave = os.environ.get('GEMINI_API_KEY')
    if not llave:
        return _sin_llave('GEMINI_API_KEY')

    from google import genai

    # El SDK avisa de una funcion avanzada que este chat no usa. El aviso
    # sale en la consola de Replit y solo asusta: aqui se calla.
    logging.getLogger('google_genai.models').setLevel(logging.ERROR)

    # Gemini nombra 'model' lo que el chat llama 'assistant'.
    conversacion = [
        {'role': 'model' if m.get('role') == 'assistant' else 'user',
         'parts': [{'text': m.get('content', '')}]}
        for m in mensajes
    ]

    cliente = genai.Client(api_key=llave)
    respuesta = cliente.models.generate_content(
        model=MODELO_GEMINI,
        contents=conversacion,
        config={'system_instruction': sistema, 'temperature': 0.3},
    )
    return _limpiar(getattr(respuesta, 'text', None))


def _preguntar_minimax(sistema, mensajes):
    llave = os.environ.get('MINIMAX_API_KEY')
    if not llave:
        return _sin_llave('MINIMAX_API_KEY')

    from openai import OpenAI

    # MiniMax habla el mismo protocolo que OpenAI: solo cambia la direccion.
    cliente = OpenAI(api_key=llave, base_url=MINIMAX_BASE_URL)
    respuesta = cliente.chat.completions.create(
        model=MODELO_MINIMAX,
        messages=[{'role': 'system', 'content': sistema}] + mensajes,
        max_tokens=1500,   # M3 razona antes de contestar y eso tambien gasta tokens
        temperature=0.3,
    )
    return _limpiar(respuesta.choices[0].message.content)


def preguntar(mensajes, contexto_analisis=None):
    """Manda la conversacion al modelo y regresa su respuesta como texto.

    mensajes: lista de {'role': 'user'|'assistant', 'content': str}
    contexto_analisis: la salida (texto) del ultimo analisis corrido, o None.
    """
    cual = proveedor()
    if cual is None:
        return _sin_llave('GEMINI_API_KEY')

    sistema = INSTRUCCIONES
    if contexto_analisis:
        sistema += ('\n\n--- SALIDA DEL ULTIMO ANALISIS DEL ESTUDIANTE ---\n'
                    + contexto_analisis)

    if cual == 'gemini':
        texto = _preguntar_gemini(sistema, mensajes)
    else:
        texto = _preguntar_minimax(sistema, mensajes)

    return texto or 'El modelo no alcanzo a contestar: pregunta otra vez.'
