import ssl, json, socket, threading, urllib.request
from config import SYNC_API_URL, SYNC_API_KEY
from database.db_manager import DatabaseManager, CLUB_DEFAULT_ID

CANAL_DIRECTORIO = 'bitacora-rio-directorio-clubs-v1'

class SyncService:
    def __init__(self, db: DatabaseManager, on_status_change=None):
        self.db = db
        self.on_status_change = on_status_change
        self.on_chat_updated = None
        self._sincronizando = False

    def _ssl_ctx(self):
        return ssl._create_unverified_context()

    def obtener_canal_chat(self) -> str:
        return self.db.obtener_perfil().get('club_activo', CLUB_DEFAULT_ID)

    def hay_internet(self, timeout: float = 2.0) -> bool:
        for host in ('8.8.8.8', '1.1.1.1'):
            try:
                socket.create_connection((host, 53), timeout=timeout).close()
                return True
            except OSError: continue
        return False

    def sincronizar_en_segundo_plano(self):
        if self._sincronizando: return
        threading.Thread(target=self._ejecutar_sync, daemon=True).start()

    def _ejecutar_sync(self):
        self._sincronizando = True
        try:
            pendientes = self.db.contar_pendientes()
            if not self.hay_internet():
                self._notificar(f'Offline ({pendientes} pend.)' if pendientes > 0 else 'Modo Offline', False); return
            club_actual = self.obtener_canal_chat()
            msgs_pend = self.db.obtener_pendientes_tabla('mensajes_chat')
            if msgs_pend:
                self._publicar_msgs(msgs_pend)
                self.db.marcar_sincronizados('mensajes_chat', [m['uuid'] for m in msgs_pend])
            for c in self.db.obtener_clubes():
                if c.get('sync_status') != 1 and c.get('es_publico') == 1:
                    self._publicar_club(c)
            nuevos = self._descargar_msgs(club_actual)
            if nuevos: self.db.guardar_mensajes_remotos(nuevos)
            self._descargar_clubes_publicos()
            if self.on_chat_updated: self.on_chat_updated()
            self._notificar('En linea • Al dia', True)
        except Exception:
            self._notificar('Reintentando red...', False)
        finally:
            self._sincronizando = False

    def _publicar_msgs(self, mensajes: list[dict]):
        for m in mensajes:
            cid = m.get('club_id') or CLUB_DEFAULT_ID
            url = f'https://ntfy.sh/bitacora-club-{cid}'
            data = json.dumps({'uuid': m['uuid'], 'club_id': cid, 'remitente': m['remitente'], 'remitente_email': m.get('remitente_email', ''), 'mensaje': m['mensaje'], 'tipo': m.get('tipo', 'texto'), 'hora_local': m['hora_local'], 'updated_at': m['updated_at']}).encode('utf-8')
            urllib.request.urlopen(urllib.request.Request(url, data=data, headers={'Content-Type': 'text/plain; charset=utf-8'}, method='POST'), timeout=8, context=self._ssl_ctx()).close()

    def _descargar_msgs(self, club_id: str) -> list[dict]:
        url = f'https://ntfy.sh/bitacora-club-{club_id}/json?poll=1&since=24h'
        res = []
        with urllib.request.urlopen(urllib.request.Request(url, method='GET'), timeout=8, context=self._ssl_ctx()) as resp:
            for linea in resp.read().decode('utf-8', errors='ignore').splitlines():
                if not linea.strip(): continue
                try:
                    ev = json.loads(linea)
                    if ev.get('event') == 'message' and ev.get('message'):
                        d = json.loads(ev['message'])
                        if isinstance(d, dict) and 'mensaje' in d: res.append(d)
                except Exception: continue
        return res

    def _publicar_club(self, c: dict):
        url = f'https://ntfy.sh/{CANAL_DIRECTORIO}'
        data = json.dumps({'codigo': c['codigo'], 'nombre': c['nombre'], 'descripcion': c.get('descripcion', ''), 'admin_email': c['admin_email'], 'admin_nombre': c['admin_nombre'], 'es_publico': 1, 'anuncio': c.get('anuncio', ''), 'baneados': c.get('baneados', '')}).encode('utf-8')
        urllib.request.urlopen(urllib.request.Request(url, data=data, headers={'Content-Type': 'text/plain; charset=utf-8'}, method='POST'), timeout=8, context=self._ssl_ctx()).close()

    def _descargar_clubes_publicos(self):
        url = f'https://ntfy.sh/{CANAL_DIRECTORIO}/json?poll=1&since=72h'
        with urllib.request.urlopen(urllib.request.Request(url, method='GET'), timeout=8, context=self._ssl_ctx()) as resp:
            for linea in resp.read().decode('utf-8', errors='ignore').splitlines():
                if not linea.strip(): continue
                try:
                    ev = json.loads(linea)
                    if ev.get('event') == 'message' and ev.get('message'):
                        d = json.loads(ev['message'])
                        if isinstance(d, dict) and 'codigo' in d and 'nombre' in d:
                            self.db.crear_o_actualizar_club(d['codigo'], d['nombre'], d.get('descripcion', ''), d.get('admin_email', ''), d.get('admin_nombre', 'Admin'), 1, d.get('anuncio', ''), d.get('baneados', ''), 1)
                except Exception: continue

    def _notificar(self, mensaje: str, exito: bool):
        if self.on_status_change: self.on_status_change(mensaje, exito)
