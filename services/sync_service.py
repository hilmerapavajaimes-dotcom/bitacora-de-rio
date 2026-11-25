import ssl, json, time, threading, urllib.request
from database.db_manager import DatabaseManager, CLUB_DEFAULT_ID
CANAL_DIRECTORIO = 'bitacora-rio-directorio-clubs-v1'
class SyncService:
    def __init__(self, db: DatabaseManager, on_status_change=None):
        self.db = db
        self.on_status_change = on_status_change
        self.on_chat_updated = None
        self.esta_online = True
        self._enviando = False
        self._sync_dir = False
        self._stream_club = None
        self._stream_resp = None
        threading.Thread(target=self._bucle_stream, daemon=True).start()
    def _ssl_ctx(self): return ssl._create_unverified_context()
    def obtener_canal_chat(self) -> str: return self.db.obtener_perfil().get('club_activo', CLUB_DEFAULT_ID)
    def hay_internet(self, timeout: float = 1.5) -> bool: return self.esta_online
    def reiniciar_stream_chat(self):
        self._stream_club = None
        try:
            if self._stream_resp: self._stream_resp.close()
        except Exception: pass
    def _bucle_stream(self):
        while True:
            cid = self.obtener_canal_chat()
            self._stream_club = cid
            url = f'https://ntfy.sh/bitacora-club-{cid}/json?since=30m'
            try:
                req = urllib.request.Request(url, headers={'Accept': 'application/x-ndjson'})
                with urllib.request.urlopen(req, timeout=35, context=self._ssl_ctx()) as resp:
                    self._stream_resp, self.esta_online = resp, True
                    self._notificar('En linea • Tiempo real', True)
                    for raw in resp:
                        if self._stream_club != cid: break
                        linea = raw.decode('utf-8', errors='ignore').strip()
                        if not linea: continue
                        ev = json.loads(linea)
                        if ev.get('event') == 'message' and ev.get('message'):
                            d = json.loads(ev['message'])
                            if isinstance(d, dict) and 'mensaje' in d:
                                self.db.guardar_mensajes_remotos([d])
                                if self.on_chat_updated: self.on_chat_updated()
            except Exception:
                if self._stream_club == cid:
                    self.esta_online = False
                    self._notificar('Sin senal • Modo Offline', False)
                    time.sleep(3)
    def sincronizar_en_segundo_plano(self, incluir_clubes: bool = False):
        if not self._enviando: threading.Thread(target=self._enviar_cola_rapida, daemon=True).start()
        if incluir_clubes and not self._sync_dir: threading.Thread(target=self._sincronizar_directorio, daemon=True).start()
    def _enviar_cola_rapida(self):
        self._enviando = True
        try:
            msgs = self.db.obtener_pendientes_tabla('mensajes_chat')
            for m in msgs:
                cid = m.get('club_id') or CLUB_DEFAULT_ID
                data = json.dumps({'uuid': m['uuid'], 'club_id': cid, 'remitente': m['remitente'], 'remitente_email': m.get('remitente_email', ''), 'mensaje': m['mensaje'], 'tipo': m.get('tipo', 'texto'), 'hora_local': m['hora_local'], 'updated_at': m['updated_at']}).encode('utf-8')
                urllib.request.urlopen(urllib.request.Request(f'https://ntfy.sh/bitacora-club-{cid}', data=data, headers={'Content-Type': 'text/plain; charset=utf-8'}, method='POST'), timeout=5, context=self._ssl_ctx()).close()
                self.db.marcar_sincronizados('mensajes_chat', [m['uuid']])
            self.esta_online = True
            if msgs and self.on_chat_updated: self.on_chat_updated()
            self._notificar('En linea • Tiempo real', True)
        except Exception:
            self.esta_online = False
            p = self.db.contar_pendientes()
            self._notificar(f'Offline ({p} pend.)' if p > 0 else 'Modo Offline', False)
        finally: self._enviando = False
    def _sincronizar_directorio(self):
        self._sync_dir = True
        try:
            for c in self.db.obtener_clubes():
                if c.get('sync_status') != 1 and c.get('es_publico') == 1:
                    data = json.dumps({'codigo': c['codigo'], 'nombre': c['nombre'], 'descripcion': c.get('descripcion', ''), 'admin_email': c['admin_email'], 'admin_nombre': c['admin_nombre'], 'es_publico': 1, 'anuncio': c.get('anuncio', ''), 'baneados': c.get('baneados', '')}).encode('utf-8')
                    urllib.request.urlopen(urllib.request.Request(f'https://ntfy.sh/{CANAL_DIRECTORIO}', data=data, headers={'Content-Type': 'text/plain; charset=utf-8'}, method='POST'), timeout=5, context=self._ssl_ctx()).close()
                    self.db.crear_o_actualizar_club(c['codigo'], c['nombre'], c.get('descripcion', ''), c['admin_email'], c['admin_nombre'], 1, c.get('anuncio', ''), c.get('baneados', ''), 1)
            with urllib.request.urlopen(urllib.request.Request(f'https://ntfy.sh/{CANAL_DIRECTORIO}/json?poll=1&since=48h', method='GET'), timeout=6, context=self._ssl_ctx()) as resp:
                for linea in resp.read().decode('utf-8', errors='ignore').splitlines():
                    if not linea.strip(): continue
                    ev = json.loads(linea)
                    if ev.get('event') == 'message' and ev.get('message'):
                        d = json.loads(ev['message'])
                        if isinstance(d, dict) and 'codigo' in d and 'nombre' in d:
                            self.db.crear_o_actualizar_club(d['codigo'], d['nombre'], d.get('descripcion', ''), d.get('admin_email', ''), d.get('admin_nombre', 'Admin'), 1, d.get('anuncio', ''), d.get('baneados', ''), 1)
        except Exception: pass
        finally: self._sync_dir = False
    def _notificar(self, mensaje: str, exito: bool):
        if self.on_status_change: self.on_status_change(mensaje, exito)
