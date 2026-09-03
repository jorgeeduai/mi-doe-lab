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
# La llave va en los Secrets de Replit (candado en la barra izquierda):
#   MINIMAX_API_KEY = la llave que te da el profesor
# Nunca la pegues en el codigo: los Secrets existen para eso.
# ============================================================

import os
import re
from openai import OpenAI

# MiniMax habla el mismo protocolo que OpenAI: solo cambia la direccion.
BASE_URL = os.environ.get('MINIMAX_BASE_URL', 'https://api.minimax.io/v1')
MODELO = os.environ.get('MINIMAX_MODEL', 'MiniMax-M3')

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


def preguntar(mensajes, contexto_analisis=None):
    """Manda la conversacion al modelo y regresa su respuesta como texto.

    mensajes: lista de {'role': 'user'|'assistant', 'content': str}
    contexto_analisis: la salida (texto) del ultimo analisis corrido, o None.
    """
    llave = os.environ.get('MINIMAX_API_KEY')
    if not llave:
        return ('No encuentro la llave. Agrega MINIMAX_API_KEY en los '
                'Secrets de Replit (el candado de la barra izquierda) y '
                'vuelve a intentar.')

    sistema = INSTRUCCIONES
    if contexto_analisis:
        sistema += ('\n\n--- SALIDA DEL ULTIMO ANALISIS DEL ESTUDIANTE ---\n'
                    + contexto_analisis)

    cliente = OpenAI(api_key=llave, base_url=BASE_URL)
    respuesta = cliente.chat.completions.create(
        model=MODELO,
        messages=[{'role': 'system', 'content': sistema}] + mensajes,
        max_tokens=1500,   # M3 razona antes de contestar y eso tambien gasta tokens
        temperature=0.3,
    )
    texto = respuesta.choices[0].message.content or ''
    # M3 incluye su razonamiento entre <think>...</think>: eso no se muestra.
    texto = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL).strip()
    return texto or 'El modelo no alcanzo a contestar: pregunta otra vez.'
