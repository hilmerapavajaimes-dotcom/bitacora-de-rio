import math, asyncio, inspect
import flet as ft
from config import DEFAULT_LAT, DEFAULT_LON, COLOR_BG, COLOR_CARD, COLOR_CARD_ALT, COLOR_BORDER, COLOR_PRIMARY, COLOR_ACCENT, COLOR_WARNING, COLOR_INFO, COLOR_TEXT, COLOR_MUTED
from database.db_manager import DatabaseManager
from services.sync_service import SyncService
from services.gps_service import GPSService
from services.map_cache_service import MapCacheService
try:
    import flet_map as ftm
except ImportError:
    ftm = None

URL_SATELITE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
URL_MAPA = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

def _calcular_distancia_y_rumbo(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[str, str]:
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    dist_m = 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    dist_str = f'{int(dist_m)} m' if dist_m < 1000 else f'{dist_m / 1000.0:.2f} km'
    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    brng = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    puntos = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO']
    return dist_str, f'{puntos[int((brng + 22.5) // 45) % 8]} ({int(brng)}°)'

def construir_mapa_view(page: ft.Page, db: DatabaseManager, sync: SyncService, refrescar_badge, map_cache: MapCacheService):
    gps = GPSService(page)
    estado = {'es_satelite': True, 'zoom': 14, 'centro_lat': DEFAULT_LAT, 'centro_lon': DEFAULT_LON, 'mi_lat': None, 'mi_lon': None, 'marcado_lat': None, 'marcado_lon': None, 'objetivo': None}
    lbl_subtitulo = ft.Text('Toca Mi GPS para ubicarte o toca cualquier punto del mapa para marcarlo', size=12, color=COLOR_MUTED)
    lbl_estado_gps_mapa = ft.Text('Buscando tu ubicacion GPS...', size=11, color=COLOR_INFO, weight=ft.FontWeight.W_600)
    lbl_cache = ft.Text(f'Cache offline: {map_cache.contar_cuadros()} cuadros guardados', size=12, color=COLOR_INFO)
    lbl_radar_titulo = ft.Text('Selecciona un pesquero para activar rumbo', size=13, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)
    lbl_radar_datos = ft.Text('Distancia: -  •  Direccion: -', size=12, color=COLOR_ACCENT, weight=ft.FontWeight.W_600)
    lbl_punto_marcado = ft.Text('Toca en el mapa para elegir coordenadas o usa tu GPS actual', size=11, color=COLOR_WARNING)
    txt_nombre_punto = ft.TextField(label='Nombre del punto (ej. Raudal / Boca de Cano)', bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    txt_lat = ft.TextField(label='Latitud', value=str(DEFAULT_LAT), keyboard_type=ft.KeyboardType.NUMBER, expand=True, bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    txt_lon = ft.TextField(label='Longitud', value=str(DEFAULT_LON), keyboard_type=ft.KeyboardType.NUMBER, expand=True, bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    sw_privado = ft.Switch(label='Punto secreto (privado)', value=True, active_color=COLOR_ACCENT)
    lista_pesqueros_ui = ft.Column(spacing=8)
    tile_layer = ftm.TileLayer(url_template=URL_SATELITE) if ftm else None
    capa_pesqueros = ftm.MarkerLayer(markers=[]) if ftm else None
    capa_punto_marcado = ftm.MarkerLayer(markers=[]) if ftm else None
    capa_mi_ubicacion = ftm.MarkerLayer(markers=[]) if ftm else None
    mapa = None
    def actualizar_radar():
        obj = estado['objetivo']
        if not obj:
            lbl_radar_titulo.value = 'Selecciona un pesquero para activar rumbo'
            lbl_radar_datos.value = 'Distancia: -  •  Direccion: -'
            return
        ref_lat = estado['mi_lat'] if estado['mi_lat'] is not None else estado['centro_lat']
        ref_lon = estado['mi_lon'] if estado['mi_lon'] is not None else estado['centro_lon']
        dist_str, rumbo_str = _calcular_distancia_y_rumbo(ref_lat, ref_lon, float(obj['latitud']), float(obj['longitud']))
        origen = 'desde tu GPS' if estado['mi_lat'] is not None else 'desde centro'
        lbl_radar_titulo.value = 'Rumbo a: ' + str(obj['nombre'])
        lbl_radar_datos.value = f'Distancia: {dist_str}  •  Direccion: {rumbo_str} ({origen})'

    def seleccionar_pesquero(p: dict):
        async def _handler(e=None):
            estado['objetivo'] = p
            actualizar_radar()
            await mover_camara(float(p['latitud']), float(p['longitud']), zoom=15)
            page.update()
        return _handler

    def reconstruir_marcadores():
        if ftm is None: return
        capa_mi_ubicacion.markers.clear()
        if estado['mi_lat'] is not None and estado['mi_lon'] is not None:
            capa_mi_ubicacion.markers.append(ftm.Marker(coordinates=ftm.MapLatitudeLongitude(estado['mi_lat'], estado['mi_lon']), width=84, height=58, content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[ft.Container(bgcolor=COLOR_INFO, border_radius=8, padding=ft.Padding.symmetric(horizontal=6, vertical=2), content=ft.Text('TU', size=10, weight=ft.FontWeight.BOLD, color=COLOR_BG)), ft.Container(width=22, height=22, border_radius=11, bgcolor='#2563EB', border=ft.Border.all(3, '#FFFFFF'))])))
        capa_punto_marcado.markers.clear()
        if estado['marcado_lat'] is not None and estado['marcado_lon'] is not None:
            capa_punto_marcado.markers.append(ftm.Marker(coordinates=ftm.MapLatitudeLongitude(estado['marcado_lat'], estado['marcado_lon']), width=110, height=60, content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1, controls=[ft.Container(bgcolor=COLOR_WARNING, border_radius=8, padding=ft.Padding.symmetric(horizontal=6, vertical=2), content=ft.Text('Marcar aqui', size=10, weight=ft.FontWeight.BOLD, color=COLOR_BG)), ft.Icon(ft.Icons.LOCATION_ON, color=COLOR_WARNING, size=30)])))
        capa_pesqueros.markers.clear()
        for p in db.obtener_pesqueros():
            nombre_corto = p['nombre'][:14] + ('...' if len(p['nombre']) > 14 else '')
            capa_pesqueros.markers.append(ftm.Marker(coordinates=ftm.MapLatitudeLongitude(float(p['latitud']), float(p['longitud'])), width=120, height=60, content=ft.GestureDetector(on_tap=seleccionar_pesquero(p), content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1, controls=[ft.Container(bgcolor=COLOR_CARD, border_radius=8, padding=ft.Padding.symmetric(horizontal=6, vertical=2), border=ft.Border.all(1, COLOR_ACCENT), content=ft.Text(nombre_corto, size=10, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)), ft.Icon(ft.Icons.PUSH_PIN, color=COLOR_ACCENT, size=26)]))))

    async def mover_camara(lat: float, lon: float, zoom: int | None = None):
        estado['centro_lat'], estado['centro_lon'] = lat, lon
        if zoom is not None: estado['zoom'] = zoom
        if mapa is not None:
            try:
                res = mapa.move_to(destination=ftm.MapLatitudeLongitude(lat, lon), zoom=estado['zoom'])
                if inspect.iscoroutine(res): await res
            except Exception: pass
    def marcar_punto_en_mapa(lat: float, lon: float, origen_texto: str = 'Punto marcado en mapa'):
        estado['marcado_lat'], estado['marcado_lon'] = lat, lon
        txt_lat.value, txt_lon.value = str(lat), str(lon)
        lbl_punto_marcado.value = f'{origen_texto}: {lat}, {lon}'
        reconstruir_marcadores()

    def al_tocar_mapa(e):
        if not hasattr(e, 'coordinates') or e.coordinates is None: return
        marcar_punto_en_mapa(round(float(e.coordinates.latitude), 6), round(float(e.coordinates.longitude), 6))
        page.update()

    async def localizar_usuario(e=None, centrar: bool = True):
        lbl_estado_gps_mapa.value, lbl_estado_gps_mapa.color = 'Fijando satelites GPS...', COLOR_WARNING
        if e is not None: page.update()
        try:
            pos = await gps.obtener_posicion_actual()
            lat, lon = pos['lat'], pos['lon']
            estado['mi_lat'], estado['mi_lon'] = lat, lon
            if estado['marcado_lat'] is None: txt_lat.value, txt_lon.value = str(lat), str(lon)
            lbl_estado_gps_mapa.value, lbl_estado_gps_mapa.color = f'Tu ubicacion: {lat}, {lon} (±' + str(int(pos['precision'])) + 'm)', COLOR_ACCENT
            reconstruir_marcadores(); actualizar_radar()
            if centrar: await mover_camara(lat, lon, zoom=15)
        except Exception as ex:
            lbl_estado_gps_mapa.value, lbl_estado_gps_mapa.color = f'GPS: {ex}', COLOR_WARNING
        page.update()

    def usar_mi_gps_para_guardar(e):
        if estado['mi_lat'] is not None and estado['mi_lon'] is not None:
            marcar_punto_en_mapa(estado['mi_lat'], estado['mi_lon'], 'Marcado en tu ubicacion GPS'); page.update()
        else: page.run_task(localizar_usuario, e, True)

    async def cambiar_zoom(delta: int):
        await mover_camara(estado['centro_lat'], estado['centro_lon'], zoom=max(3, min(18, estado['zoom'] + delta))); page.update()

    def alternar_capa_mapa(e):
        if tile_layer is None: return
        estado['es_satelite'] = not estado['es_satelite']
        tile_layer.url_template = URL_SATELITE if estado['es_satelite'] else URL_MAPA
        btn_capa.text = 'Satelite' if estado['es_satelite'] else 'Mapa'; page.update()

    async def descargar_zona_offline(e):
        btn_descargar.disabled, lbl_cache.value, lbl_cache.color = True, 'Descargando cuadros...', COLOR_WARNING; page.update()
        lat = estado['mi_lat'] if estado['mi_lat'] is not None else estado['centro_lat']
        lon = estado['mi_lon'] if estado['mi_lon'] is not None else estado['centro_lon']
        try:
            res = map_cache.descargar_zona(lat, lon)
            if inspect.iscoroutine(res): await res
            else: await asyncio.to_thread(map_cache.descargar_zona, lat, lon)
        except Exception: pass
        lbl_cache.value, lbl_cache.color, btn_descargar.disabled = f'Cache offline: {map_cache.contar_cuadros()} cuadros guardados', COLOR_INFO, False; page.update()
    def refrescar_lista_pesqueros():
        lista_pesqueros_ui.controls.clear()
        pesqueros = db.obtener_pesqueros()
        if not pesqueros:
            lista_pesqueros_ui.controls.append(ft.Text('Aun no tienes pesqueros guardados.', size=12, color=COLOR_MUTED)); return
        for p in pesqueros:
            es_priv = p.get('privacidad') == 'privado'
            lista_pesqueros_ui.controls.append(ft.Container(bgcolor=COLOR_CARD_ALT, border_radius=12, padding=12, border=ft.Border.all(1, COLOR_BORDER), on_click=seleccionar_pesquero(p), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Column(spacing=2, expand=True, controls=[ft.Text(p['nombre'], weight=ft.FontWeight.BOLD, color=COLOR_TEXT), ft.Text('Lat: ' + str(p['latitud']) + '  •  Lon: ' + str(p['longitud']), size=11, color=COLOR_MUTED)]), ft.Row(spacing=6, controls=[ft.Icon(ft.Icons.LOCK if es_priv else ft.Icons.GROUPS, size=16, color=COLOR_WARNING if es_priv else COLOR_ACCENT), ft.Icon(ft.Icons.NEAR_ME, size=18, color=COLOR_INFO)])])))

    def guardar_pesquero(e):
        nombre = txt_nombre_punto.value.strip()
        if not nombre: lbl_punto_marcado.value = 'Escribe un nombre para el punto'; page.update(); return
        try: lat, lon = round(float(txt_lat.value.replace(',', '.')), 6), round(float(txt_lon.value.replace(',', '.')), 6)
        except ValueError: lbl_punto_marcado.value = 'Coordenadas invalidas'; page.update(); return
        db.registrar_pesquero(nombre=nombre, latitud=lat, longitud=lon, privacidad='privado' if sw_privado.value else 'club')
        txt_nombre_punto.value = ''; estado['marcado_lat'], estado['marcado_lon'] = None, None; lbl_punto_marcado.value = f'Pesquero {nombre} guardado'
        reconstruir_marcadores(); refrescar_lista_pesqueros(); refrescar_badge(); sync.sincronizar_en_segundo_plano(); page.update()

    btn_capa = ft.Button('Satelite', icon=ft.Icons.LAYERS, bgcolor=COLOR_CARD_ALT, color=COLOR_TEXT, on_click=alternar_capa_mapa)
    btn_mi_gps = ft.Button('Mi GPS', icon=ft.Icons.MY_LOCATION, bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, on_click=lambda e: page.run_task(localizar_usuario, e, True))
    btn_descargar = ft.Button('Descargar Zona', icon=ft.Icons.DOWNLOAD, bgcolor=COLOR_ACCENT, color=COLOR_BG, on_click=descargar_zona_offline)
    reconstruir_marcadores(); refrescar_lista_pesqueros()
    if ftm is not None:
        mapa = ftm.Map(expand=True, initial_center=ftm.MapLatitudeLongitude(DEFAULT_LAT, DEFAULT_LON), initial_zoom=14, min_zoom=3, max_zoom=18, on_tap=al_tocar_mapa, on_long_press=al_tocar_mapa, layers=[tile_layer, capa_pesqueros, capa_punto_marcado, capa_mi_ubicacion])
        controles_flotantes_mapa = ft.Container(right=10, top=10, content=ft.Column(spacing=6, controls=[ft.IconButton(icon=ft.Icons.MY_LOCATION, icon_color=COLOR_BG, bgcolor=COLOR_INFO, on_click=lambda e: page.run_task(localizar_usuario, e, True)), ft.IconButton(icon=ft.Icons.ADD, icon_color=COLOR_TEXT, bgcolor=COLOR_CARD, on_click=lambda e: page.run_task(cambiar_zoom, 1)), ft.IconButton(icon=ft.Icons.REMOVE, icon_color=COLOR_TEXT, bgcolor=COLOR_CARD, on_click=lambda e: page.run_task(cambiar_zoom, -1))]))
        pildora_gps_mapa = ft.Container(left=10, bottom=10, bgcolor='#CC0D0E15', border_radius=10, padding=ft.Padding.symmetric(horizontal=10, vertical=5), border=ft.Border.all(1, COLOR_BORDER), content=lbl_estado_gps_mapa)
        visor_mapa = ft.Container(height=340, border_radius=14, border=ft.Border.all(1, COLOR_PRIMARY), clip_behavior=ft.ClipBehavior.HARD_EDGE, content=ft.Stack(expand=True, controls=[mapa, controles_flotantes_mapa, pildora_gps_mapa]))
    else:
        visor_mapa = ft.Container(bgcolor=COLOR_CARD, border_radius=14, padding=16, border=ft.Border.all(1, COLOR_WARNING), content=ft.Text('Modulo flet-map no disponible.', color=COLOR_WARNING))
    if hasattr(page, 'run_task'): page.run_task(localizar_usuario, None, True)
    return ft.ListView(expand=True, spacing=12, padding=16, controls=[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text('Mapa y Radar', size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXT), ft.Row(spacing=6, controls=[btn_capa, btn_mi_gps])]), lbl_subtitulo, visor_mapa, ft.Container(bgcolor=COLOR_CARD, border_radius=14, padding=12, border=ft.Border.all(1, COLOR_BORDER), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[lbl_cache, btn_descargar])), ft.Container(bgcolor=COLOR_CARD, border_radius=14, padding=12, border=ft.Border.all(1, COLOR_BORDER), content=ft.Row(spacing=12, controls=[ft.Container(width=40, height=40, border_radius=20, bgcolor=COLOR_CARD_ALT, alignment=ft.Alignment(0, 0), content=ft.Icon(ft.Icons.NAVIGATION, color=COLOR_ACCENT, size=22)), ft.Column(spacing=2, expand=True, controls=[lbl_radar_titulo, lbl_radar_datos])])), ft.Container(bgcolor=COLOR_CARD, border_radius=14, padding=14, border=ft.Border.all(1, COLOR_BORDER), content=ft.Column(spacing=10, controls=[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text('Guardar Punto Marcado', size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT), ft.Button('Usar mi GPS', icon=ft.Icons.GPS_FIXED, bgcolor=COLOR_CARD_ALT, color=COLOR_INFO, on_click=usar_mi_gps_para_guardar)]), lbl_punto_marcado, txt_nombre_punto, ft.Row(spacing=8, controls=[txt_lat, txt_lon]), sw_privado, ft.Button('Guardar Pesquero', icon=ft.Icons.ADD_LOCATION_ALT, bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, width=400, on_click=guardar_pesquero)])), ft.Text('Mis Pesqueros Guardados (Toca para activar rumbo)', size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT), lista_pesqueros_ui])
