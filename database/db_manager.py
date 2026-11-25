import sqlite3
import uuid
from datetime import datetime, timezone
from config import DB_PATH, DEFAULT_PESCADOR


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._inicializar_tablas()

    def _conectar(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ahora_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _inicializar_tablas(self):
        with self._conectar() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS capturas (
                    uuid TEXT PRIMARY KEY,
                    pescador TEXT DEFAULT 'Ilmer',
                    especie TEXT NOT NULL,
                    peso_kg REAL DEFAULT 0,
                    senuelo TEXT,
                    color_senuelo TEXT DEFAULT '',
                    estructura TEXT DEFAULT '',
                    hora_captura TEXT DEFAULT '',
                    estado_rio TEXT,
                    foto_ficha TEXT DEFAULT '',
                    notas TEXT,
                    privacidad TEXT DEFAULT 'club',
                    sync_status INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)

            columnas_existentes = {
                fila[1] for fila in cursor.execute("PRAGMA table_info(capturas)").fetchall()
            }
            nuevas_cols = {
                "pescador": f"TEXT DEFAULT '{DEFAULT_PESCADOR}'",
                "color_senuelo": "TEXT DEFAULT ''",
                "estructura": "TEXT DEFAULT ''",
                "hora_captura": "TEXT DEFAULT ''",
                "foto_ficha": "TEXT DEFAULT ''",
            }
            for col, tipo in nuevas_cols.items():
                if col not in columnas_existentes:
                    cursor.execute(f"ALTER TABLE capturas ADD COLUMN {col} {tipo}")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pesqueros (
                    uuid TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    latitud REAL NOT NULL,
                    longitud REAL NOT NULL,
                    referencia TEXT,
                    privacidad TEXT DEFAULT 'privado',
                    sync_status INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reporte_rio (
                    uuid TEXT PRIMARY KEY,
                    nivel TEXT NOT NULL,
                    claridad TEXT NOT NULL,
                    zona TEXT,
                    sync_status INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gastos_salida (
                    uuid TEXT PRIMARY KEY,
                    concepto TEXT NOT NULL,
                    pagado_por TEXT NOT NULL,
                    monto REAL NOT NULL,
                    sync_status INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mensajes_chat (
                    uuid TEXT PRIMARY KEY,
                    remitente TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    tipo TEXT DEFAULT 'texto',
                    hora_local TEXT NOT NULL,
                    sync_status INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    # --- CAPTURAS TÁCTICAS ---
    def registrar_captura(
        self,
        especie: str,
        peso_kg: float,
        senuelo: str,
        estado_rio: str,
        pescador: str = DEFAULT_PESCADOR,
        color_senuelo: str = "",
        estructura: str = "",
        hora_captura: str = "",
        foto_ficha: str = "",
        notas: str = "",
        privacidad: str = "club",
    ) -> str:
        nuevo_id = str(uuid.uuid4())
        if not hora_captura:
            hora_captura = datetime.now().strftime("%H:%M")

        with self._conectar() as conn:
            conn.execute(
                """
                INSERT INTO capturas 
                (uuid, pescador, especie, peso_kg, senuelo, color_senuelo, estructura,
                 hora_captura, estado_rio, foto_ficha, notas, privacidad, sync_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    nuevo_id,
                    pescador.strip() or DEFAULT_PESCADOR,
                    especie,
                    peso_kg,
                    senuelo,
                    color_senuelo,
                    estructura,
                    hora_captura,
                    estado_rio,
                    foto_ficha,
                    notas,
                    privacidad,
                    self._ahora_iso(),
                ),
            )
            conn.commit()
        return nuevo_id

    def obtener_capturas(self, limite: int = 20) -> list[dict]:
        with self._conectar() as conn:
            filas = conn.execute(
                "SELECT * FROM capturas ORDER BY updated_at DESC LIMIT ?",
                (limite,),
            ).fetchall()
            return [dict(f) for f in filas]

    def obtener_estadisticas(self) -> dict:
        with self._conectar() as conn:
            total = conn.execute("SELECT COUNT(*) FROM capturas").fetchone()[0]
            mayor = conn.execute(
                "SELECT especie, peso_kg, pescador FROM capturas ORDER BY peso_kg DESC LIMIT 1"
            ).fetchone()
            top_senuelo = conn.execute(
                "SELECT senuelo, COUNT(*) as c FROM capturas WHERE senuelo != '' GROUP BY senuelo ORDER BY c DESC LIMIT 1"
            ).fetchone()
            top_color = conn.execute(
                "SELECT color_senuelo, COUNT(*) as c FROM capturas WHERE color_senuelo != '' GROUP BY color_senuelo ORDER BY c DESC LIMIT 1"
            ).fetchone()
            top_estructura = conn.execute(
                "SELECT estructura, COUNT(*) as c FROM capturas WHERE estructura != '' GROUP BY estructura ORDER BY c DESC LIMIT 1"
            ).fetchone()
            top_especie = conn.execute(
                "SELECT especie, COUNT(*) as c FROM capturas GROUP BY especie ORDER BY c DESC LIMIT 1"
            ).fetchone()
            top_hora = conn.execute(
                "SELECT substr(hora_captura, 1, 2) as h, COUNT(*) as c FROM capturas WHERE hora_captura != '' GROUP BY h ORDER BY c DESC LIMIT 1"
            ).fetchone()

            hora_str = f"{top_hora['h']}:00 - {top_hora['h']}:59" if top_hora and top_hora["h"] else "Sin datos"

            return {
                "total_capturas": total,
                "record_especie": mayor["especie"] if mayor else "—",
                "record_peso": mayor["peso_kg"] if mayor else 0.0,
                "record_pescador": mayor["pescador"] if mayor else "—",
                "mejor_senuelo": top_senuelo["senuelo"] if top_senuelo else "Sin datos",
                "mejor_color": top_color["color_senuelo"] if top_color else "Sin datos",
                "mejor_estructura": top_estructura["estructura"] if top_estructura else "Sin datos",
                "mejor_hora": hora_str,
                "especie_frecuente": top_especie["especie"] if top_especie else "Sin datos",
            }

    def obtener_ranking_club(self) -> dict:
        with self._conectar() as conn:
            records_especie = conn.execute(
                """
                SELECT especie, MAX(peso_kg) as max_peso, pescador, senuelo
                FROM capturas
                GROUP BY especie
                ORDER BY max_peso DESC
                """
            ).fetchall()

            tabla_pescadores = conn.execute(
                """
                SELECT pescador, COUNT(*) as total, ROUND(SUM(peso_kg), 2) as kilos_totales
                FROM capturas
                GROUP BY pescador
                ORDER BY kilos_totales DESC, total DESC
                """
            ).fetchall()

            return {
                "records_especie": [dict(r) for r in records_especie],
                "tabla_pescadores": [dict(p) for p in tabla_pescadores],
            }

    # --- PESQUEROS GPS ---
    def registrar_pesquero(
        self,
        nombre: str,
        latitud: float,
        longitud: float,
        referencia: str = "",
        privacidad: str = "privado",
    ) -> str:
        nuevo_id = str(uuid.uuid4())
        with self._conectar() as conn:
            conn.execute(
                """
                INSERT INTO pesqueros
                (uuid, nombre, latitud, longitud, referencia, privacidad, sync_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    nuevo_id,
                    nombre,
                    latitud,
                    longitud,
                    referencia,
                    privacidad,
                    self._ahora_iso(),
                ),
            )
            conn.commit()
        return nuevo_id

    def obtener_pesqueros(self) -> list[dict]:
        with self._conectar() as conn:
            filas = conn.execute(
                "SELECT * FROM pesqueros ORDER BY updated_at DESC"
            ).fetchall()
            return [dict(f) for f in filas]

    # --- ESTADO DEL RÍO ---
    def registrar_estado_rio(self, nivel: str, claridad: str, zona: str = "General"):
        nuevo_id = str(uuid.uuid4())
        with self._conectar() as conn:
            conn.execute(
                """
                INSERT INTO reporte_rio (uuid, nivel, claridad, zona, sync_status, updated_at)
                VALUES (?, ?, ?, ?, 0, ?)
                """,
                (nuevo_id, nivel, claridad, zona, self._ahora_iso()),
            )
            conn.commit()

    def obtener_ultimo_estado_rio(self) -> dict | None:
        with self._conectar() as conn:
            fila = conn.execute(
                "SELECT * FROM reporte_rio ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
            return dict(fila) if fila else None

    # --- LA "VACA" (GASTOS DE SALIDA) ---
    def registrar_gasto(self, concepto: str, pagado_por: str, monto: float):
        nuevo_id = str(uuid.uuid4())
        with self._conectar() as conn:
            conn.execute(
                """
                INSERT INTO gastos_salida (uuid, concepto, pagado_por, monto, sync_status, updated_at)
                VALUES (?, ?, ?, ?, 0, ?)
                """,
                (nuevo_id, concepto.strip(), pagado_por.strip(), monto, self._ahora_iso()),
            )
            conn.commit()

    def obtener_gastos(self) -> list[dict]:
        with self._conectar() as conn:
            filas = conn.execute(
                "SELECT * FROM gastos_salida ORDER BY updated_at DESC"
            ).fetchall()
            return [dict(f) for f in filas]

    def limpiar_gastos(self):
        with self._conectar() as conn:
            conn.execute("DELETE FROM gastos_salida")
            conn.commit()

    # --- CHAT DEL CLUB (OFFLINE-FIRST + SYNC EN LÍNEA) ---
    def registrar_mensaje_chat(self, remitente: str, mensaje: str, tipo: str = "texto") -> str:
        nuevo_id = str(uuid.uuid4())
        hora_local = datetime.now().strftime("%H:%M")
        with self._conectar() as conn:
            conn.execute(
                """
                INSERT INTO mensajes_chat (uuid, remitente, mensaje, tipo, hora_local, sync_status, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    nuevo_id,
                    remitente.strip() or DEFAULT_PESCADOR,
                    mensaje.strip(),
                    tipo,
                    hora_local,
                    self._ahora_iso(),
                ),
            )
            conn.commit()
        return nuevo_id

    def obtener_mensajes_chat(self, limite: int = 60) -> list[dict]:
        with self._conectar() as conn:
            filas = conn.execute(
                """
                SELECT * FROM (
                    SELECT * FROM mensajes_chat ORDER BY updated_at DESC LIMIT ?
                ) ORDER BY updated_at ASC
                """,
                (limite,),
            ).fetchall()
            return [dict(f) for f in filas]

    def guardar_mensajes_remotos(self, mensajes: list[dict]):
        if not mensajes:
            return
        with self._conectar() as conn:
            for m in mensajes:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO mensajes_chat
                    (uuid, remitente, mensaje, tipo, hora_local, sync_status, updated_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        m.get("uuid", str(uuid.uuid4())),
                        m.get("remitente", "Compañero"),
                        m.get("mensaje", ""),
                        m.get("tipo", "texto"),
                        m.get("hora_local", "--:--"),
                        m.get("updated_at", self._ahora_iso()),
                    ),
                )
            conn.commit()

    # --- SINCRONIZACIÓN ---
    def contar_pendientes(self) -> int:
        total = 0
        with self._conectar() as conn:
            for tabla in ("capturas", "pesqueros", "reporte_rio", "mensajes_chat"):
                cnt = conn.execute(
                    f"SELECT COUNT(*) FROM {tabla} WHERE sync_status != 1"
                ).fetchone()[0]
                total += cnt
        return total

    def obtener_pendientes_tabla(self, tabla: str) -> list[dict]:
        with self._conectar() as conn:
            filas = conn.execute(
                f"SELECT * FROM {tabla} WHERE sync_status != 1"
            ).fetchall()
            return [dict(f) for f in filas]

    def marcar_sincronizados(self, tabla: str, uuids: list[str]):
        if not uuids:
            return
        with self._conectar() as conn:
            marcadores = ",".join("?" for _ in uuids)
            conn.execute(
                f"UPDATE {tabla} SET sync_status = 1 WHERE uuid IN ({marcadores})",
                uuids,
            )
            conn.commit()
