import os
import math
import zlib
import struct
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from config import MAP_CACHE_DIR

URLS_BASE = {
    "satelite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "calle": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
}


def _generar_tile_oscuro_png() -> bytes:
    """Genera un cuadro PNG 256x256 oscuro en Python puro para zonas sin caché offline."""
    ancho, alto = 256, 256
    # Color #131622 (RGB: 19, 22, 34)
    fila = b"\x00" + (b"\x13\x16\x22" * ancho)
    raw = fila * alto

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack("!I", len(data))
            + tag
            + data
            + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack("!IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, level=1))
        + chunk(b"IEND", b"")
    )


TILE_VACIO_PNG = _generar_tile_oscuro_png()


def coord_a_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def descargar_tile_individual(estilo: str, z: int, x: int, y: int) -> bytes | None:
    if estilo not in URLS_BASE:
        return None

    ruta_archivo = os.path.join(MAP_CACHE_DIR, estilo, str(z), str(x), f"{y}.png")
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, "rb") as f:
            return f.read()

    url = URLS_BASE[estilo].format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers={"User-Agent": "BitacoraRioApp/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            if resp.status == 200:
                datos = resp.read()
                os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
                with open(ruta_archivo, "wb") as f:
                    f.write(datos)
                return datos
    except Exception:
        return None
    return None


class _TileRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Ruta esperada: /{estilo}/{z}/{x}/{y}.png
        partes = self.path.strip("/").split("/")
        if len(partes) != 4 or not partes[3].endswith(".png"):
            self.send_response(404)
            self.end_headers()
            return

        estilo = partes[0]
        try:
            z = int(partes[1])
            x = int(partes[2])
            y = int(partes[3].replace(".png", ""))
        except ValueError:
            self.send_response(400)
            self.end_headers()
            return

        datos = descargar_tile_individual(estilo, z, x, y)
        if datos is None:
            datos = TILE_VACIO_PNG

        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, format, *args):
        pass  # Silencia logs en consola


class MapCacheService:
    def __init__(self):
        os.makedirs(MAP_CACHE_DIR, exist_ok=True)
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _TileRequestHandler)
        self.puerto = self._server.server_address[1]
        self._hilo = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._hilo.start()
        self.descargando = False

    def obtener_url_template(self, modo_satelite: bool) -> str:
        estilo = "satelite" if modo_satelite else "calle"
        return f"http://127.0.0.1:{self.puerto}/{estilo}/{{z}}/{{x}}/{{y}}.png"

    def contar_tiles_cacheados(self) -> int:
        total = 0
        if not os.path.exists(MAP_CACHE_DIR):
            return 0
        for _, _, archivos in os.walk(MAP_CACHE_DIR):
            total += sum(1 for a in archivos if a.endswith(".png"))
        return total

    def descargar_zona_offline(
        self,
        lat_centro: float,
        lon_centro: float,
        radio_km: float = 3.0,
        zooms: tuple[int, ...] = (12, 13, 14, 15),
        on_progreso=None,
    ):
        if self.descargando:
            return

        def _tarea():
            self.descargando = True
            try:
                delta_lat = radio_km / 111.0
                delta_lon = radio_km / (111.0 * max(0.1, math.cos(math.radians(lat_centro))))

                lista_tiles = []
                for z in zooms:
                    x1, y1 = coord_a_tile(lat_centro + delta_lat, lon_centro - delta_lon, z)
                    x2, y2 = coord_a_tile(lat_centro - delta_lat, lon_centro + delta_lon, z)
                    for x in range(min(x1, x2), max(x1, x2) + 1):
                        for y in range(min(y1, y2), max(y1, y2) + 1):
                            lista_tiles.append(("satelite", z, x, y))

                total = len(lista_tiles)
                for idx, (estilo, z, x, y) in enumerate(lista_tiles, start=1):
                    descargar_tile_individual(estilo, z, x, y)
                    if on_progreso and (idx % 5 == 0 or idx == total):
                        on_progreso(idx, total, False)

                if on_progreso:
                    on_progreso(total, total, True)
            finally:
                self.descargando = False

        threading.Thread(target=_tarea, daemon=True).start()
