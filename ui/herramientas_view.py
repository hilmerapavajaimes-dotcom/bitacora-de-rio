import os
import flet as ft
from config import (
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
from data.guia_regional import ESPECIES_DETALLADAS, GUIA_CARNADAS, METODOS_CEBADEROS
from services.nudos_media_service import NUDOS_CATALOGO, obtener_media_nudo


def construir_herramientas_view(page: ft.Page, db: DatabaseManager):
    stats = db.obtener_estadisticas()
    contenedor_seccion = ft.Column(spacing=12)

    # =========================================================================
    # SECCIÓN 1: CATÁLOGO DE ESPECIES DE LA REGIÓN
    # =========================================================================
    tarjetas_especies = []
    for esp in ESPECIES_DETALLADAS:
        tarjetas_especies.append(
            ft.Container(
                bgcolor=COLOR_CARD,
                border_radius=14,
                padding=14,
                border=ft.Border.all(1, COLOR_BORDER),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(esp["nombre"], size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                                ft.Container(
                                    bgcolor=COLOR_CARD_ALT,
                                    border_radius=8,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    content=ft.Text(esp["tipo"], size=10, color=COLOR_ACCENT, weight=ft.FontWeight.BOLD),
                                ),
                            ],
                        ),
                        ft.Text(f"• Hábitat: {esp['habitat']}", size=12, color=COLOR_MUTED),
                        ft.Text(f"• Carnada/Señuelo: {esp['carnada_senuelo']}", size=12, color=COLOR_TEXT),
                        ft.Text(f"• Equipo: {esp['equipo']}", size=12, color=COLOR_INFO),
                        ft.Container(
                            bgcolor=COLOR_BG,
                            border_radius=8,
                            padding=8,
                            content=ft.Text(f"Tip: {esp['consejo']}", size=11, color=COLOR_WARNING),
                        ),
                    ],
                ),
            )
        )

    vista_especies = ft.Column(
        spacing=10,
        controls=[
            ft.Text("Guía de Especies de la Región", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            *tarjetas_especies,
        ],
    )

    # =========================================================================
    # SECCIÓN 2: CARNADAS ARTESANALES Y MÉTODOS DE CEBADEROS
    # =========================================================================
    tarjetas_carnadas = []
    for carn in GUIA_CARNADAS:
        tarjetas_carnadas.append(
            ft.Container(
                bgcolor=COLOR_CARD,
                border_radius=14,
                padding=14,
                border=ft.Border.all(1, COLOR_BORDER),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(carn["nombre"], size=14, weight=ft.FontWeight.BOLD, color=COLOR_ACCENT),
                        ft.Text(f"Ingredientes: {carn['ingredientes']}", size=12, color=COLOR_INFO),
                        ft.Container(
                            bgcolor=COLOR_BG,
                            border_radius=10,
                            padding=10,
                            content=ft.Text("\n".join(carn["preparacion"]), size=12, color=COLOR_TEXT),
                        ),
                    ],
                ),
            )
        )

    tarjetas_cebaderos = []
    for ceb in METODOS_CEBADEROS:
        tarjetas_cebaderos.append(
            ft.Container(
                bgcolor=COLOR_CARD,
                border_radius=14,
                padding=14,
                border=ft.Border.all(1, COLOR_PRIMARY),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(ceb["nombre"], size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXT, expand=True),
                                ft.Text(ceb["ideal_para"], size=11, color=COLOR_WARNING, weight=ft.FontWeight.BOLD),
                            ],
                        ),
                        ft.Container(
                            bgcolor=COLOR_BG,
                            border_radius=10,
                            padding=10,
                            content=ft.Text("\n".join(ceb["como_hacerlo"]), size=12, color=COLOR_TEXT),
                        ),
                    ],
                ),
            )
        )

    vista_carnadas_cebaderos = ft.Column(
        spacing=12,
        controls=[
            ft.Text("Preparación de Carnadas y Masas", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            *tarjetas_carnadas,
            ft.Text("Métodos para Hacer Cebaderos", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            *tarjetas_cebaderos,
        ],
    )

    # =========================================================================
    # SECCIÓN 3: ANALÍTICA, GUÍA VISUAL DE NUDOS, MASA Y CHECKLIST
    # =========================================================================
    tarjeta_stats = ft.Container(
        bgcolor=COLOR_CARD,
        border_radius=16,
        padding=16,
        border=ft.Border.all(1, COLOR_BORDER),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text("Analítica Táctica de Capturas", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Container(
                            expand=True,
                            bgcolor=COLOR_CARD_ALT,
                            border_radius=12,
                            padding=12,
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Capturas totales", size=11, color=COLOR_MUTED),
                                    ft.Text(str(stats["total_capturas"]), size=20, weight=ft.FontWeight.BOLD, color=COLOR_ACCENT),
                                ],
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            bgcolor=COLOR_CARD_ALT,
                            border_radius=12,
                            padding=12,
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Pieza récord", size=11, color=COLOR_MUTED),
                                    ft.Text(
                                        f"{stats['record_especie']} ({stats['record_peso']} kg)",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLOR_WARNING,
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                ft.Text(f"• Señuelo estrella: {stats['mejor_senuelo']}", size=13, color=COLOR_TEXT),
                ft.Text(f"• Color más efectivo: {stats['mejor_color']}", size=13, color=COLOR_INFO),
                ft.Text(f"• Estructura top: {stats['mejor_estructura']}", size=13, color=COLOR_TEXT),
                ft.Text(f"• Hora más productiva: {stats['mejor_hora']}", size=13, color=COLOR_ACCENT),
            ],
        ),
    )

    # --- VISOR INTERACTIVO DE TODOS LOS NUDOS (GIF + 4 PASOS) ---
    estado_nudo = {
        "nudo_idx": 0,
        "modo": "gif",  # 'gif' muestra la animación en bucle; 0..3 muestra cada paso fijo
        "media": obtener_media_nudo(NUDOS_CATALOGO[0]["slug"]),
    }

    lbl_nudo_titulo = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT)
    lbl_nudo_uso = ft.Text("", size=12, color=COLOR_INFO)
    img_nudo = ft.Image(
        src=estado_nudo["media"]["gif"],
        height=195,
        border_radius=12,
    )

    fila_selector_nudos = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=6)
    fila_botones_pasos = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=6)
    lista_pasos_texto = ft.Column(spacing=6)

    def seleccionar_nudo(idx: int):
        def _handler(e=None):
            estado_nudo["nudo_idx"] = idx
            estado_nudo["modo"] = "gif"
            estado_nudo["media"] = obtener_media_nudo(NUDOS_CATALOGO[idx]["slug"])
            refrescar_visor_nudo(True)
        return _handler

    def seleccionar_modo_paso(modo):
        def _handler(e=None):
            estado_nudo["modo"] = modo
            refrescar_visor_nudo(True)
        return _handler

    def refrescar_visor_nudo(actualizar_ui: bool = True):
        nudo_idx = estado_nudo["nudo_idx"]
        nudo = NUDOS_CATALOGO[nudo_idx]
        modo = estado_nudo["modo"]
        media = estado_nudo["media"]

        lbl_nudo_titulo.value = nudo["nombre"]
        lbl_nudo_uso.value = f"{nudo['uso']}  •  Resistencia: {nudo['resistencia']}"

        # Actualiza la imagen (GIF animado o foto de paso específico)
        if modo == "gif":
            ruta_img = media["gif"]
        else:
            ruta_img = media["pasos"][modo]

        if ruta_img and os.path.exists(ruta_img):
            img_nudo.src = ruta_img

        # Botones superiores con todos los nudos disponibles
        fila_selector_nudos.controls.clear()
        for i, item in enumerate(NUDOS_CATALOGO):
            activo = i == nudo_idx
            fila_selector_nudos.controls.append(
                ft.Button(
                    item["corto"],
                    bgcolor=COLOR_PRIMARY if activo else COLOR_CARD_ALT,
                    color=COLOR_TEXT if activo else COLOR_MUTED,
                    on_click=seleccionar_nudo(i),
                )
            )

        # Botones de control: Ver Animación GIF o Paso 1..4
        fila_botones_pasos.controls.clear()
        fila_botones_pasos.controls.append(
            ft.Button(
                "Animación",
                icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                bgcolor=COLOR_ACCENT if modo == "gif" else COLOR_CARD_ALT,
                color=COLOR_BG if modo == "gif" else COLOR_TEXT,
                on_click=seleccionar_modo_paso("gif"),
            )
        )
        for p_idx in range(4):
            es_paso_activo = modo == p_idx
            fila_botones_pasos.controls.append(
                ft.Container(
                    width=36,
                    height=34,
                    border_radius=8,
                    bgcolor=COLOR_PRIMARY if es_paso_activo else COLOR_CARD_ALT,
                    alignment=ft.Alignment(0, 0),
                    on_click=seleccionar_modo_paso(p_idx),
                    content=ft.Text(
                        f"P{p_idx + 1}",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT if es_paso_activo else COLOR_MUTED,
                    ),
                )
            )

        # Lista completa de los 4 pasos debajo para leer todo de un vistazo
        lista_pasos_texto.controls.clear()
        for p_idx, texto_paso in enumerate(nudo["pasos"]):
            resaltado = modo == p_idx
            lista_pasos_texto.controls.append(
                ft.Container(
                    bgcolor=COLOR_CARD_ALT if resaltado else COLOR_BG,
                    border_radius=8,
                    padding=8,
                    border=ft.Border.all(1, COLOR_ACCENT if resaltado else COLOR_BORDER),
                    content=ft.Text(
                        texto_paso,
                        size=12,
                        color=COLOR_TEXT,
                        weight=ft.FontWeight.BOLD if resaltado else ft.FontWeight.NORMAL,
                    ),
                )
            )

        if actualizar_ui:
            page.update()

    refrescar_visor_nudo(False)

    tarjeta_nudos = ft.Container(
        bgcolor=COLOR_CARD,
        border_radius=16,
        padding=16,
        border=ft.Border.all(1, COLOR_BORDER),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text("Guía Visual de Nudos (7 Nudos Paso a Paso)", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                fila_selector_nudos,
                lbl_nudo_titulo,
                lbl_nudo_uso,
                ft.Container(
                    bgcolor=COLOR_BG,
                    border_radius=12,
                    padding=6,
                    border=ft.Border.all(1, COLOR_PRIMARY),
                    alignment=ft.Alignment(0, 0),
                    content=img_nudo,
                ),
                fila_botones_pasos,
                lista_pasos_texto,
            ],
        ),
    )

    # --- CALCULADORA DE MASA FERMENTADA ---
    txt_kilos = ft.TextField(
        label="Kilos de base (maíz/harina)",
        value="2.0",
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )
    lbl_receta = ft.Text("", size=13, color=COLOR_TEXT)

    def calcular_masa(e=None):
        try:
            kg = float(txt_kilos.value.replace(",", "."))
        except ValueError:
            kg = 1.0
        agua_ml = int(kg * 650)
        azucar_g = int(kg * 120)
        levadura_g = int(kg * 15)
        esencia_ml = int(kg * 25)
        lbl_receta.value = (
            f"Para {kg:.1f} kg de base:\n"
            f"• Agua tibia / suero: {agua_ml} ml\n"
            f"• Papelón rallado o azúcar: {azucar_g} g\n"
            f"• Levadura o fermento: {levadura_g} g\n"
            f"• Vainilla / esencia / queso rallado: {esencia_ml} ml"
        )
        if e:
            page.update()

    calcular_masa()

    tarjeta_masa = ft.Container(
        bgcolor=COLOR_CARD,
        border_radius=16,
        padding=16,
        border=ft.Border.all(1, COLOR_BORDER),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text("Calculadora de Proporciones de Masa", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                ft.Row(
                    spacing=10,
                    controls=[
                        txt_kilos,
                        ft.Button(
                            "Calcular",
                            bgcolor=COLOR_PRIMARY,
                            color=COLOR_TEXT,
                            on_click=calcular_masa,
                        ),
                    ],
                ),
                ft.Container(
                    bgcolor=COLOR_BG,
                    border_radius=12,
                    padding=12,
                    content=lbl_receta,
                ),
            ],
        ),
    )

    # --- CHECKLIST ANTES DE SALIR ---
    items_equipo = [
        "Alicate de punta y saca-anzuelos",
        "Líderes de acero (payara/picúa) y fluorocarbono",
        "Linterna de cabeza cargada y cuchillo",
        "Agua potable, hidratación y bloqueador",
        "Cédula / documentos y bolsa impermeable",
    ]

    tarjeta_checklist = ft.Container(
        bgcolor=COLOR_CARD,
        border_radius=16,
        padding=16,
        border=ft.Border.all(1, COLOR_BORDER),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text("Checklist antes de zarpar", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                *[ft.Checkbox(label=item, active_color=COLOR_ACCENT) for item in items_equipo],
            ],
        ),
    )

    vista_herramientas = ft.Column(
        spacing=12,
        controls=[tarjeta_stats, tarjeta_nudos, tarjeta_masa, tarjeta_checklist],
    )

    # =========================================================================
    # SELECTOR SUPERIOR DE SUB-SECCIONES
    # =========================================================================
    btn_tab_especies = ft.Button("Especies", bgcolor=COLOR_PRIMARY, color=COLOR_TEXT, expand=True)
    btn_tab_carnadas = ft.Button("Carnadas/Cebos", bgcolor=COLOR_CARD_ALT, color=COLOR_MUTED, expand=True)
    btn_tab_tools = ft.Button("Herramientas", bgcolor=COLOR_CARD_ALT, color=COLOR_MUTED, expand=True)

    def seleccionar_subtab(indice: int):
        def _handler(e=None):
            botones = [btn_tab_especies, btn_tab_carnadas, btn_tab_tools]
            for i, b in enumerate(botones):
                b.bgcolor = COLOR_PRIMARY if i == indice else COLOR_CARD_ALT
                b.color = COLOR_TEXT if i == indice else COLOR_MUTED

            if indice == 0:
                contenedor_seccion.controls = [vista_especies]
            elif indice == 1:
                contenedor_seccion.controls = [vista_carnadas_cebaderos]
            else:
                contenedor_seccion.controls = [vista_herramientas]

            if e:
                page.update()
        return _handler

    btn_tab_especies.on_click = seleccionar_subtab(0)
    btn_tab_carnadas.on_click = seleccionar_subtab(1)
    btn_tab_tools.on_click = seleccionar_subtab(2)

    seleccionar_subtab(0)()

    return ft.ListView(
        expand=True,
        spacing=12,
        padding=16,
        controls=[
            ft.Row(spacing=6, controls=[btn_tab_especies, btn_tab_carnadas, btn_tab_tools]),
            contenedor_seccion,
        ],
    )
