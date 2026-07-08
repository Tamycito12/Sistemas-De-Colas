import base64
import io
import random

import matplotlib
matplotlib.use('Agg')  # backend sin interfaz gráfica (necesario en el servidor)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from django.shortcuts import render

# Cantidad máxima de personas que pueden esperar en la cola
MAX_COLA = 30


def inicio(request):
    return render(request, 'analisis/inicio.html')


def analisis(request):
    return render(request, 'analisis/analisis.html')


# ==========================================
# COLA CON FICHAS
# ==========================================

def _obtener_estado_cola(request):
    """Lee (o inicializa) el estado de la cola guardado en la sesión del usuario."""
    session = request.session

    session.setdefault('cola', [])
    session.setdefault('atendidos_nombres', [])
    session.setdefault('atendidos_fichas', [])
    session.setdefault('atendidos_tiempo', [])
    session.setdefault('contador_fichas', 1)

    return session


def cola(request):
    """Sistema de cola con fichas: registrar personas y atenderlas (FIFO)."""
    session = _obtener_estado_cola(request)
    mensaje = None
    error = None

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # --- Registrar persona ---
        if accion == 'registrar':
            nombre = (request.POST.get('nombre') or '').strip()

            if not nombre:
                error = 'Debes ingresar un nombre.'
            elif len(session['cola']) >= MAX_COLA:
                error = 'La cola está llena.'
            else:
                cola_actual = session['cola']
                cola_actual.append(nombre)
                session['cola'] = cola_actual
                mensaje = f'"{nombre}" fue agregado a la cola.'

        # --- Atender persona ---
        elif accion == 'atender':
            cola_actual = session['cola']

            if not cola_actual:
                error = 'No hay personas en espera.'
            else:
                persona = cola_actual.pop(0)
                session['cola'] = cola_actual

                ficha = session['contador_fichas']
                tiempo_atencion = random.randint(1, 5)

                atendidos_nombres = session['atendidos_nombres']
                atendidos_fichas = session['atendidos_fichas']
                atendidos_tiempo = session['atendidos_tiempo']

                atendidos_nombres.append(persona)
                atendidos_fichas.append(ficha)
                atendidos_tiempo.append(tiempo_atencion)

                session['atendidos_nombres'] = atendidos_nombres
                session['atendidos_fichas'] = atendidos_fichas
                session['atendidos_tiempo'] = atendidos_tiempo
                session['contador_fichas'] = ficha + 1

                mensaje = f'Atendiendo a "{persona}" — Ficha #{ficha} — Tiempo de atención: {tiempo_atencion} min.'

        # --- Reiniciar sistema ---
        elif accion == 'reiniciar':
            for clave in ('cola', 'atendidos_nombres', 'atendidos_fichas', 'atendidos_tiempo', 'contador_fichas'):
                if clave in session:
                    del session[clave]
            session = _obtener_estado_cola(request)
            mensaje = 'El sistema fue reiniciado.'

        session.modified = True

    historial = list(zip(
        session['atendidos_nombres'],
        session['atendidos_fichas'],
        session['atendidos_tiempo'],
    ))

    contexto = {
        'cola': session['cola'],
        'historial': historial,
        'max_cola': MAX_COLA,
        'mensaje': mensaje,
        'error': error,
    }
    return render(request, 'analisis/cola.html', contexto)


# ==========================================
# CÁLCULO MATEMÁTICO (Excel + distribución exponencial)
# ==========================================

def _leer_columna_t(archivo):
    """Lee un archivo Excel y devuelve la columna 't' como un vector de NumPy."""
    datos = pd.read_excel(archivo)

    if 't' not in datos.columns:
        raise ValueError('El archivo debe tener una columna llamada "t".')

    return datos['t'].to_numpy(dtype=float)


def calculo(request):
    """Sube dos archivos Excel (tiempo de servicio y tiempo de llegada),
    calcula el promedio del tiempo de servicio y grafica la distribución
    exponencial e^(-x/promedio) para ambos vectores.
    """
    error = None
    resultado = None
    grafico_base64 = None

    if request.method == 'POST':
        archivo_servicio = request.FILES.get('archivo_servicio')
        archivo_llegada = request.FILES.get('archivo_llegada')

        if not archivo_servicio or not archivo_llegada:
            error = 'Debes subir los dos archivos: tiempo de servicio y tiempo de llegada.'
        elif not archivo_servicio.name.lower().endswith('.xlsx') or not archivo_llegada.name.lower().endswith('.xlsx'):
            error = 'Ambos archivos deben ser Excel (.xlsx).'
        else:
            try:
                vector_servicio = _leer_columna_t(archivo_servicio)
                vector_llegada = _leer_columna_t(archivo_llegada)

                if len(vector_servicio) == 0 or len(vector_llegada) == 0:
                    raise ValueError('Los archivos no pueden estar vacíos.')

                promedio_servicio = float(np.mean(vector_servicio))

                def mi_funcion(x):
                    return np.exp(-x / promedio_servicio)

                y_servicio = mi_funcion(vector_servicio)
                y_llegada = mi_funcion(vector_llegada)

                # --- Generar la gráfica con Matplotlib ---
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(vector_servicio, y_servicio, marker='o', label='Tiempo de Servicio')
                ax.plot(vector_llegada, y_llegada, marker='s', label='Tiempo de Llegada')
                ax.set_title('Distribución Exponencial')
                ax.set_xlabel('Tiempo')
                ax.set_ylabel(f'e^(-x/{promedio_servicio:.2f})')
                ax.legend()
                ax.grid(True)

                buffer = io.BytesIO()
                fig.savefig(buffer, format='png', bbox_inches='tight')
                plt.close(fig)
                buffer.seek(0)
                grafico_base64 = base64.b64encode(buffer.read()).decode('utf-8')

                resultado = {
                    'promedio_servicio': round(promedio_servicio, 4),
                    'vector_servicio': vector_servicio.tolist(),
                    'vector_llegada': vector_llegada.tolist(),
                }
            except ValueError as e:
                error = str(e)
            except Exception:
                error = 'No se pudo procesar alguno de los archivos. Verifica el formato.'

    return render(request, 'analisis/calculo.html', {
        'resultado': resultado,
        'error': error,
        'grafico_base64': grafico_base64,
    })
