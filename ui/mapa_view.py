import math
import flet as ft
from config import (
    DEFAULT_LAT,
    DEFAULT_LON,
    COLOR_BG,
    COLOR_CARD,
    COLOR_CARD_ALT,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_ACCENT,
    COLOR_WARNING,
    COLOR_INFO,
    COLOR_TEXT,
    COLOR_MUTED,
)
from database.db_manager import DatabaseManager
from services.sync_service import SyncService
from services.gps_service import (
    GPSService,
    calcular_distancia_metros,
    calcular_rumbo_grados,
    obtener_punto_cardinal,
    formatear_distancia,
)
from services.map_cache_service import MapCacheService

try:
    import flet_map as fm
except ImportError:
    fm = None


def construir_mapa_view(
    page: ft.Page,
    db: DatabaseManager,
    sync: SyncService,
    refrescar_badge,
    map_cache: MapCacheService,
):
    gps = GPSService(page)

    estado = {
        "mi_lat": None,
        "mi_lon": None,
        "centro_lat": DEFAULT_LAT,
        "centro_lon": DEFAULT_LON,
        "objetivo": None,
        "modo_satelite": True,
    }

    lbl_gps_info = ft.Text("Toca 'Mi GPS' o marca un punto directo en el mapa", size=12, color=COLOR_MUTED)
    lbl_cache_info = ft.Text(
        f"Caché offline: {map_cache.contar_tiles_cacheados()} cuadros guardados",
        size=11,
        color=COLOR_INFO,
    )
    barra_descarga = ft.ProgressBar(value=0, visible=False, color=COLOR_ACCENT, bgcolor=COLOR_CARD_ALT)

    lbl_brujula_titulo = ft.Text("Selecciona un pesquero para activar rumbo", size=13, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)
    lbl_brujula_detalle = ft.Text("Distancia: —  •  Dirección: —", size=12, color=COLOR_ACCENT)
    icono_flecha = ft.Icon(ft.Icons.NAVIGATION, size=34, color=COLOR_ACCENT, rotate=ft.Rotate(angle=0))

    txt_nombre = ft.TextField(
        label="Nombre del punto (ej. Raudal / Boca de Caño)",
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )
    txt_lat = ft.TextField(
        label="Latitud",
        value=str(DEFAULT_LAT),
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )
    txt_lon = ft.TextField(
        label="Longitud",
        value=str(DEFAULT_LON),
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )
    sw_privado = ft.Switch(label="Punto secreto (privado)", value=True, active_track_color=COLOR_ACCENT)

    lista_puntos = ft.Column(spacing=8)
    marcadores_layer = fm.MarkerLayer(markers=[]) if fm else None
    tile_layer = (
        fm.TileLayer(url_template=map_cache.obtener_url_template(True)) if fm else None
    )

    def seleccionar_objetivo(punto: dict):
        def _handler(e=None):
            estado["objetivo"] = punto
            actualizar_brujula()
            page.update()
        return _handler

    def actualizar_brujula():
        obj = estado["objetivo"]
        mi_lat = estado["mi_lat"]
        mi_lon = estado["mi_lon"]

        if obj is None:
            return

        lbl_brujula_titulo.value = f"Rumbo a: {obj['nombre']}"
        if mi_lat is None or mi_lon is None:
            lbl_brujula_detalle.value = f"Coords: {obj['latitud']}, {obj['longitud']} (Fija tu GPS para ver metros)"
            lbl_brujula_detalle.color = COLOR_WARNING
            return

        metros = calcular_distancia_metros(mi_lat, mi_lon, obj["latitud"], obj["longitud"])
        rumbo = calcular_rumbo_grados(mi_lat, mi_lon, obj["latitud"], obj["longitud"])
        cardinal = obtener_punto_cardinal(rumbo)

        icono_flecha.rotate = ft.Rotate(angle=math.radians(rumbo))
        lbl_brujula_detalle.value = f"{formatear_distancia(metros)}  •  {rumbo:.0f}° {cardinal}"
        lbl_brujula_detalle.color = COLOR_ACCENT

    def refrescar_marcadores_mapa():
        if not fm or marcadores_layer is None:
            return
        marcadores_layer.markers.clear()

        if estado["mi_lat"] is not None and estado["mi_lon"] is not None:
            marcadores_layer.markers.append(
                fm.Marker(
                    coordinates=fm.MapLatitudeLongitude(estado["mi_lat"], estado["mi_lon"]),
                    content=ft.Icon(ft.Icons.MY_LOCATION, color=COLOR_INFO, size=28),
                )
            )

        for p in db.obtener_pesqueros():
            es_priv = p["privacidad"] == "privado"
            color_pin = COLOR_ACCENT if es_priv else COLOR_WARNING
            marcadores_layer.markers.append(
                fm.Marker(
                    coordinates=fm.MapLatitudeLongitude(p["latitud"], p["longitud"]),
                    content=ft.GestureDetector(
                        on_tap=seleccionar_objetivo(p),
                        content=ft.Column(
                            spacing=0,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    bgcolor=COLOR_BG,
                                    padding=ft.Padding.symmetric(horizontal=5, vertical=2),
                                    border_radius=6,
                                    content=ft.Text(p["nombre"], size=10, color=COLOR_TEXT, weight=ft.FontWeight.BOLD),
                                ),
                                ft.Icon(ft.Icons.LOCATION_ON, color=color_pin, size=30),
                            ],
                        ),
                    ),
                )
            )

    def al_tocar_mapa(e):
        if hasattr(e, "coordinates") and e.coordinates:
            lat = round(e.coordinates.latitude, 6)
            lon = round(e.coordinates.longitude, 6)
            estado["centro_lat"] = lat
            estado["centro_lon"] = lon
            txt_lat.value = str(lat)
            txt_lon.value = str(lon)
            lbl_gps_info.value = f"Punto marcado: {lat}, {lon}"
            lbl_gps_info.color = COLOR_INFO
            page.update()

    def alternar_capa_mapa(e):
        if not fm or tile_layer is None:
            return
        estado["modo_satelite"] = not estado["modo_satelite"]
        tile_layer.url_template = map_cache.obtener_url_template(estado["modo_satelite"])
        btn_capa.text = "Mapa" if estado["modo_satelite"] else "Satélite"
        page.update()

    def iniciar_descarga_offline(e):
        try:
            lat = float(txt_lat.value.replace(",", "."))
            lon = float(txt_lon.value.replace(",", "."))
        except ValueError:
            lat, lon = estado["centro_lat"], estado["centro_lon"]

        barra_descarga.visible = True
        barra_descarga.value = 0.05
        lbl_cache_info.value = "Descargando vista satelital (3 km a la redonda)..."
        lbl_cache_info.color = COLOR_WARNING
        page.update()

        def _al_progresar(actual: int, total: int, terminado: bool):
            barra_descarga.value = actual / max(1, total)
            if terminado:
                barra_descarga.visible = False
                lbl_cache_info.value = (
                    f"Zona lista offline ({map_cache.contar_tiles_cacheados()} cuadros en memoria)"
                )
                lbl_cache_info.color = COLOR_ACCENT
            else:
                lbl_cache_info.value = f"Descargando zona satelital: {actual}/{total} cuadros..."
            page.update()

        map_cache.descargar_zona_offline(lat, lon, radio_km=3.0, on_progreso=_al_progresar)

    btn_capa = ft.Button(
        "Mapa",
        icon=ft.Icons.LAYERS,
        bgcolor=COLOR_CARD_ALT,
        color=COLOR_TEXT,
        on_click=alternar_capa_mapa,
    )

    async def capturar_mi_gps(e):
        lbl_gps_info.value = "Buscando satélites GPS..."
        lbl_gps_info.color = COLOR_WARNING
        page.update()

        try:
            pos = await gps.obtener_posicion_actual()
            estado["mi_lat"] = pos["lat"]
            estado["mi_lon"] = pos["lon"]
            estado["centro_lat"] = pos["lat"]
            estado["centro_lon"] = pos["lon"]
            txt_lat.value = str(pos["lat"])
            txt_lon.value = str(pos["lon"])
            lbl_gps_info.value = f"GPS fijado: {pos['lat']}, {pos['lon']} (±{pos['precision']} m)"
            lbl_gps_info.color = COLOR_ACCENT
        except Exception as ex:
            lbl_gps_info.value = str(ex)
            lbl_gps_info.color = COLOR_WARNING

        refrescar_marcadores_mapa()
        actualizar_brujula()
        renderizar_lista_puntos()
        page.update()

    if fm:
        contenedor_mapa = ft.Container(
            height=290,
            border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.Border.all(1, COLOR_BORDER),
            content=fm.Map(
                expand=True,
                initial_center=fm.MapLatitudeLongitude(DEFAULT_LAT, DEFAULT_LON),
                initial_zoom=13,
                on_tap=al_tocar_mapa,
                layers=[tile_layer, marcadores_layer],
            ),
        )
    else:
        contenedor_mapa = ft.Container(
            bgcolor=COLOR_CARD_ALT,
            border_radius=16,
            padding=16,
            border=ft.Border.all(1, COLOR_WARNING),
            content=ft.Text(
                "Instala 'flet-map' (pip install flet-map) para activar el mapa satelital interactivo.",
                color=COLOR_WARNING,
                size=13,
            ),
        )

    def renderizar_lista_puntos():
        lista_puntos.controls.clear()
        mi_lat = estado["mi_lat"]
        mi_lon = estado["mi_lon"]

        for p in db.obtener_pesqueros():
            es_priv = p["privacidad"] == "privado"
            badge_color = COLOR_ACCENT if es_priv else COLOR_WARNING
            badge_txt = "PRIVADO" if es_priv else "CLUB"

            sub = f"{p['latitud']}, {p['longitud']}"
            if mi_lat is not None and mi_lon is not None:
                d = calcular_distancia_metros(mi_lat, mi_lon, p["latitud"], p["longitud"])
                r = calcular_rumbo_grados(mi_lat, mi_lon, p["latitud"], p["longitud"])
                sub += f" • a {formatear_distancia(d)} ({obtener_punto_cardinal(r)})"

            lista_puntos.controls.append(
                ft.Container(
                    bgcolor=COLOR_CARD,
                    border_radius=14,
                    padding=12,
                    border=ft.Border.all(1, COLOR_BORDER),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                expand=True,
                                spacing=3,
                                controls=[
                                    ft.Text(p["nombre"], weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                                    ft.Text(sub, size=12, color=COLOR_MUTED),
                                ],
                            ),
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.Container(
                                        bgcolor=badge_color,
                                        border_radius=6,
                                        padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                                        content=ft.Text(badge_txt, size=10, weight=ft.FontWeight.BOLD, color=COLOR_BG),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EXPLORE,
                                        icon_color=COLOR_ACCENT,
                                        tooltip="Activar brújula hacia este punto",
                                        on_click=seleccionar_objetivo(p),
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )

    def guardar_punto(e):
        if not txt_nombre.value.strip():
            return
        try:
            lat = float(txt_lat.value.replace(",", "."))
            lon = float(txt_lon.value.replace(",", "."))
        except ValueError:
            return

        priv = "privado" if sw_privado.value else "club"
        db.registrar_pesquero(txt_nombre.value.strip(), lat, lon, privacidad=priv)
        txt_nombre.value = ""
        refrescar_marcadores_mapa()
        renderizar_lista_puntos()
        refrescar_badge()
        sync.sincronizar_en_segundo_plano()
        page.update()

    refrescar_marcadores_mapa()
    renderizar_lista_puntos()

    return ft.ListView(
        expand=True,
        spacing=12,
        padding=16,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Mapa y Radar", size=17, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                    ft.Row(
                        spacing=6,
                        controls=[
                            btn_capa,
                            ft.Button(
                                "Mi GPS",
                                icon=ft.Icons.MY_LOCATION,
                                bgcolor=COLOR_PRIMARY,
                                color=COLOR_TEXT,
                                on_click=capturar_mi_gps,
                            ),
                        ],
                    ),
                ],
            ),
            lbl_gps_info,
            contenedor_mapa,
            # Barra de descarga offline del mapa
            ft.Container(
                bgcolor=COLOR_CARD,
                border_radius=12,
                padding=10,
                border=ft.Border.all(1, COLOR_BORDER),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Container(expand=True, content=lbl_cache_info),
                                ft.Button(
                                    "Descargar Zona",
                                    icon=ft.Icons.DOWNLOAD_FOR_OFFLINE,
                                    bgcolor=COLOR_CARD_ALT,
                                    color=COLOR_ACCENT,
                                    on_click=iniciar_descarga_offline,
                                ),
                            ],
                        ),
                        barra_descarga,
                    ],
                ),
            ),
            # Brújula offline
            ft.Container(
                bgcolor=COLOR_CARD,
                border_radius=14,
                padding=12,
                border=ft.Border.all(1, COLOR_BORDER),
                content=ft.Row(
                    spacing=12,
                    controls=[
                        ft.Container(
                            bgcolor=COLOR_BG,
                            border_radius=25,
                            padding=8,
                            content=icono_flecha,
                        ),
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[lbl_brujula_titulo, lbl_brujula_detalle],
                        ),
                    ],
                ),
            ),
            # Formulario rápido de guardado
            ft.Container(
                bgcolor=COLOR_CARD,
                border_radius=16,
                padding=16,
                border=ft.Border.all(1, COLOR_BORDER),
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Guardar Punto Marcado", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                        txt_nombre,
                        ft.Row(spacing=10, controls=[txt_lat, txt_lon]),
                        sw_privado,
                        ft.Button(
                            "Guardar Pesquero",
                            icon=ft.Icons.ADD_LOCATION_ALT,
                            bgcolor=COLOR_PRIMARY,
                            color=COLOR_TEXT,
                            width=400,
                            height=44,
                            on_click=guardar_punto,
                        ),
                    ],
                ),
            ),
            ft.Text("Pesqueros Guardados", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            lista_puntos,
        ],
    )
