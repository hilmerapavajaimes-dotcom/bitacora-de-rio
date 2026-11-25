import asyncio, http.server, inspect, re, socketserver, threading, urllib.parse, webbrowser
import flet as ft
from config import DEFAULT_LAT, DEFAULT_LON
HTML_TPL = '<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1></head><body style=background:#0D0E15;color:#F8FAFC;font-family:sans-serif;text-align:center;padding:30px><h2 id=t style=color:#10B981>Obteniendo GPS...</h2><p id=m>Acepta el permiso de ubicacion.</p><script>navigator.geolocation.getCurrentPosition(function(p){var a=p.coords.latitude.toFixed(6),b=p.coords.longitude.toFixed(6),c=Math.round(p.coords.accuracy||10);fetch(String.fromCharCode(47,112,111,115,63,108,97,116,61)+a+String.fromCharCode(38,108,111,110,61)+b+String.fromCharCode(38,97,99,99,61)+c).then(function(){t.innerText=String.fromCharCode(71,80,83,32,101,110,118,105,97,100,111,33);m.innerText=a+String.fromCharCode(44,32)+b+String.fromCharCode(32,45,32,86,117,101,108,118,101,32,97,32,108,97,32,97,112,112);});},function(){t.innerText=String.fromCharCode(65,99,116,105,118,97,32,101,108,32,71,80,83);},{enableHighAccuracy:true,timeout:12000});</script></body></html>'
class GPSService:
    def __init__(self, page: ft.Page): self.page = page
    @staticmethod
    def extraer_coordenadas(texto: str):
        m = re.search(r'(-?\d{1,2}\.\d{3,})\s*[,;\s]\s*(-?\d{1,3}\.\d{3,})', texto or '')
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180: return round(lat, 6), round(lon, 6)
        return None
    async def obtener_posicion_actual(self) -> dict:
        res, ev = {}, threading.Event()
        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_GET(self):
                u = urllib.parse.urlparse(self.path)
                if u.path == '/pos':
                    q = urllib.parse.parse_qs(u.query)
                    res['lat'], res['lon'], res['precision'] = round(float(q['lat'][0]), 6), round(float(q['lon'][0]), 6), round(float(q.get('acc', ['10'])[0]), 1)
                    ev.set(); self.send_response(200); self.end_headers(); self.wfile.write(b'OK')
                else:
                    b = HTML_TPL.encode('utf-8'); self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers(); self.wfile.write(b)
        srv = socketserver.TCPServer(('127.0.0.1', 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            r = self.page.launch_url(f'http://127.0.0.1:{srv.server_address[1]}/')
            if inspect.iscoroutine(r): await r
            if await asyncio.to_thread(ev.wait, 16.0) and 'lat' in res: return res
            raise RuntimeError('Sin respuesta GPS')
        finally:
            srv.shutdown(); srv.server_close()
