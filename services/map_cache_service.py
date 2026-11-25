import os, math, shutil, urllib.request
try:
    from config import BASE_DIR
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class MapCacheService:
    def __init__(self, cache_dir: str = ""):
        self.cache_dir = cache_dir or os.path.join(BASE_DIR, "map_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def contar_cuadros(self) -> int:
        if not os.path.exists(self.cache_dir): return 0
        return sum(1 for _, _, fs in os.walk(self.cache_dir) for f in fs if f.endswith((".png", ".jpg", ".jpeg")))

    def contar_tiles(self) -> int:
        return self.contar_cuadros()

    def _latlon_a_tile(self, lat: float, lon: float, z: int) -> tuple[int, int]:
        rad = math.radians(max(-85.0511, min(85.0511, lat)))
        n = 2.0 ** z
        return int((lon + 180.0) / 360.0 * n), int((1.0 - math.asinh(math.tan(rad)) / math.pi) / 2.0 * n)

    def descargar_zona(self, lat: float, lon: float, zooms=(13, 14, 15), radio: int = 2) -> int:
        ok = 0
        for z in zooms:
            cx, cy = self._latlon_a_tile(lat, lon, z)
            for dx in range(-radio, radio + 1):
                for dy in range(-radio, radio + 1):
                    tx, ty = cx + dx, cy + dy
                    carpeta = os.path.join(self.cache_dir, str(z), str(tx))
                    os.makedirs(carpeta, exist_ok=True)
                    dest = os.path.join(carpeta, f"{ty}.jpg")
                    if os.path.exists(dest) and os.path.getsize(dest) > 0:
                        ok += 1; continue
                    url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{ty}/{tx}"
                    try:
                        req = urllib.request.Request(url, headers={"User-Agent": "BitacoraDeRio/1.0"})
                        with urllib.request.urlopen(req, timeout=6) as r:
                            data = r.read()
                            if data:
                                open(dest, "wb").write(data)
                                ok += 1
                    except Exception: pass
        return ok

    def descargar_area(self, lat: float, lon: float, zooms=(13, 14, 15), radio: int = 2) -> int:
        return self.descargar_zona(lat, lon, zooms, radio)

    def limpiar_cache(self):
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        os.makedirs(self.cache_dir, exist_ok=True)
