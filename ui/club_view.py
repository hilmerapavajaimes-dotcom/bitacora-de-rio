import re, uuid, asyncio, inspect, urllib.parse, webbrowser
import flet as ft
from config import CLUB_NAME, DEFAULT_PESCADOR, COLOR_BG, COLOR_CARD, COLOR_CARD_ALT, COLOR_BORDER, COLOR_PRIMARY, COLOR_ACCENT, COLOR_WARNING, COLOR_DANGER, COLOR_INFO, COLOR_TEXT, COLOR_MUTED
from database.db_manager import DatabaseManager, CLUB_DEFAULT_ID
from services.sync_service import SyncService
from services.gps_service import GPSService

def construir_club_view(page: ft.Page, db: DatabaseManager, sync: SyncService, refrescar_badge, abrir_en_chat: bool = True):
    gps = GPSService(page)
    estado = {'tab': 0, 'poll': 0}
    lista_mensajes = ft.ListView(expand=True, spacing=8, padding=10, auto_scroll=True)
    lbl_chat_titulo = ft.Text('', size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)
    lbl_chat_estado = ft.Text('', size=11, color=COLOR_ACCENT)
    banner_anuncio = ft.Container(visible=False, bgcolor='#311042', border_radius=10, padding=8, border=ft.Border.all(1, COLOR_PRIMARY))
    txt_mensaje = ft.TextField(hint_text='Escribe al club...', expand=True, bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)

    def club_actual_obj() -> dict:
        perfil = db.obtener_perfil()
        cid = perfil.get('club_activo', CLUB_DEFAULT_ID)
        return db.obtener_club(cid) or {'codigo': cid, 'nombre': CLUB_NAME, 'descripcion': '', 'admin_email': '', 'admin_nombre': 'Admin', 'anuncio': '', 'baneados': ''}

    def renderizar_chat():
        perfil = db.obtener_perfil()
        club = club_actual_obj()
        mi_email = perfil.get('email', '').strip().lower()
        mi_nombre = perfil.get('nombre', DEFAULT_PESCADOR).strip().lower()
        baneados = [b.strip().lower() for b in (club.get('baneados') or '').split(',') if b.strip()]
        lbl_chat_titulo.value = f'{club['nombre']} ({club['codigo']})'
        lbl_chat_estado.value = '🟢 En linea' if sync.hay_internet(1.0) else '🟠 Offline (en cola)'
        lbl_chat_estado.color = COLOR_ACCENT if 'En linea' in lbl_chat_estado.value else COLOR_WARNING
        anuncio = (club.get('anuncio') or '').strip()
        banner_anuncio.visible = bool(anuncio)
        if anuncio: banner_anuncio.content = ft.Text(f'📢 Admin: {anuncio}', size=11, color=COLOR_WARNING, weight=ft.FontWeight.W_600)
        lista_mensajes.controls.clear()
        msgs = db.obtener_mensajes_chat(club['codigo'], 60)
        if not msgs:
            lista_mensajes.controls.append(ft.Container(padding=20, alignment=ft.Alignment(0, 0), content=ft.Text(f'Canal de {club['nombre']}.\nComparte codigo: {club['codigo']}', size=12, color=COLOR_MUTED, text_align=ft.TextAlign.CENTER)))
            return
        for m in msgs:
            rem_email = (m.get('remitente_email') or '').lower()
            if m['remitente'].lower() in baneados or (rem_email and rem_email in baneados): continue
            es_mio = (mi_email and rem_email == mi_email) or (m['remitente'].strip().lower() == mi_nombre)
            es_admin = bool(club.get('admin_email')) and rem_email == club.get('admin_email', '').lower()
            es_gps = m.get('tipo') == 'gps'
            bg = ('#064E3B' if es_mio else '#1E3A5F') if es_gps else (COLOR_PRIMARY if es_mio else COLOR_CARD_ALT)
            badge = ' 👑' if es_admin else (' ✓' if rem_email else '')
            tick = ' ✓✓' if m.get('sync_status') == 1 else ' 🕒'
            burbuja = ft.Container(bgcolor=bg, border_radius=14, padding=ft.Padding.symmetric(horizontal=12, vertical=8), border=ft.Border.all(1, COLOR_ACCENT if es_gps else COLOR_BORDER), width=270, content=ft.Column(spacing=3, controls=[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(('Tu' if es_mio else m['remitente']) + badge, size=11, weight=ft.FontWeight.BOLD, color=COLOR_ACCENT if not es_mio else COLOR_TEXT), ft.Text(m['hora_local'] + (tick if es_mio else ''), size=10, color=COLOR_MUTED)]), ft.Text(m['mensaje'], size=13, color=COLOR_TEXT, selectable=True)]))
            lista_mensajes.controls.append(ft.Row(alignment=ft.MainAxisAlignment.END if es_mio else ft.MainAxisAlignment.START, controls=[burbuja]))

    def enviar_msg(e=None, texto_forzado: str = '', tipo: str = 'texto'):
        contenido = texto_forzado if texto_forzado else txt_mensaje.value
        if not contenido or not contenido.strip(): return
        perfil = db.obtener_perfil()
        club = club_actual_obj()
        db.registrar_mensaje_chat(perfil.get('nombre', DEFAULT_PESCADOR), contenido.strip(), tipo, club['codigo'], perfil.get('email', ''))
        if not texto_forzado: txt_mensaje.value = ''
        renderizar_chat(); refrescar_badge(); sync.sincronizar_en_segundo_plano(); page.update()
    txt_mensaje.on_submit = enviar_msg

    async def enviar_gps_chat(e):
        lbl_chat_estado.value = 'Fijando GPS...'; page.update()
        try:
            pos = await gps.obtener_posicion_actual()
            enviar_msg(texto_forzado=f'📍 Mi ubicacion:\nLat: {pos['lat']}, Lon: {pos['lon']}\nhttps://maps.google.com/?q={pos['lat']},{pos['lon']}', tipo='gps')
        except Exception as ex:
            lbl_chat_estado.value = f'GPS: {ex}'; page.update()
    chips_chat = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=6, controls=[ft.Button('📍 Mi GPS', bgcolor=COLOR_CARD_ALT, color=COLOR_ACCENT, on_click=enviar_gps_chat), ft.Button('🎣 Hay pique!', bgcolor=COLOR_CARD_ALT, color=COLOR_TEXT, on_click=lambda _: enviar_msg(texto_forzado='🎣 Hay buen pique activo aqui!')), ft.Button('🌊 Rio subiendo', bgcolor=COLOR_CARD_ALT, color=COLOR_INFO, on_click=lambda _: enviar_msg(texto_forzado='🌊 Ojo: rio subiendo con corriente.'))])
    vista_chat = ft.Column(expand=True, spacing=8, controls=[ft.Container(bgcolor=COLOR_CARD, border_radius=12, padding=10, border=ft.Border.all(1, COLOR_BORDER), content=ft.Column(spacing=4, controls=[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[lbl_chat_titulo, ft.Row(spacing=4, controls=[lbl_chat_estado, ft.IconButton(icon=ft.Icons.REFRESH, icon_color=COLOR_ACCENT, on_click=lambda _: (sync.sincronizar_en_segundo_plano(), renderizar_chat(), page.update()))])]), banner_anuncio])), ft.Container(expand=True, bgcolor=COLOR_BG, border_radius=14, border=ft.Border.all(1, COLOR_BORDER), content=lista_mensajes), chips_chat, ft.Row(spacing=8, controls=[txt_mensaje, ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=COLOR_TEXT, bgcolor=COLOR_PRIMARY, on_click=enviar_msg)])])

    lista_clubes_ui = ft.Column(spacing=8)
    panel_admin_ui = ft.Container(visible=False, bgcolor=COLOR_CARD, border_radius=14, padding=12, border=ft.Border.all(1, COLOR_WARNING))
    txt_unirse_cod = ft.TextField(label='Codigo de club (ej. lospanemas-orinoco-2026)', expand=True, bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    txt_nuevo_nombre = ft.TextField(label='Nombre del nuevo club', bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    txt_nuevo_desc = ft.TextField(label='Zona / Rio (ej. Rio Cataniapo)', bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    sw_club_pub = ft.Switch(label='Club publico (visible en red)', value=True, active_color=COLOR_ACCENT)
    lbl_club_msg = ft.Text('', size=12, color=COLOR_ACCENT)

    def refrescar_clubes():
        perfil = db.obtener_perfil()
        actual = club_actual_obj()
        mi_email = perfil.get('email', '').lower()
        es_admin = bool(mi_email) and mi_email == actual.get('admin_email', '').lower()
        panel_admin_ui.visible = es_admin
        if es_admin:
            txt_anun = ft.TextField(label='Anuncio fijado del club', value=actual.get('anuncio', ''), bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
            txt_ban = ft.TextField(label='Expulsar/Bloquear (nombre o correo)', width=200, bgcolor=COLOR_CARD_ALT, border_color=COLOR_DANGER)
            def guardar_admin(e):
                ban_actual = actual.get('baneados', '')
                if txt_ban.value.strip(): ban_actual = (ban_actual + ',' + txt_ban.value.strip()).strip(',')
                db.crear_o_actualizar_club(actual['codigo'], actual['nombre'], actual.get('descripcion', ''), actual['admin_email'], actual['admin_nombre'], actual.get('es_publico', 1), txt_anun.value, ban_actual, 0)
                sync.sincronizar_en_segundo_plano(); refrescar_clubes(); renderizar_chat(); page.update()
            panel_admin_ui.content = ft.Column(spacing=8, controls=[ft.Text('👑 Administrar: ' + actual['nombre'], size=14, weight=ft.FontWeight.BOLD, color=COLOR_WARNING), txt_anun, ft.Row(spacing=8, controls=[txt_ban, ft.Button('Guardar', bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, on_click=guardar_admin)])])
        lista_clubes_ui.controls.clear()
        for c in db.obtener_clubes():
            activo = c['codigo'] == actual['codigo']
            def entrar_club(cod=c['codigo']):
                return lambda e: (db.cambiar_club_activo(cod), sync.sincronizar_en_segundo_plano(), cambiar_tab(0)(e))
            lista_clubes_ui.controls.append(ft.Container(bgcolor=COLOR_CARD_ALT, border_radius=12, padding=12, border=ft.Border.all(1, COLOR_ACCENT if activo else COLOR_BORDER), content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Column(spacing=2, expand=True, controls=[ft.Text(c['nombre'] + (' (Activo)' if activo else ''), weight=ft.FontWeight.BOLD, color=COLOR_TEXT), ft.Text('Admin: ' + c['admin_nombre'] + ' • Cod: ' + c['codigo'], size=11, color=COLOR_MUTED)]), ft.Button('Chat', bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, on_click=entrar_club())])))
    def crear_club(e):
        perfil = db.obtener_perfil()
        if not perfil.get('email'): lbl_club_msg.value = 'Vincula tu correo Google en la pestana Cuenta primero'; lbl_club_msg.color = COLOR_WARNING; page.update(); return
        nom = txt_nuevo_nombre.value.strip()
        if not nom: return
        slug = re.sub(r'[^a-z0-9]+', '-', nom.lower()).strip('-') + '-' + uuid.uuid4().hex[:4]
        db.crear_o_actualizar_club(slug, nom, txt_nuevo_desc.value.strip(), perfil['email'], perfil['nombre'], 1 if sw_club_pub.value else 0, '', '', 0)
        db.cambiar_club_activo(slug); txt_nuevo_nombre.value = ''; txt_nuevo_desc.value = ''
        sync.sincronizar_en_segundo_plano(); refrescar_clubes(); renderizar_chat(); cambiar_tab(0)(e)

    def unirse_codigo(e):
        cod = re.sub(r'[^a-zA-Z0-9_-]', '', txt_unirse_cod.value.strip().lower())
        if not cod: return
        if not db.obtener_club(cod): db.crear_o_actualizar_club(cod, 'Club ' + cod, 'Grupo por invitacion', 'externo', 'Club', 0, '', '', 1)
        db.cambiar_club_activo(cod); txt_unirse_cod.value = ''; sync.sincronizar_en_segundo_plano(); cambiar_tab(0)(e)

    vista_clubes = ft.ListView(expand=True, spacing=12, controls=[panel_admin_ui, ft.Container(bgcolor=COLOR_CARD, border_radius=14, padding=14, border=ft.Border.all(1, COLOR_BORDER), content=ft.Column(spacing=8, controls=[ft.Text('Unirse a un Club por Codigo', size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT), ft.Row(spacing=8, controls=[txt_unirse_cod, ft.Button('Unirse', bgcolor=COLOR_ACCENT, color=COLOR_BG, on_click=unirse_codigo)])])), ft.Container(bgcolor=COLOR_CARD, border_radius=14, padding=14, border=ft.Border.all(1, COLOR_BORDER), content=ft.Column(spacing=8, controls=[ft.Text('Crear Nuevo Club de Pesca', size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT), lbl_club_msg, txt_nuevo_nombre, txt_nuevo_desc, sw_club_pub, ft.Button('Crear y Administrar Club', icon=ft.Icons.ADD_CIRCLE, bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, width=400, on_click=crear_club)])), ft.Text('Directorio de Clubes en Red', size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT), lista_clubes_ui])

    perf = db.obtener_perfil()
    txt_p_nombre = ft.TextField(label='Tu Nombre en el Club', value=perf.get('nombre', DEFAULT_PESCADOR), bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    txt_p_email = ft.TextField(label='Correo de Google (ej. tunombre@gmail.com)', value=perf.get('email', ''), bgcolor=COLOR_CARD_ALT, border_color=COLOR_INFO)
    txt_p_bio = ft.TextField(label='Equipo / Modalidad favorita', value=perf.get('bio', ''), bgcolor=COLOR_CARD_ALT, border_color=COLOR_PRIMARY)
    lbl_p_estado = ft.Text('🟢 Cuenta vinculada: ' + perf['email'] if perf.get('email') else '⚪ Sin correo vinculado (modo invitado)', size=12, color=COLOR_ACCENT if perf.get('email') else COLOR_WARNING)
    def guardar_cuenta(e):
        if '@' not in txt_p_email.value: lbl_p_estado.value = 'Ingresa un correo valido (@gmail.com)'; lbl_p_estado.color = COLOR_WARNING; page.update(); return
        db.guardar_perfil(txt_p_nombre.value, txt_p_email.value, 'google', txt_p_bio.value)
        lbl_p_estado.value = '🟢 Cuenta Google vinculada: ' + txt_p_email.value.strip().lower(); lbl_p_estado.color = COLOR_ACCENT
        refrescar_clubes(); renderizar_chat(); page.update()
    vista_cuenta = ft.ListView(expand=True, spacing=12, controls=[ft.Container(bgcolor=COLOR_CARD, border_radius=16, padding=16, border=ft.Border.all(1, COLOR_PRIMARY), content=ft.Column(spacing=10, controls=[ft.Row(spacing=8, controls=[ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=COLOR_INFO, size=28), ft.Text('Vincular Cuenta Google / Perfil', size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)]), lbl_p_estado, txt_p_nombre, txt_p_email, txt_p_bio, ft.Button('Guardar y Vincular Cuenta', icon=ft.Icons.VERIFIED_USER, bgcolor=COLOR_ACCENT, color=COLOR_BG, width=400, on_click=guardar_cuenta)]))])

    ranking = db.obtener_ranking_club()
    lista_rec = ft.Column(spacing=6, controls=[ft.Container(bgcolor=COLOR_CARD_ALT, border_radius=10, padding=10, content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(r['especie'] + ' (' + r['pescador'] + ')', color=COLOR_TEXT), ft.Text(str(r['max_peso']) + ' kg', weight=ft.FontWeight.BOLD, color=COLOR_WARNING)])) for r in ranking['records_especie']] or [ft.Text('Sin capturas aun.', size=12, color=COLOR_MUTED)])
    vista_ranking = ft.ListView(expand=True, spacing=12, controls=[ft.Container(bgcolor=COLOR_CARD, border_radius=16, padding=16, border=ft.Border.all(1, COLOR_BORDER), content=ft.Column(spacing=10, controls=[ft.Text('Records por Especie', size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT), lista_rec]))])

    contenedor = ft.Container(expand=True)
    btns = [ft.Button('Chat', expand=True), ft.Button('Clubes', expand=True), ft.Button('Ranking', expand=True), ft.Button('Cuenta', expand=True)]
    vistas = [vista_chat, vista_clubes, vista_ranking, vista_cuenta]
    def cambiar_tab(idx: int):
        def _h(e=None):
            estado['tab'] = idx
            for i, b in enumerate(btns):
                b.bgcolor, b.color = (COLOR_PRIMARY, COLOR_TEXT) if i == idx else (COLOR_CARD_ALT, COLOR_MUTED)
            if idx == 1: refrescar_clubes()
            if idx == 0: renderizar_chat()
            contenedor.content = vistas[idx]
            if e: page.update()
        return _h
    for i, b in enumerate(btns): b.on_click = cambiar_tab(i)
    sync.on_chat_updated = lambda: (renderizar_chat(), page.update())
    renderizar_chat(); refrescar_clubes(); cambiar_tab(0 if abrir_en_chat else 1)()
    async def ciclo_chat():
        estado['poll'] += 1; tk = estado['poll']
        while estado['poll'] == tk:
            await asyncio.sleep(5)
            if estado['poll'] != tk: break
            if estado['tab'] in (0, 1): sync.sincronizar_en_segundo_plano()
    if hasattr(page, 'run_task'): page.run_task(ciclo_chat)
    return ft.Container(expand=True, padding=12, content=ft.Column(expand=True, spacing=8, controls=[ft.Row(spacing=6, controls=btns), contenedor]))
