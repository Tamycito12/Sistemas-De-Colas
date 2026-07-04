import math
from django.shortcuts import render


def inicio(request):
    return render(request, 'analisis/inicio.html')


def analisis(request):
    return render(request, 'analisis/analisis.html')


def cargar(request):
    """Carga de archivo Excel/PDF con datos de varias personas.
    Por ahora solo interfaz: recibe el archivo. El cálculo se agrega después.
    """
    nombre_archivo = None
    error = None
    resultados = None  # Aquí luego irá la lista de dicts calculados por persona

    if request.method == 'POST':
        archivo = request.FILES.get('archivo')

        if not archivo:
            error = 'Debes seleccionar un archivo.'
        elif not archivo.name.lower().endswith(('.xlsx', '.csv', '.pdf')):
            error = 'Formato no soportado. Usa .xlsx, .csv o .pdf.'
        else:
            nombre_archivo = archivo.name
            # TODO: leer el archivo (openpyxl/pandas para Excel, pdfplumber para PDF)
            # y llenar `resultados` con una lista de dicts:
            # {'nombre': ..., 'lam': ..., 'mu': ..., 'servidores': ..., 'rho': ..., ...}

    return render(request, 'analisis/cargar.html', {
        'nombre_archivo': nombre_archivo,
        'error': error,
        'resultados': resultados,
    })


def mm1(request):
    """Modelo de colas M/M/1: un solo servidor."""
    resultado = None
    error = None

    if request.method == 'POST':
        try:
            lam = float(request.POST['lambda'])
            mu = float(request.POST['mu'])

            if lam <= 0 or mu <= 0:
                error = 'λ y μ deben ser mayores que cero.'
            elif lam >= mu:
                error = 'El sistema es inestable: λ debe ser menor que μ.'
            else:
                rho = lam / mu
                L = rho / (1 - rho)
                Lq = (rho ** 2) / (1 - rho)
                W = 1 / (mu - lam)
                Wq = rho / (mu - lam)

                resultado = {
                    'rho': round(rho * 100, 2),
                    'L': round(L, 4),
                    'Lq': round(Lq, 4),
                    'W': round(W, 4),
                    'Wq': round(Wq, 4),
                }
        except (ValueError, KeyError):
            error = 'Ingresa valores numéricos válidos.'

    return render(request, 'analisis/mm1.html', {'resultado': resultado, 'error': error})


def mmc(request):
    """Modelo de colas M/M/c: múltiples servidores en paralelo."""
    resultado = None
    error = None

    if request.method == 'POST':
        try:
            lam = float(request.POST['lambda'])
            mu = float(request.POST['mu'])
            c = int(request.POST['servidores'])

            if lam <= 0 or mu <= 0 or c <= 0:
                error = 'λ, μ y el número de servidores deben ser mayores que cero.'
            else:
                a = lam / mu          # carga ofrecida (Erlangs)
                rho = a / c           # utilización por servidor

                if rho >= 1:
                    error = 'El sistema es inestable: λ debe ser menor que c·μ.'
                else:
                    suma = sum((a ** n) / math.factorial(n) for n in range(c))
                    termino_c = (a ** c) / (math.factorial(c) * (1 - rho))
                    P0 = 1 / (suma + termino_c)

                    Lq = (P0 * (a ** c) * rho) / (math.factorial(c) * (1 - rho) ** 2)
                    L = Lq + a
                    Wq = Lq / lam
                    W = Wq + (1 / mu)

                    resultado = {
                        'rho': round(rho * 100, 2),
                        'P0': round(P0 * 100, 2),
                        'L': round(L, 4),
                        'Lq': round(Lq, 4),
                        'W': round(W, 4),
                        'Wq': round(Wq, 4),
                    }
        except (ValueError, KeyError):
            error = 'Ingresa valores numéricos válidos.'

    return render(request, 'analisis/mmc.html', {'resultado': resultado, 'error': error})
