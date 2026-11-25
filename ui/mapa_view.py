import asyncio, inspect, math, os
import flet as ft
from config import DEFAULT_LAT, DEFAULT_LON, COLOR_BG, COLOR_CARD, COLOR_CARD_ALT, COLOR_BORDER, COLOR_PRIMARY, COLOR_ACCENT, COLOR_WARNING, COLOR_INFO, COLOR_TEXT, COLOR_MUTED
from database.db_manager import DatabaseManager
from services.gps_service import GPSService
from services.map_cache_service import MapCacheService
from services.sync_service import SyncService
URL_SATELITE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
URL_MAPA = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
MAP_W, MAP_H, TILE_SZ = 340.0, 330.0, 256.0
def _ll_a_ft(lat: float, lon: float, z: int):
    rad = math.radians(max(-85.0511, min(85.0511, lat)))
    n = 2.0 ** z
    return (lon + 180.0) / 360.0 * n, (1.0 - math.asinh(math.tan(rad)) / math.pi) / 2.0 * n
def _ft_a_ll(xf: float, yf: float, z: int):
    n = 2.0 ** z
    return round(max(-85.0, min(85.0, math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * yf / n)))))), 6), round(max(-180.0, min(180.0, (xf / n) * 360.0 - 180.0)), 6)
def _dist_rumbo(lat1: float, lon1: float, lat2: float, lon2: float):
    p1, p2, dp, dl = math.radians(lat1), math.radians(lat2), math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    dm = 2.0 * 6371000.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    ds = f'{int(dm)} m' if dm < 1000 else f'{dm / 1000.0:.2f} km'
    br = (math.degrees(math.atan2(math.sin(dl) * math.cos(p2), math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) + 360.0) % 360.0
    pts = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO']
    return ds, f'{pts[int((br + 22.5) // 45) % 8]} ({int(br)}°)'
def construir_mapa_view(page: ft.Page, db: DatabaseManager, sync: SyncService, refrescar_badge, map_cache: MapCacheService):
    gps = GPSService(page)
    est = {'sat': True, 'z': 14, 'clat': DEFAULT_LAT, 'clon': DEFAULT_LON, 'mlat': None, 'mlon': None, 'plat': None, 'plon': None, 'obj': None}
    lbl_sub = ft.Text('Toca el mapa para marcar, arrastra para mover o pulsa Mi GPS', size=12, color=COLOR_MUTED)
    lbl_gps = ft.Text(f'Centro: {DEFAULT_LAT}, {DEFAULT_LON}', size=11, color=COLOR_INFO, weight=ft.FontWeight.W_600)
    lbl_cache = ft.Text(f'Cache offline: {map_cache.contar_cuadros()} cuadros', size=12, color=COLOR_INFO)
    lbl_rad_t = ft.Text('Selecciona un pesquero para activar rumbo', size=13, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)
    lbl_rad_d = ft.Text('Distancia: -  •  Direccion: -', size=12, color=COLOR_ACCENT, weight=ft.FontWeight.W_600)
    lbl_pto = ft.Text('Toca en el mapa o pega un enlace de Google Maps', size=11, color=COLOR_WARNING)
    txt_nom = ft.TextField(label='Nombre del punto (ej. Raudal / Boca de Cano)', bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    txt_lat = ft.TextField(label='Latitud', value=str(DEFAULT_LAT), keyboard_type=ft.KeyboardType.NUMBER, expand=True, bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    txt_lon = ft.TextField(label='Longitud', value=str(DEFAULT_LON), keyboard_type=ft.KeyboardType.NUMBER, expand=True, bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    txt_link = ft.TextField(label='Pegar enlace Google Maps o Lat, Lon', expand=True, bgcolor=COLOR_CARD_ALT, border_color=COLOR_INFO)
    sw_priv = ft.Switch(label='Punto secreto (privado)', value=True, active_color=COLOR_ACCENT)
    lista_ui = ft.Column(spacing=8)
    lienzo = ft.Stack(width=MAP_W, height=MAP_H)
    def act_radar():
        o = est['obj']
        if not o: lbl_rad_t.value, lbl_rad_d.value = 'Selecciona un pesquero para activar rumbo', 'Distancia: -  •  Direccion: -'; return
        rlat = est['mlat'] if est['mlat'] is not None else est['clat']
        rlon = est['mlon'] if est['mlon'] is not None else est['clon']
        ds, rb = _dist_rumbo(rlat, rlon, float(o['latitud']), float(o['longitud']))
        lbl_rad_t.value = 'Rumbo a: ' + str(o['nombre'])
        lbl_rad_d.value = f'Distancia: {ds}  •  Direccion: {rb}'
    def sel_pesquero(p: dict):
        def _h(e=None):
            est['obj'], est['clat'], est['clon'], est['z'] = p, float(p['latitud']), float(p['longitud']), 15
            act_radar(); redibujar(); page.update()
        return _h
    def redibujar():
        z = est['z']
        xf, yf = _ll_a_ft(est['clat'], est['clon'], z)
        cx, cy = int(math.floor(xf)), int(math.floor(yf))
        gl, gt, mt = (MAP_W / 2.0) - (1.0 + xf - cx) * TILE_SZ, (MAP_H / 2.0) - (1.0 + yf - cy) * TILE_SZ, (1 << z) - 1
        capas = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                tx, ty = max(0, min(mt, cx + dx)), max(0, min(mt, cy + dy))
                lj = os.path.join(map_cache.cache_dir, str(z), str(tx), f'{ty}.jpg')
                src = lj if (est['sat'] and os.path.exists(lj) and os.path.getsize(lj) > 0) else (URL_SATELITE if est['sat'] else URL_MAPA).format(z=z, x=tx, y=ty)
                capas.append(ft.Container(left=gl + (dx + 1) * TILE_SZ, top=gt + (dy + 1) * TILE_SZ, width=TILE_SZ, height=TILE_SZ, content=ft.Image(src=src, width=TILE_SZ, height=TILE_SZ)))
        def en_vista(la, lo):
            mxf, myf = _ll_a_ft(la, lo, z)
            vx, vy = (MAP_W / 2.0) + (mxf - xf) * TILE_SZ, (MAP_H / 2.0) + (myf - yf) * TILE_SZ
            return (vx, vy) if (-40 <= vx <= MAP_W + 40 and -40 <= vy <= MAP_H + 40) else None
        for p in db.obtener_pesqueros():
            xy = en_vista(float(p['latitud']), float(p['longitud']))
            if xy: capas.append(ft.Container(left=xy[0] - 42, top=xy[1] - 44, width=84, on_click=sel_pesquero(p), content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1, controls=[ft.Container(bgcolor=COLOR_CARD, border_radius=6, padding=ft.Padding.symmetric(horizontal=5, vertical=2), border=ft.Border.all(1, COLOR_ACCENT), content=ft.Text(p['nombre'][:12], size=9, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)), ft.Icon(ft.Icons.PUSH_PIN, color=COLOR_ACCENT, size=22)])))
        if est['plat'] is not None:
            xy = en_vista(est['plat'], est['plon'])
            if xy: capas.append(ft.Container(left=xy[0] - 40, top=xy[1] - 46, width=80, content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1, controls=[ft.Container(bgcolor=COLOR_WARNING, border_radius=6, padding=ft.Padding.symmetric(horizontal=5, vertical=2), content=ft.Text('Marcar', size=9, weight=ft.FontWeight.BOLD, color=COLOR_BG)), ft.Icon(ft.Icons.LOCATION_ON, color=COLOR_WARNING, size=26)])))
        if est['mlat'] is not None:
            xy = en_vista(est['mlat'], est['mlon'])
            if xy: capas.append(ft.Container(left=xy[0] - 18, top=xy[1] - 32, width=36, content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1, controls=[ft.Container(bgcolor=COLOR_INFO, border_radius=6, padding=ft.Padding.symmetric(horizontal=4, vertical=1), content=ft.Text('TU', size=9, weight=ft.FontWeight.BOLD, color=COLOR_BG)), ft.Container(width=16, height=16, border_radius=8, bgcolor='#2563EB', border=ft.Border.all(2, '#FFFFFF'))])))
        lienzo.controls = capas
    def marcar(la, lo, txt='Marcado en mapa'):
        est['plat'], est['plon'] = la, lo; txt_lat.value, txt_lon.value = str(la), str(lo); lbl_pto.value = f'{txt}: {la}, {lo}'; redibujar()
    def al_tocar(e):
        pos = getattr(e, 'local_position', None)
        tx, ty = (pos.x, pos.y) if pos is not None else (getattr(e, 'local_x', MAP_W / 2.0), getattr(e, 'local_y', MAP_H / 2.0))
        xf, yf = _ll_a_ft(est['clat'], est['clon'], est['z'])
        marcar(*_ft_a_ll(xf + (tx - MAP_W / 2.0) / TILE_SZ, yf + (ty - MAP_H / 2.0) / TILE_SZ, est['z'])); page.update()
    def al_mover(e):
        d = getattr(e, 'local_delta', None)
        dx, dy = (d.x, d.y) if d is not None else (getattr(e, 'delta_x', 0.0), getattr(e, 'delta_y', 0.0))
        xf, yf = _ll_a_ft(est['clat'], est['clon'], est['z'])
        est['clat'], est['clon'] = _ft_a_ll(xf - dx / TILE_SZ, yf - dy / TILE_SZ, est['z'])
        lbl_gps.value = 'Vista: {}, {} (Z{})'.format(est['clat'], est['clon'], est['z']); redibujar(); page.update()
    async def localizar(e=None):
        lbl_gps.value, lbl_gps.color = 'Abriendo GPS en navegador...', COLOR_WARNING; page.update()
        try:
            pos = await gps.obtener_posicion_actual()
            la, lo = pos['lat'], pos['lon']
            est['mlat'], est['mlon'], est['clat'], est['clon'], est['z'] = la, lo, la, lo, 15
            marcar(la, lo, 'Tu GPS'); lbl_gps.value, lbl_gps.color = 'Tu GPS: {}, {} (±{}m)'.format(la, lo, int(pos['precision'])), COLOR_ACCENT; act_radar()
        except Exception as ex:
            lbl_gps.value, lbl_gps.color = f'{ex} (o pega enlace abajo)', COLOR_WARNING
        page.update()
    def usar_link(e):
        c = gps.extraer_coordenadas(txt_link.value)
        if not c: lbl_pto.value = 'No se detectaron coordenadas en ese texto'; page.update(); return
        est['mlat'], est['mlon'], est['clat'], est['clon'], est['z'] = c[0], c[1], c[0], c[1], 15
        marcar(c[0], c[1], 'Coordenadas aplicadas'); lbl_gps.value, lbl_gps.color = f'Ubicacion: {c[0]}, {c[1]}', COLOR_ACCENT; txt_link.value = ''; act_radar(); page.update()
    def zoom_btn(d):
        return lambda e: (est.update({'z': max(4, min(17, est['z'] + d))}), setattr(lbl_gps, 'value', 'Vista: {}, {} (Z{})'.format(est['clat'], est['clon'], est['z'])), redibujar(), page.update())
    def capa_btn(e):
        est['sat'] = not est['sat']; btn_capa.text = 'Satelite' if est['sat'] else 'Mapa'; redibujar(); page.update()
    async def desc_zona(e):
        btn_desc.disabled, lbl_cache.value, lbl_cache.color = True, 'Descargando cuadros...', COLOR_WARNING; page.update()
        la, lo = (est['mlat'] if est['mlat'] is not None else est['clat']), (est['mlon'] if est['mlon'] is not None else est['clon'])
        try:
            r = map_cache.descargar_zona(la, lo)
            if inspect.iscoroutine(r): await r
            else: await asyncio.to_thread(map_cache.descargar_zona, la, lo)
        except Exception: pass
        lbl_cache.value, lbl_cache.color, btn_desc.disabled = f'Cache offline: {map_cache.contar_cuadros()} cuadros', COLOR_INFO, False; redibujar(); page.update()
    def ref_lista():
        lista_ui.controls.clear()
        ps = db.obtener_pesqueros()
        if not ps: lista_ui.controls.append(ft.Text('Aun no tienes pesqueros guardados.', size=12, color=COLOR_MUTED)); return
        for p in ps:
            priv = p.get('privacidad') == 'privado'
            lista_ui.controls.append(ft.Container(bgcolor=COLOR_CARD_ALT, border_radius=12, padding=12, border=ft.Border.all(1, COLOR_BORDER), on_click=sel_pesquero(p), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Column(spacing=2, expand=True, controls=[ft.Text(p['nombre'], weight=ft.FontWeight.BOLD, color=COLOR_TEXT), ft.Text('Lat: {}  •  Lon: {}'.format(p['latitud'], p['longitud']), size=11, color=COLOR_MUTED)]), ft.Row(spacing=6, controls=[ft.Icon(ft.Icons.LOCK if priv else ft.Icons.GROUPS, size=16, color=COLOR_WARNING if priv else COLOR_ACCENT), ft.Icon(ft.Icons.NEAR_ME, size=18, color=COLOR_INFO)])])))
    def guardar_pto(e):
        nom = txt_nom.value.strip()
        if not nom: lbl_pto.value = 'Escribe un nombre para el punto'; page.update(); return
        try: la, lo = round(float(txt_lat.value.replace(',', '.')), 6), round(float(txt_lon.value.replace(',', '.')), 6)
        except ValueError: lbl_pto.value = 'Coordenadas invalidas'; page.update(); return
        db.registrar_pesquero(nombre=nom, latitud=la, longitud=lo, privacidad='privado' if sw_priv.value else 'club')
        txt_nom.value, est['plat'], est['plon'], lbl_pto.value = '', None, None, f'Pesquero {nom} guardado'
        redibujar(); ref_lista(); refrescar_badge(); sync.sincronizar_en_segundo_plano(); page.update()
    btn_capa = ft.Button('Satelite', icon=ft.Icons.LAYERS, bgcolor=COLOR_CARD_ALT, color=COLOR_TEXT, on_click=capa_btn)
    btn_gps = ft.Button('Mi GPS', icon=ft.Icons.MY_LOCATION, bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, on_click=lambda e: page.run_task(localizar, e))
    btn_desc = ft.Button('Descargar Zona', icon=ft.Icons.DOWNLOAD, bgcolor=COLOR_ACCENT, color=COLOR_BG, on_click=desc_zona)
    redibujar(); ref_lista()
    visor = ft.Container(width=MAP_W, height=MAP_H, bgcolor=COLOR_CARD_ALT, border_radius=14, border=ft.Border.all(1, COLOR_PRIMARY), clip_behavior=ft.ClipBehavior.HARD_EDGE, content=ft.Stack(width=MAP_W, height=MAP_H, controls=[ft.GestureDetector(on_tap_down=al_tocar, on_pan_update=al_mover, content=lienzo), ft.Container(right=8, top=8, content=ft.Column(spacing=6, controls=[ft.IconButton(icon=ft.Icons.MY_LOCATION, icon_color=COLOR_BG, bgcolor=COLOR_INFO, on_click=lambda e: page.run_task(localizar, e)), ft.IconButton(icon=ft.Icons.ADD, icon_color=COLOR_TEXT, bgcolor=COLOR_CARD, on_click=zoom_btn(1)), ft.IconButton(icon=ft.Icons.REMOVE, icon_color=COLOR_TEXT, bgcolor=COLOR_CARD, on_click=zoom_btn(-1))])), ft.Container(left=8, bottom=8, bgcolor='#CC0D0E15', border_radius=10, padding=ft.Padding.symmetric(horizontal=8, vertical=4), border=ft.Border.all(1, COLOR_BORDER), content=lbl_gps)]))
    return ft.ListView(expand=True, spacing=12, padding=16, controls=[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text('Mapa y Radar', size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXT), ft.Row(spacing=6, controls=[btn_capa, btn_gps])]), lbl_sub, ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[visor]), ft.Container(bgcolor=COLOR_CARD, border_radius=14, padding=12, border=ft.Border.all(1, COLOR_BORDER), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[lbl_cache, btn_desc])), ft.Container(bgcolor=COLOR_CARD, border_radius=14, padding=12, border=ft.Border.all(1, COLOR_BORDER), content=ft.Row(spacing=12, controls=[ft.Container(width=40, height=40, border_radius=20, bgcolor=COLOR_CARD_ALT, alignment=ft.Alignment(0, 0), content=ft.Icon(ft.Icons.NAVIGATION, color=COLOR_ACCENT, size=22)), ft.Column(spacing=2, expand=True, controls=[lbl_rad_t, lbl_rad_d])])), ft.Container(bgcolor=COLOR_CARD, border_radius=14, padding=14, border=ft.Border.all(1, COLOR_BORDER), content=ft.Column(spacing=10, controls=[ft.Text('Guardar Punto Marcado', size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT), lbl_pto, ft.Row(spacing=6, controls=[txt_link, ft.Button('Usar', bgcolor=COLOR_INFO, color=COLOR_BG, on_click=usar_link)]), txt_nom, ft.Row(spacing=8, controls=[txt_lat, txt_lon]), sw_priv, ft.Button('Guardar Pesquero', icon=ft.Icons.ADD_LOCATION_ALT, bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, width=400, on_click=guardar_pto)])), ft.Text('Mis Pesqueros Guardados (Toca para activar rumbo)', size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT), lista_ui])
