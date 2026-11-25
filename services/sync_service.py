import json
import socket
import threading
import urllib.request
from config import SYNC_API_URL, SYNC_API_KEY
from database.db_manager import DatabaseManager


class SyncService:
    def __init__(self, db: DatabaseManager, on_status_change=None):
        self.db = db
        self.on_status_change = on_status_change
        self.on_chat_updated = None
        self._sincronizando = False

    def hay_internet(self, timeout: float = 2.0) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=timeout).close()
            return True
        except OSError:
            return False

    def sincronizar_en_segundo_plano(self):
        if self._sincronizando:
            return
        hilo = threading.Thread(target=self._ejecutar_sync, daemon=True)
        hilo.start()

    def _ejecutar_sync(self):
        self._sincronizando = True
        try:
            pendientes = self.db.contar_pendientes()
            en_linea = self.hay_internet()

            if not en_linea:
                if pendientes > 0:
                    self._notificar(f"Offline ({pendientes} pend.)", False)
                else:
                    self._notificar("Modo Offline", False)
                return

            # 1. Subir registros pendientes de todas las tablas
            tablas = ["capturas", "pesqueros", "reporte_rio", "mensajes_chat"]
            for tabla in tablas:
                registros = self.db.obtener_pendientes_tabla(tabla)
                if not registros:
                    continue

                if SYNC_API_URL:
                    self._enviar_a_nube(tabla, registros)

                uuids = [r["uuid"] for r in registros]
                self.db.marcar_sincronizados(tabla, uuids)

            # 2. Descargar mensajes nuevos del chat del club si hay backend configurado
            if SYNC_API_URL:
                nuevos_msgs = self._descargar_chat_nube()
                if nuevos_msgs:
                    self.db.guardar_mensajes_remotos(nuevos_msgs)

            if self.on_chat_updated:
                self.on_chat_updated()

            self._notificar("En línea • Al día", True)
        except Exception as e:
            self._notificar(f"Error sync: {e}", False)
        finally:
            self._sincronizando = False

    def _enviar_a_nube(self, tabla: str, registros: list[dict]):
        url = f"{SYNC_API_URL.rstrip('/')}/{tabla}"
        datos = json.dumps(registros).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "apikey": SYNC_API_KEY,
            "Authorization": f"Bearer {SYNC_API_KEY}",
            "Prefer": "resolution=merge-duplicates",
        }
        req = urllib.request.Request(url, data=datos, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 201, 204):
                raise RuntimeError(f"HTTP {resp.status}")

    def _descargar_chat_nube(self) -> list[dict]:
        url = f"{SYNC_API_URL.rstrip('/')}/mensajes_chat?select=*&order=updated_at.desc&limit=50"
        headers = {
            "apikey": SYNC_API_KEY,
            "Authorization": f"Bearer {SYNC_API_KEY}",
        }
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
        return []

    def _notificar(self, mensaje: str, exito: bool):
        if self.on_status_change:
            self.on_status_change(mensaje, exito)
