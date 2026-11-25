import os
import inspect
from datetime import datetime
import flet as ft
from config import (
    DEFAULT_PESCADOR,
    COLOR_CARD,
    COLOR_CARD_ALT,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_DARK,
    COLOR_ACCENT,
    COLOR_WARNING,
    COLOR_INFO,
    COLOR_TEXT,
    COLOR_MUTED,
    ESPECIES_RIO,
    ESTADOS_RIO,
    CLARIDAD_AGUA,
    TIPOS_SENUELO,
    COLORES_SENUELO,
    ESTRUCTURAS_RIO,
)
from database.db_manager import DatabaseManager
from services.sync_service import SyncService
from services.solunar_service import calcular_datos_solunares
from services.tarjeta_service import generar_ficha_captura


def construir_home_view(page: ft.Page, db: DatabaseManager, sync: SyncService, refrescar_badge):
    estado_actual = db.obtener_ultimo_estado_rio()
    nivel_txt = estado_actual["nivel"] if estado_actual else "Sin reporte"
    claridad_txt = estado_actual["claridad"] if estado_actual else "—"
    solunar = calcular_datos_solunares()

    estado_foto = {"ruta_origen": ""}

    # Selector de archivos compatibilizado con Flet 0.80+
    file_picker = ft.FilePicker()
    if hasattr(page, "services"):
        page.services.append(file_picker)
    else:
        page.overlay.append(file_picker)

    lbl_rio = ft.Text(
        f"{nivel_txt} • {claridad_txt}",
        size=13,
        color=COLOR_ACCENT,
        weight=ft.FontWeight.BOLD,
    )

    banner_resumen = ft.Container(
        border_radius=18,
        padding=16,
        border=ft.Border.all(1, COLOR_PRIMARY),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[COLOR_PRIMARY_DARK, COLOR_CARD],
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text("ESTADO ACTUAL DEL RÍO", size=11, color=COLOR_MUTED, weight=ft.FontWeight.BOLD),
                        lbl_rio,
                        ft.Text(f"Próximo pico: {solunar['mayor_1']}", size=12, color=COLOR_TEXT),
                    ],
                ),
                ft.Container(
                    bgcolor=COLOR_CARD_ALT,
                    border_radius=14,
                    padding=10,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Text(solunar["icono"], size=24),
                            ft.Text(f"{solunar['puntaje']}%", size=12, weight=ft.FontWeight.BOLD, color=COLOR_ACCENT),
                        ],
                    ),
                ),
            ],
        ),
    )

    dd_nivel = ft.Dropdown(
        label="Nivel del río",
        value=ESTADOS_RIO[1],
        options=[ft.dropdown.Option(x) for x in ESTADOS_RIO],
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )

    dd_claridad = ft.Dropdown(
        label="Claridad",
        value=CLARIDAD_AGUA[0],
        options=[ft.dropdown.Option(x) for x in CLARIDAD_AGUA],
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )

    def guardar_rio(e):
        db.registrar_estado_rio(dd_nivel.value, dd_claridad.value)
        lbl_rio.value = f"{dd_nivel.value} • {dd_claridad.value}"
        refrescar_badge()
        sync.sincronizar_en_segundo_plano()
        page.update()

    tarjeta_rio = ft.Container(
        bgcolor=COLOR_CARD,
        border_radius=16,
        padding=16,
        border=ft.Border.all(1, COLOR_BORDER),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text("Condición del Río", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                ft.Row(spacing=10, controls=[dd_nivel, dd_claridad]),
                ft.Button(
                    "Actualizar estado del agua",
                    icon=ft.Icons.WATER,
                    bgcolor=COLOR_CARD_ALT,
                    color=COLOR_TEXT,
                    on_click=guardar_rio,
                ),
            ],
        ),
    )

    # --- FORMULARIO TÁCTICO DE CAPTURA ---
    txt_pescador = ft.TextField(
        label="Pescador",
        value=DEFAULT_PESCADOR,
        width=130,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )

    dd_especie = ft.Dropdown(
        label="Especie",
        value=ESPECIES_RIO[0],
        options=[ft.dropdown.Option(x) for x in ESPECIES_RIO],
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )

    txt_peso = ft.TextField(
        label="Peso (kg)",
        value="1.5",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=105,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )

    dd_senuelo = ft.Dropdown(
        label="Señuelo / Carnada",
        value=TIPOS_SENUELO[0],
        options=[ft.dropdown.Option(x) for x in TIPOS_SENUELO],
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )

    dd_color = ft.Dropdown(
        label="Color",
        value=COLORES_SENUELO[0],
        options=[ft.dropdown.Option(x) for x in COLORES_SENUELO],
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )

    dd_estructura = ft.Dropdown(
        label="Estructura donde picó",
        value=ESTRUCTURAS_RIO[0],
        options=[ft.dropdown.Option(x) for x in ESTRUCTURAS_RIO],
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )

    lbl_foto_estado = ft.Text("Sin foto adjunta (opcional)", size=12, color=COLOR_MUTED)
    lbl_ficha_generada = ft.Text("", size=12, color=COLOR_ACCENT)

    async def seleccionar_foto(e):
        try:
            res = file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE,
            )
            archivos = await res if inspect.iscoroutine(res) else None
            if archivos and len(archivos) > 0:
                ruta = getattr(archivos[0], "path", "")
                if ruta:
                    estado_foto["ruta_origen"] = ruta
                    lbl_foto_estado.value = f"Foto lista: {os.path.basename(ruta)}"
                    lbl_foto_estado.color = COLOR_INFO
                    page.update()
        except Exception as ex:
            lbl_foto_estado.value = f"Aviso selector: {ex}"
            lbl_foto_estado.color = COLOR_WARNING
            page.update()

    sw_compartir = ft.Switch(
        label="Compartir en ranking del club",
        value=True,
        active_track_color=COLOR_PRIMARY,
    )
    lista_capturas = ft.Column(spacing=8)

    def renderizar_capturas():
        lista_capturas.controls.clear()
        for cap in db.obtener_capturas(12):
            icono_sync = ft.Icons.CLOUD_DONE if cap["sync_status"] == 1 else ft.Icons.CLOUD_OFF
            color_sync = COLOR_ACCENT if cap["sync_status"] == 1 else COLOR_MUTED

            detalle_linea1 = f"{cap['senuelo']}"
            if cap.get("color_senuelo"):
                detalle_linea1 += f" ({cap['color_senuelo']})"

            detalle_linea2 = f"{cap.get('estructura') or 'Río'} • {cap.get('hora_captura') or ''} • Por {cap.get('pescador') or DEFAULT_PESCADOR}"

            controles_der = []
            if cap.get("foto_ficha") and os.path.exists(cap["foto_ficha"]):
                controles_der.append(
                    ft.Icon(ft.Icons.PHOTO_CAMERA_BACK, color=COLOR_INFO, size=20, tooltip="Ficha guardada")
                )
            controles_der.append(ft.Icon(icono_sync, color=color_sync, size=20))

            lista_capturas.controls.append(
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
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        f"{cap['especie']} — {cap['peso_kg']} kg",
                                        weight=ft.FontWeight.BOLD,
                                        color=COLOR_TEXT,
                                    ),
                                    ft.Text(detalle_linea1, size=12, color=COLOR_ACCENT),
                                    ft.Text(detalle_linea2, size=11, color=COLOR_MUTED),
                                ],
                            ),
                            ft.Row(spacing=6, controls=controles_der),
                        ],
                    ),
                )
            )

    def guardar_captura(e):
        try:
            peso = float(txt_peso.value.replace(",", "."))
        except ValueError:
            peso = 0.0

        ruta_ficha_final = ""
        if estado_foto["ruta_origen"]:
            try:
                ruta_ficha_final = generar_ficha_captura(
                    ruta_foto_origen=estado_foto["ruta_origen"],
                    especie=dd_especie.value,
                    peso_kg=peso,
                    senuelo=dd_senuelo.value,
                    color_senuelo=dd_color.value,
                    estructura=dd_estructura.value,
                    pescador=txt_pescador.value,
                )
                lbl_ficha_generada.value = f"Ficha WhatsApp guardada en: {ruta_ficha_final}"
                lbl_ficha_generada.color = COLOR_ACCENT
            except Exception as ex:
                lbl_ficha_generada.value = str(ex)
                lbl_ficha_generada.color = COLOR_WARNING

        priv = "club" if sw_compartir.value else "privado"
        db.registrar_captura(
            especie=dd_especie.value,
            peso_kg=peso,
            senuelo=dd_senuelo.value,
            estado_rio=dd_nivel.value,
            pescador=txt_pescador.value,
            color_senuelo=dd_color.value,
            estructura=dd_estructura.value,
            hora_captura=datetime.now().strftime("%H:%M"),
            foto_ficha=ruta_ficha_final,
            privacidad=priv,
        )

        estado_foto["ruta_origen"] = ""
        lbl_foto_estado.value = "Sin foto adjunta (opcional)"
        lbl_foto_estado.color = COLOR_MUTED

        renderizar_capturas()
        refrescar_badge()
        sync.sincronizar_en_segundo_plano()
        page.update()

    tarjeta_captura = ft.Container(
        bgcolor=COLOR_CARD,
        border_radius=16,
        padding=16,
        border=ft.Border.all(1, COLOR_BORDER),
        content=ft.Column(
            spacing=11,
            controls=[
                ft.Text("Registro Táctico de Captura", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                ft.Row(spacing=8, controls=[dd_especie, txt_peso]),
                ft.Row(spacing=8, controls=[dd_senuelo, dd_color]),
                ft.Row(spacing=8, controls=[ft.Container(expand=True, content=dd_estructura), txt_pescador]),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Button(
                            "Foto para Ficha",
                            icon=ft.Icons.ADD_A_PHOTO,
                            bgcolor=COLOR_CARD_ALT,
                            color=COLOR_INFO,
                            on_click=seleccionar_foto,
                        ),
                        ft.Container(expand=True, content=lbl_foto_estado),
                    ],
                ),
                lbl_ficha_generada,
                sw_compartir,
                ft.Button(
                    "Guardar Captura",
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                    bgcolor=COLOR_PRIMARY,
                    color=COLOR_TEXT,
                    width=400,
                    height=46,
                    on_click=guardar_captura,
                ),
            ],
        ),
    )

    renderizar_capturas()

    return ft.ListView(
        expand=True,
        spacing=14,
        padding=16,
        controls=[
            banner_resumen,
            tarjeta_captura,
            tarjeta_rio,
            ft.Text("Últimas Capturas", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            lista_capturas,
        ],
    )
