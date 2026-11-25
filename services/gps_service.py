import math
import flet as ft

try:
    import flet_geolocator as fg
except ImportError:
    fg = None


def calcular_distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia exacta en metros entre dos coordenadas GPS (Fórmula de Haversine)."""
    radio_tierra_m = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radio_tierra_m * c


def calcular_rumbo_grados(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula el ángulo de dirección (0° a 360°, donde 0° es Norte) desde el punto 1 al punto 2."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    theta = math.atan2(y, x)
    return (math.degrees(theta) + 360.0) % 360.0


def obtener_punto_cardinal(grados: float) -> str:
    """Convierte grados (0-360) a dirección de brújula legible."""
    direcciones = [
        "Norte (N)",
        "Noreste (NE)",
        "Este (E)",
        "Sureste (SE)",
        "Sur (S)",
        "Suroeste (SO)",
        "Oeste (O)",
        "Noroeste (NO)",
    ]
    indice = round(grados / 45.0) % 8
    return direcciones[indice]


def formatear_distancia(metros: float) -> str:
    """Devuelve metros si es menor a 1 km, o kilómetros con dos decimales."""
    if metros < 1000:
        return f"{metros:.0f} m"
    return f"{metros / 1000.0:.2f} km"


class GPSService:
    def __init__(self, page: ft.Page):
        self.page = page
        self.geolocator = None

        if fg is not None:
            self.geolocator = fg.Geolocator()
            if hasattr(self.page, "services"):
                self.page.services.append(self.geolocator)

    def disponible(self) -> bool:
        return self.geolocator is not None

    async def obtener_posicion_actual(self) -> dict:
        """
        Obtiene las coordenadas reales del chip GPS del teléfono sin requerir internet.
        Retorna dict con 'lat', 'lon' y 'precision'.
        """
        if self.geolocator is None:
            raise RuntimeError(
                "Instala 'flet-geolocator' (pip install flet-geolocator) para activar el chip GPS."
            )

        try:
            permiso = await self.geolocator.get_permission_status()
            if permiso in (
                fg.GeolocatorPermissionStatus.DENIED,
                fg.GeolocatorPermissionStatus.DENIED_FOREVER,
            ):
                permiso = await self.geolocator.request_permission()
                if permiso in (
                    fg.GeolocatorPermissionStatus.DENIED,
                    fg.GeolocatorPermissionStatus.DENIED_FOREVER,
                ):
                    raise PermissionError("Permiso de ubicación denegado en el teléfono.")
        except AttributeError:
            pass

        pos = await self.geolocator.get_current_position()
        return {
            "lat": round(pos.latitude, 6),
            "lon": round(pos.longitude, 6),
            "precision": round(getattr(pos, "accuracy", 0.0), 1),
        }
