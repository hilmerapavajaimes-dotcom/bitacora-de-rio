import math
from datetime import datetime, timedelta, timezone


def _formato_hora(horas_decimales: float) -> str:
    h_norm = horas_decimales % 24.0
    horas = int(h_norm)
    minutos = int(round((h_norm - horas) * 60))
    if minutos == 60:
        horas = (horas + 1) % 24
        minutos = 0
    return f"{horas:02d}:{minutos:02d}"


def calcular_datos_solunares(fecha: datetime | None = None) -> dict:
    """
    Calcula la fase lunar, porcentaje de iluminación, calificación de pesca
    y horas pico solunares para cualquier fecha sin requerir internet.
    """
    if fecha is None:
        fecha = datetime.now()

    # Referencia astronómica: Luna Nueva conocida (6 de enero de 2000, 18:14 UTC)
    ref_luna_nueva = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    fecha_utc = datetime(fecha.year, fecha.month, fecha.day, 12, 0, tzinfo=timezone.utc)

    ciclo_sinodico = 29.530588853
    dias_transcurridos = (fecha_utc - ref_luna_nueva).total_seconds() / 86400.0
    edad_lunar = dias_transcurridos % ciclo_sinodico

    # Porcentaje de iluminación (0% a 100%)
    angulo = 2.0 * math.pi * (edad_lunar / ciclo_sinodico)
    iluminacion = round(((1.0 - math.cos(angulo)) / 2.0) * 100.0, 1)

    # Clasificación de fase lunar
    if edad_lunar < 1.85 or edad_lunar >= 27.68:
        fase = "Luna Nueva"
        icono = "🌑"
        consejo = "Ideal para depredadores nocturnos (bagre, payara) y ataques agresivos al amanecer."
    elif edad_lunar < 5.54:
        fase = "Luna Creciente"
        icono = "🌒"
        consejo = "Actividad en ascenso; busca bordes de corriente y bocas de caños."
    elif edad_lunar < 9.23:
        fase = "Cuarto Creciente"
        icono = "🌓"
        consejo = "Buena actividad en horas de tarde y primeras horas de la noche."
    elif edad_lunar < 12.91:
        fase = "Gibosa Creciente"
        icono = "🌔"
        consejo = "Los peces comen con fuerza antes de la luna llena; prueba señuelos de media agua."
    elif edad_lunar < 16.61:
        fase = "Luna Llena"
        icono = "🌕"
        consejo = "Máxima actividad gravitacional. Excelente para pesca nocturna y madrugada."
    elif edad_lunar < 20.30:
        fase = "Gibosa Menguante"
        icono = "🌖"
        consejo = "Buen pique temprano en la mañana antes de que caliente el sol."
    elif edad_lunar < 23.99:
        fase = "Cuarto Menguante"
        icono = "🌗"
        consejo = "Actividad moderada; trabaja estructuras sumergidas y pozos profundos."
    else:
        fase = "Luna Menguante"
        icono = "🌘"
        consejo = "Transición hacia luna nueva; excelente para señuelos de superficie al alba."

    # Puntuación de actividad (mayor en Luna Nueva y Luna Llena, secundario en Cuartos)
    # cos(2 * angulo) es +1 en Nueva/Llena y -1 en Cuartos
    factor_gravedad = (math.cos(2.0 * angulo) + 1.0) / 2.0  # 0.0 a 1.0
    puntaje = int(round(58 + (factor_gravedad * 38)))

    if puntaje >= 88:
        calificacion = "Excelente"
        estrellas = 5
    elif puntaje >= 76:
        calificacion = "Muy Bueno"
        estrellas = 4
    elif puntaje >= 65:
        calificacion = "Bueno"
        estrellas = 3
    else:
        calificacion = "Moderado"
        estrellas = 2

    # Cálculo aproximado del tránsito lunar (se retrasa ~50.4 min cada día)
    transito_superior = (edad_lunar * 0.8403) % 24.0
    transito_inferior = (transito_superior + 12.42) % 24.0
    salida_lunar = (transito_superior - 6.21) % 24.0
    puesta_lunar = (transito_superior + 6.21) % 24.0

    mayor_1 = f"{_formato_hora(transito_superior - 1.0)} - {_formato_hora(transito_superior + 1.0)}"
    mayor_2 = f"{_formato_hora(transito_inferior - 1.0)} - {_formato_hora(transito_inferior + 1.0)}"
    menor_1 = f"{_formato_hora(salida_lunar - 0.5)} - {_formato_hora(salida_lunar + 0.5)}"
    menor_2 = f"{_formato_hora(puesta_lunar - 0.5)} - {_formato_hora(puesta_lunar + 0.5)}"

    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    return {
        "fecha_str": f"{dias_semana[fecha.weekday()]} {fecha.day:02d}/{fecha.month:02d}",
        "fase": fase,
        "icono": icono,
        "iluminacion": iluminacion,
        "edad_lunar": round(edad_lunar, 1),
        "puntaje": puntaje,
        "calificacion": calificacion,
        "estrellas": estrellas,
        "consejo": consejo,
        "mayor_1": mayor_1,
        "mayor_2": mayor_2,
        "menor_1": menor_1,
        "menor_2": menor_2,
    }


def obtener_pronostico_semanal() -> list[dict]:
    hoy = datetime.now()
    return [calcular_datos_solunares(hoy + timedelta(days=i)) for i in range(7)]
