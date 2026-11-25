import math
import flet as ft
from config import (
    COLOR_BG,
    COLOR_CARD,
    COLOR_CARD_ALT,
    COLOR_PRIMARY,
    COLOR_ACCENT,
    COLOR_WARNING,
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


def construir_pesqueros_view(page: ft.Page, db: DatabaseManager, sync: SyncService, refrescar_badge):
    gps = GPSService(page)

    estado_gps = {
        "mi_lat": None,
        "mi_lon": None,
        "objetivo": None,
    }

    # --- CONTROLES DE BRÚJULA / RADAR OFFLINE ---
    lbl_mi_ubicacion = ft.Text(
        "Mi GPS: Sin fijar (pulsa 'Capturar GPS')",
        size=12,
        color=COLOR_MUTED,
    )
    lbl_estado_gps = ft.Text("", size=11, color=COLOR_WARNING)

    icono_brujula = ft.Icon(
        ft.Icons.NAVIGATION,
        size=42,
        color=COLOR_ACCENT,
        rotate=ft.Rotate(angle=0),
    )

    lbl_objetivo_nombre = ft.Text(
        "Selecciona un pesquero abajo para guiarte",
        size=14,
        weight=ft.FontWeight.BOLD,
        color=COLOR_TEXT,
    )
    lbl_distancia_rumbo = ft.Text(
        "Distancia: —  •  Rumbo: —",
        size=13,
        color=COLOR_ACCENT,
        weight=ft.FontWeight.W_600,
    )

    def actualizar_calculo_brujula():
        mi_lat = estado_gps["mi_lat"]
        mi_lon = estado_gps["mi_lon"]
        obj = estado_gps["objetivo"]

        if obj is None:
            lbl_objetivo_nombre.value = "Selecciona un pesquero abajo para guiarte"
            lbl_distancia_rumbo.value = "Distancia: —  •  Rumbo: —"
            return

        lbl_objetivo_nombre.value = f"Destino: {obj['nombre']}"

        if mi_lat is None or mi_lon is None:
            lbl_distancia_rumbo.value = "Fija tu GPS actual para calcular metros y rumbo"
            lbl_distancia_rumbo.color = COLOR_WARNING
            return

        metros = calcular_distancia_metros(mi_lat, mi_lon, obj["latitud"], obj["longitud"])
        rumbo = calcular_rumbo_grados(mi_lat, mi_lon, obj["latitud"], obj["longitud"])
        cardinal = obtener_punto_cardinal(rumbo)

        icono_brujula.rotate = ft.Rotate(angle=math.radians(rumbo))
        lbl_distancia_rumbo.value = f"{formatear_distancia(metros)}  •  {rumbo:.0f}° {cardinal}"
        lbl_distancia_rumbo.color = COLOR_ACCENT

    async def capturar_mi_gps(e):
        lbl_estado_gps.value = "Buscando satélites GPS..."
        lbl_estado_gps.color = COLOR_WARNING
        page.update()

        try:
            pos = await gps.obtener_posicion_actual()
            estado_gps["mi_lat"] = pos["lat"]
            estado_gps["mi_lon"] = pos["lon"]
            lbl_mi_ubicacion.value = f"Mi GPS: {pos['lat']}, {pos['lon']} (±{pos['precision']} m)"
            lbl_mi_ubicacion.color = COLOR_ACCENT
            lbl_estado_gps.value = "Posición satelital actualizada sin internet"
            lbl_estado_gps.color = COLOR_ACCENT
        except Exception as ex:
            lbl_estado_gps.value = str(ex)
            lbl_estado_gps.color = COLOR_WARNING

        actualizar_calculo_brujula()
        renderizar_puntos()
        page.update()

    tarjeta_brujula = ft.Container(
        bgcolor=COLOR_CARD,
        border_radius=16,
        padding=16,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Radar y Brújula Offline", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                        ft.Button(
                            "Capturar GPS",
                            icon=ft.Icons.MY_LOCATION,
                            bgcolor=COLOR_PRIMARY,
                            color=COLOR_TEXT,
                            on_click=capturar_mi_gps,
                        ),
                    ],
                ),
                lbl_mi_ubicacion,
                lbl_estado_gps,
                ft.Container(
                    bgcolor=COLOR_CARD_ALT,
                    border_radius=12,
                    padding=12,
                    content=ft.Row(
                        spacing=14,
                        controls=[
                            ft.Container(
                                bgcolor=COLOR_BG,
                                border_radius=30,
                                padding=10,
                                content=icono_brujula,
                            ),
                            ft.Column(
                                expand=True,
                                spacing=4,
                                controls=[
                                    lbl_objetivo_nombre,
                                    lbl_distancia_rumbo,
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    # --- FORMULARIO DE NUEVO PESQUERO ---
    txt_nombre = ft.TextField(
        label="Nombre del punto (ej. Piedra Boca Caño)",
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )
    txt_lat = ft.TextField(
        label="Latitud",
        value="5.6639",
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )
    txt_lon = ft.TextField(
        label="Longitud",
        value="-67.6236",
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )
    sw_privado = ft.Switch(
        label="Punto secreto (solo respaldo privado)",
        value=True,
        active_track_color=COLOR_ACCENT,
    )

    async def usar_gps_en_formulario(e):
        if estado_gps["mi_lat"] is None:
            await capturar_mi_gps(e)
        if estado_gps["mi_lat"] is not None:
            txt_lat.value = str(estado_gps["mi_lat"])
            txt_lon.value = str(estado_gps["mi_lon"])
            page.update()

    lista_puntos = ft.Column(spacing=8)

    def seleccionar_objetivo(punto: dict):
        def _handler(e):
            estado_gps["objetivo"] = punto
            actualizar_calculo_brujula()
            page.update()
        return _handler

    def renderizar_puntos():
        lista_puntos.controls.clear()
        mi_lat = estado_gps["mi_lat"]
        mi_lon = estado_gps["mi_lon"]

        for p in db.obtener_pesqueros():
            es_privado = p["privacidad"] == "privado"
            badge_color = COLOR_ACCENT if es_privado else COLOR_WARNING
            badge_txt = "PRIVADO" if es_privado else "CLUB"

            subtitulo = f"GPS: {p['latitud']}, {p['longitud']}"
            if mi_lat is not None and mi_lon is not None:
                dist = calcular_distancia_metros(mi_lat, mi_lon, p["latitud"], p["longitud"])
                rumbo = calcular_rumbo_grados(mi_lat, mi_lon, p["latitud"], p["longitud"])
                subtitulo += f"  •  a {formatear_distancia(dist)} ({obtener_punto_cardinal(rumbo)})"

            lista_puntos.controls.append(
                ft.Container(
                    bgcolor=COLOR_CARD,
                    border_radius=12,
                    padding=12,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                expand=True,
                                spacing=3,
                                controls=[
                                    ft.Text(p["nombre"], weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                                    ft.Text(subtitulo, size=12, color=COLOR_MUTED),
                                ],
                            ),
                            ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Container(
                                        bgcolor=badge_color,
                                        border_radius=8,
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                        content=ft.Text(badge_txt, size=11, weight=ft.FontWeight.BOLD, color=COLOR_BG),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EXPLORE,
                                        icon_color=COLOR_ACCENT,
                                        tooltip="Guiar hasta este punto",
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
        renderizar_puntos()
        refrescar_badge()
        sync.sincronizar_en_segundo_plano()
        page.update()

    renderizar_puntos()

    return ft.ListView(
        expand=True,
        spacing=14,
        padding=16,
        controls=[
            tarjeta_brujula,
            ft.Container(
                bgcolor=COLOR_CARD,
                border_radius=16,
                padding=16,
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Guardar Nuevo Pesquero", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                                ft.Button(
                                    "Usar mi GPS",
                                    icon=ft.Icons.GPS_FIXED,
                                    bgcolor=COLOR_CARD_ALT,
                                    color=COLOR_ACCENT,
                                    on_click=usar_gps_en_formulario,
                                ),
                            ],
                        ),
                        txt_nombre,
                        ft.Row(spacing=10, controls=[txt_lat, txt_lon]),
                        sw_privado,
                        ft.Button(
                            "Guardar Coordenada",
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
            ft.Text("Mis Pesqueros Guardados", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            lista_puntos,
        ],
    )
