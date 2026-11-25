import sqlite3, uuid
from datetime import datetime, timezone
from config import DB_PATH, DEFAULT_PESCADOR

CLUB_DEFAULT_ID = 'lospanemas-orinoco-2026'

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
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS capturas (uuid TEXT PRIMARY KEY, pescador TEXT, especie TEXT NOT NULL, peso_kg REAL DEFAULT 0, senuelo TEXT, color_senuelo TEXT, estructura TEXT, hora_captura TEXT, estado_rio TEXT, foto_ficha TEXT, notas TEXT, privacidad TEXT DEFAULT 'club', sync_status INTEGER DEFAULT 0, updated_at TEXT NOT NULL)''')
            cols_cap = {f[1] for f in c.execute('PRAGMA table_info(capturas)').fetchall()}
            for col in ('pescador', 'color_senuelo', 'estructura', 'hora_captura', 'foto_ficha'):
                if col not in cols_cap: c.execute(f'ALTER TABLE capturas ADD COLUMN {col} TEXT')
            c.execute('''CREATE TABLE IF NOT EXISTS pesqueros (uuid TEXT PRIMARY KEY, nombre TEXT NOT NULL, latitud REAL NOT NULL, longitud REAL NOT NULL, referencia TEXT, privacidad TEXT DEFAULT 'privado', sync_status INTEGER DEFAULT 0, updated_at TEXT NOT NULL)''')
            c.execute('''CREATE TABLE IF NOT EXISTS reporte_rio (uuid TEXT PRIMARY KEY, nivel TEXT NOT NULL, claridad TEXT NOT NULL, zona TEXT, sync_status INTEGER DEFAULT 0, updated_at TEXT NOT NULL)''')
            c.execute('''CREATE TABLE IF NOT EXISTS gastos_salida (uuid TEXT PRIMARY KEY, concepto TEXT NOT NULL, pagado_por TEXT NOT NULL, monto REAL NOT NULL, sync_status INTEGER DEFAULT 0, updated_at TEXT NOT NULL)''')
            c.execute('''CREATE TABLE IF NOT EXISTS mensajes_chat (uuid TEXT PRIMARY KEY, club_id TEXT, remitente TEXT NOT NULL, remitente_email TEXT, mensaje TEXT NOT NULL, tipo TEXT DEFAULT 'texto', hora_local TEXT NOT NULL, sync_status INTEGER DEFAULT 0, updated_at TEXT NOT NULL)''')
            cols_msg = {f[1] for f in c.execute('PRAGMA table_info(mensajes_chat)').fetchall()}
            if 'club_id' not in cols_msg: c.execute('ALTER TABLE mensajes_chat ADD COLUMN club_id TEXT')
            if 'remitente_email' not in cols_msg: c.execute('ALTER TABLE mensajes_chat ADD COLUMN remitente_email TEXT')
            c.execute('UPDATE mensajes_chat SET club_id = ? WHERE club_id IS NULL', (CLUB_DEFAULT_ID,))
            c.execute('''CREATE TABLE IF NOT EXISTS clubes (codigo TEXT PRIMARY KEY, nombre TEXT NOT NULL, descripcion TEXT, admin_email TEXT NOT NULL, admin_nombre TEXT NOT NULL, es_publico INTEGER DEFAULT 1, anuncio TEXT, baneados TEXT, sync_status INTEGER DEFAULT 0, updated_at TEXT NOT NULL)''')
            c.execute('''CREATE TABLE IF NOT EXISTS perfil_usuario (id INTEGER PRIMARY KEY CHECK (id = 1), nombre TEXT NOT NULL, email TEXT, proveedor TEXT DEFAULT 'local', club_activo TEXT, bio TEXT, updated_at TEXT NOT NULL)''')
            c.execute('INSERT OR IGNORE INTO clubes (codigo, nombre, descripcion, admin_email, admin_nombre, es_publico, anuncio, baneados, sync_status, updated_at) VALUES (?, ?, ?, ?, ?, 1, ?, ?, 1, ?)', (CLUB_DEFAULT_ID, 'Club Los Panemas', 'Pesca deportiva en el Rio Orinoco y Cataniapo', 'hilmerapavajaimes@gmail.com', DEFAULT_PESCADOR, 'Bienvenidos al canal oficial del club!', '', self._ahora_iso()))
            c.execute('INSERT OR IGNORE INTO perfil_usuario (id, nombre, email, proveedor, club_activo, bio, updated_at) VALUES (1, ?, ?, ?, ?, ?, ?)', (DEFAULT_PESCADOR, '', 'local', CLUB_DEFAULT_ID, 'Pescador de rio', self._ahora_iso()))
            conn.commit()
    def obtener_perfil(self) -> dict:
        with self._conectar() as conn:
            f = conn.execute('SELECT * FROM perfil_usuario WHERE id = 1').fetchone()
            return dict(f) if f else {'nombre': DEFAULT_PESCADOR, 'email': '', 'proveedor': 'local', 'club_activo': CLUB_DEFAULT_ID, 'bio': ''}

    def guardar_perfil(self, nombre: str, email: str, proveedor: str = 'google', bio: str = ''):
        with self._conectar() as conn:
            conn.execute('UPDATE perfil_usuario SET nombre=?, email=?, proveedor=?, bio=?, updated_at=? WHERE id=1', (nombre.strip() or DEFAULT_PESCADOR, email.strip().lower(), proveedor, bio.strip(), self._ahora_iso()))
            conn.commit()

    def cambiar_club_activo(self, codigo: str):
        with self._conectar() as conn:
            conn.execute('UPDATE perfil_usuario SET club_activo=?, updated_at=? WHERE id=1', (codigo.strip(), self._ahora_iso()))
            conn.commit()

    def crear_o_actualizar_club(self, codigo: str, nombre: str, descripcion: str, admin_email: str, admin_nombre: str, es_publico: int = 1, anuncio: str = '', baneados: str = '', sync_status: int = 0):
        with self._conectar() as conn:
            conn.execute('INSERT INTO clubes (codigo, nombre, descripcion, admin_email, admin_nombre, es_publico, anuncio, baneados, sync_status, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(codigo) DO UPDATE SET nombre=excluded.nombre, descripcion=excluded.descripcion, es_publico=excluded.es_publico, anuncio=excluded.anuncio, baneados=excluded.baneados, sync_status=excluded.sync_status, updated_at=excluded.updated_at', (codigo, nombre, descripcion, admin_email.lower(), admin_nombre, es_publico, anuncio, baneados, sync_status, self._ahora_iso()))
            conn.commit()

    def obtener_clubes(self) -> list[dict]:
        with self._conectar() as conn:
            return [dict(f) for f in conn.execute('SELECT * FROM clubes ORDER BY updated_at DESC').fetchall()]

    def obtener_club(self, codigo: str) -> dict | None:
        with self._conectar() as conn:
            f = conn.execute('SELECT * FROM clubes WHERE codigo=?', (codigo,)).fetchone()
            return dict(f) if f else None

    def registrar_captura(self, especie: str, peso_kg: float, senuelo: str, estado_rio: str, pescador: str = '', color_senuelo: str = '', estructura: str = '', hora_captura: str = '', foto_ficha: str = '', notas: str = '', privacidad: str = 'club') -> str:
        nuevo_id = str(uuid.uuid4())
        if not pescador: pescador = self.obtener_perfil().get('nombre', DEFAULT_PESCADOR)
        if not hora_captura: hora_captura = datetime.now().strftime('%H:%M')
        with self._conectar() as conn:
            conn.execute('INSERT INTO capturas (uuid, pescador, especie, peso_kg, senuelo, color_senuelo, estructura, hora_captura, estado_rio, foto_ficha, notas, privacidad, sync_status, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0,?)', (nuevo_id, pescador, especie, peso_kg, senuelo, color_senuelo, estructura, hora_captura, estado_rio, foto_ficha, notas, privacidad, self._ahora_iso()))
            conn.commit()
        return nuevo_id

    def obtener_capturas(self, limite: int = 20) -> list[dict]:
        with self._conectar() as conn:
            return [dict(f) for f in conn.execute('SELECT * FROM capturas ORDER BY updated_at DESC LIMIT ?', (limite,)).fetchall()]

    def obtener_estadisticas(self) -> dict:
        with self._conectar() as conn:
            total = conn.execute('SELECT COUNT(*) FROM capturas').fetchone()[0]
            mayor = conn.execute('SELECT especie, peso_kg, pescador FROM capturas ORDER BY peso_kg DESC LIMIT 1').fetchone()
            top_s = conn.execute('SELECT senuelo, COUNT(*) c FROM capturas WHERE LENGTH(senuelo) > 0 GROUP BY senuelo ORDER BY c DESC LIMIT 1').fetchone()
            top_c = conn.execute('SELECT color_senuelo, COUNT(*) c FROM capturas WHERE LENGTH(color_senuelo) > 0 GROUP BY color_senuelo ORDER BY c DESC LIMIT 1').fetchone()
            top_e = conn.execute('SELECT estructura, COUNT(*) c FROM capturas WHERE LENGTH(estructura) > 0 GROUP BY estructura ORDER BY c DESC LIMIT 1').fetchone()
            top_h = conn.execute('SELECT substr(hora_captura,1,2) h, COUNT(*) c FROM capturas WHERE LENGTH(hora_captura) > 0 GROUP BY h ORDER BY c DESC LIMIT 1').fetchone()
            hora_str = (top_h['h'] + ':00') if (top_h and top_h['h']) else 'Sin datos'
            return {'total_capturas': total, 'record_especie': mayor['especie'] if mayor else '-', 'record_peso': mayor['peso_kg'] if mayor else 0.0, 'mejor_senuelo': top_s['senuelo'] if top_s else 'Sin datos', 'mejor_color': top_c['color_senuelo'] if top_c else 'Sin datos', 'mejor_estructura': top_e['estructura'] if top_e else 'Sin datos', 'mejor_hora': hora_str}
    def obtener_ranking_club(self) -> dict:
        with self._conectar() as conn:
            rec = conn.execute('SELECT especie, MAX(peso_kg) as max_peso, pescador, senuelo FROM capturas GROUP BY especie ORDER BY max_peso DESC').fetchall()
            tab = conn.execute('SELECT pescador, COUNT(*) as total, ROUND(SUM(peso_kg), 2) as kilos_totales FROM capturas GROUP BY pescador ORDER BY kilos_totales DESC, total DESC').fetchall()
            return {'records_especie': [dict(r) for r in rec], 'tabla_pescadores': [dict(p) for p in tab]}

    def registrar_pesquero(self, nombre: str, latitud: float, longitud: float, referencia: str = '', privacidad: str = 'privado') -> str:
        nid = str(uuid.uuid4())
        with self._conectar() as conn:
            conn.execute('INSERT INTO pesqueros (uuid, nombre, latitud, longitud, referencia, privacidad, sync_status, updated_at) VALUES (?,?,?,?,?,?,0,?)', (nid, nombre, latitud, longitud, referencia, privacidad, self._ahora_iso()))
            conn.commit()
        return nid

    def obtener_pesqueros(self) -> list[dict]:
        with self._conectar() as conn:
            return [dict(f) for f in conn.execute('SELECT * FROM pesqueros ORDER BY updated_at DESC').fetchall()]

    def registrar_estado_rio(self, nivel: str, claridad: str, zona: str = 'General'):
        with self._conectar() as conn:
            conn.execute('INSERT INTO reporte_rio (uuid, nivel, claridad, zona, sync_status, updated_at) VALUES (?,?,?,?,0,?)', (str(uuid.uuid4()), nivel, claridad, zona, self._ahora_iso()))
            conn.commit()

    def obtener_ultimo_estado_rio(self) -> dict | None:
        with self._conectar() as conn:
            f = conn.execute('SELECT * FROM reporte_rio ORDER BY updated_at DESC LIMIT 1').fetchone()
            return dict(f) if f else None

    def registrar_gasto(self, concepto: str, pagado_por: str, monto: float):
        with self._conectar() as conn:
            conn.execute('INSERT INTO gastos_salida (uuid, concepto, pagado_por, monto, sync_status, updated_at) VALUES (?,?,?,?,0,?)', (str(uuid.uuid4()), concepto.strip(), pagado_por.strip(), monto, self._ahora_iso()))
            conn.commit()

    def obtener_gastos(self) -> list[dict]:
        with self._conectar() as conn:
            return [dict(f) for f in conn.execute('SELECT * FROM gastos_salida ORDER BY updated_at DESC').fetchall()]

    def limpiar_gastos(self):
        with self._conectar() as conn:
            conn.execute('DELETE FROM gastos_salida'); conn.commit()

    def registrar_mensaje_chat(self, remitente: str, mensaje: str, tipo: str = 'texto', club_id: str = '', remitente_email: str = '') -> str:
        nid = str(uuid.uuid4())
        if not club_id: club_id = self.obtener_perfil().get('club_activo', CLUB_DEFAULT_ID)
        with self._conectar() as conn:
            conn.execute('INSERT INTO mensajes_chat (uuid, club_id, remitente, remitente_email, mensaje, tipo, hora_local, sync_status, updated_at) VALUES (?,?,?,?,?,?,?,0,?)', (nid, club_id, remitente, remitente_email.lower(), mensaje.strip(), tipo, datetime.now().strftime('%H:%M'), self._ahora_iso()))
            conn.commit()
        return nid

    def obtener_mensajes_chat(self, club_id: str = '', limite: int = 60) -> list[dict]:
        if not club_id: club_id = self.obtener_perfil().get('club_activo', CLUB_DEFAULT_ID)
        with self._conectar() as conn:
            filas = conn.execute('SELECT * FROM (SELECT * FROM mensajes_chat WHERE club_id=? ORDER BY updated_at DESC LIMIT ?) ORDER BY updated_at ASC', (club_id, limite)).fetchall()
            return [dict(f) for f in filas]

    def guardar_mensajes_remotos(self, mensajes: list[dict]):
        with self._conectar() as conn:
            for m in mensajes:
                conn.execute('INSERT OR IGNORE INTO mensajes_chat (uuid, club_id, remitente, remitente_email, mensaje, tipo, hora_local, sync_status, updated_at) VALUES (?,?,?,?,?,?,?,1,?)', (m.get('uuid', str(uuid.uuid4())), m.get('club_id', CLUB_DEFAULT_ID), m.get('remitente', 'Pescador'), m.get('remitente_email', ''), m.get('mensaje', ''), m.get('tipo', 'texto'), m.get('hora_local', '--:--'), m.get('updated_at', self._ahora_iso())))
            conn.commit()

    def contar_pendientes(self) -> int:
        with self._conectar() as conn:
            return sum(conn.execute(f'SELECT COUNT(*) FROM {t} WHERE sync_status != 1').fetchone()[0] for t in ('capturas', 'pesqueros', 'reporte_rio', 'mensajes_chat', 'clubes'))

    def obtener_pendientes_tabla(self, tabla: str) -> list[dict]:
        with self._conectar() as conn:
            return [dict(f) for f in conn.execute(f'SELECT * FROM {tabla} WHERE sync_status != 1').fetchall()]

    def marcar_sincronizados(self, tabla: str, uuids: list[str]):
        if not uuids: return
        with self._conectar() as conn:
            placeholders = ','.join('?' for _ in uuids)
            conn.execute(f'UPDATE {tabla} SET sync_status = 1 WHERE uuid IN ({placeholders})', uuids); conn.commit()
