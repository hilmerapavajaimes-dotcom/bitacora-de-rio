import os
import inspect
import urllib.parse
import webbrowser
import flet as ft
from config import (
    APP_NAME,
    CLUB_NAME,
    COLOR_BG,
    COLOR_CARD,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_ACCENT,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_INFO,
    COLOR_TEXT,
)
from database.db_manager import DatabaseManager
from services.sync_service import SyncService
from services.gps_service import GPSService
from services.map_cache_service import MapCacheService
from services.icon_service import asegurar_icono_app, ICON_ICO_PATH
from ui.home_view import construir_home_view
from ui.mapa_view import construir_mapa_view
from ui.solunar_view import construir_solunar_view
from ui.club_view import construir_club_view
from ui.herramientas_view import construir_herramientas_view


def main(page: ft.Page):
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLOR_BG
    page.padding = 0

    # Genera y aplica el ícono HD de la aplicación (assets/icon.png)
    ruta_icono = asegurar_icono_app()
    try:
        if os.path.exists(ICON_ICO_PATH):
            page.window.icon = ICON_ICO_PATH
        elif ruta_icono:
            page.window.icon = ruta_icono
    except Exception:
        pass

    db = DatabaseManager()
    gps_sos = GPSService(page)
    map_cache = MapCacheService()

    lbl_estado_sync = ft.Text("Offline listo", size=11, color=COLOR_ACCENT, weight=ft.FontWeight.W_600)

    def refrescar_badge():
        pendientes = db.contar_pendientes()
        if pendientes > 0:
            lbl_estado_sync.value = f"{pendientes} pend."
            lbl_estado_sync.color = COLOR_WARNING
        else:
            lbl_estado_sync.value = "Al día"
            lbl_estado_sync.color = COLOR_ACCENT

    def al_cambiar_estado_sync(mensaje: str, exito: bool):
        lbl_estado_sync.value = mensaje
        lbl_estado_sync.color = COLOR_ACCENT if exito else COLOR_WARNING
        page.update()

    sync = SyncService(db, on_status_change=al_cambiar_estado_sync)
    refrescar_badge()

    async def enviar_ubicacion_sos(e):
        lbl_estado_sync.value = "Fijando GPS SOS..."
        lbl_estado_sync.color = COLOR_WARNING
        page.update()

        try:
            pos = await gps_sos.obtener_posicion_actual()
            lat, lon = pos["lat"], pos["lon"]
            texto = (
                f"Ubicación actual en salida de pesca (Club {CLUB_NAME}):\n"
                f"Lat: {lat}, Lon: {lon}\n"
                f"Ver en mapa: https://maps.google.com/?q={lat},{lon}"
            )
        except Exception:
            texto = (
                f"Reporte de salida de pesca (Club {CLUB_NAME}): "
                f"Sin señal satelital fija en este instante, todo en orden en el río."
            )

        refrescar_badge()
        page.update()

        url = f"https://wa.me/?text={urllib.parse.quote(texto)}"
        try:
            res = page.launch_url(url)
            if inspect.iscoroutine(res):
                await res
        except Exception:
            webbrowser.open(url)

    contenedor_principal = ft.Container(expand=True)
    vista_home = construir_home_view(page, db, sync, refrescar_badge)
    vista_mapa = construir_mapa_view(page, db, sync, refrescar_badge, map_cache)
    vista_solunar = construir_solunar_view(page)
    contenedor_principal.content = vista_home

    def navegar_a_indice(idx: int):
        nav_bar.selected_index = idx
        if idx == 0:
            contenedor_principal.content = vista_home
        elif idx == 1:
            contenedor_principal.content = vista_mapa
        elif idx == 2:
            contenedor_principal.content = vista_solunar
        elif idx == 3:
            contenedor_principal.content = construir_club_view(page, db, sync, refrescar_badge, abrir_en_chat=True)
        elif idx == 4:
            contenedor_principal.content = construir_herramientas_view(page, db)
        page.update()

    def cambiar_tab(e):
        navegar_a_indice(e.control.selected_index)

    # Miniatura del ícono en la barra superior
    logo_header = (
        ft.Image(src=ruta_icono, width=30, height=30, border_radius=8)
        if ruta_icono
        else ft.Icon(ft.Icons.PHISHING, color=COLOR_PRIMARY)
    )

    header = ft.Container(
        bgcolor=COLOR_CARD,
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        border=ft.Border.only(bottom=ft.BorderSide(1, COLOR_BORDER)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        logo_header,
                        ft.Text(APP_NAME, size=17, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                    ],
                ),
                ft.Row(
                    spacing=0,
                    controls=[
                        lbl_estado_sync,
                        ft.IconButton(
                            icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
                            icon_color=COLOR_INFO,
                            tooltip="Abrir Chat del Club",
                            on_click=lambda _: navegar_a_indice(3),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SOS,
                            icon_color=COLOR_DANGER,
                            tooltip="Enviar ubicación GPS por WhatsApp",
                            on_click=enviar_ubicacion_sos,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SYNC,
                            icon_color=COLOR_TEXT,
                            tooltip="Sincronizar ahora",
                            on_click=lambda _: sync.sincronizar_en_segundo_plano(),
                        ),
                    ],
                ),
            ],
        ),
    )

    nav_bar = ft.NavigationBar(
        bgcolor=COLOR_CARD,
        indicator_color=COLOR_PRIMARY,
        selected_index=0,
        on_change=cambiar_tab,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.SET_MEAL, label="Bitácora"),
            ft.NavigationBarDestination(icon=ft.Icons.MAP, label="Mapa"),
            ft.NavigationBarDestination(icon=ft.Icons.NIGHTLIGHT_ROUND, label="Luna"),
            ft.NavigationBarDestination(icon=ft.Icons.GROUPS, label="Club"),
            ft.NavigationBarDestination(icon=ft.Icons.BUILD_CIRCLE, label="Extras"),
        ],
    )

    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[header, contenedor_principal, nav_bar],
        )
    )

    sync.sincronizar_en_segundo_plano()


if __name__ == "__main__":
    ft.run(main)
