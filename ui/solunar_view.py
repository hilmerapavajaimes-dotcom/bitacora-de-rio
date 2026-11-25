import flet as ft
from config import (
    COLOR_BG,
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
)
from services.solunar_service import calcular_datos_solunares, obtener_pronostico_semanal


def construir_solunar_view(page: ft.Page):
    hoy = calcular_datos_solunares()
    semana = obtener_pronostico_semanal()

    estrellas_str = "★" * hoy["estrellas"] + "☆" * (5 - hoy["estrellas"])
    color_nota = COLOR_ACCENT if hoy["puntaje"] >= 76 else COLOR_WARNING

    # Tarjeta principal con degradado
    tarjeta_hoy = ft.Container(
        border_radius=18,
        padding=18,
        border=ft.Border.all(1, COLOR_PRIMARY),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[COLOR_PRIMARY_DARK, COLOR_CARD],
        ),
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("CONDICIÓN LUNAR DE HOY", size=11, color=COLOR_MUTED, weight=ft.FontWeight.BOLD),
                                ft.Text(hoy["fase"], size=22, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                                ft.Text(
                                    f"Iluminación: {hoy['iluminacion']}% • Día lunar {hoy['edad_lunar']}",
                                    size=12,
                                    color=COLOR_MUTED,
                                ),
                            ],
                        ),
                        ft.Text(hoy["icono"], size=46),
                    ],
                ),
                ft.Container(
                    bgcolor=COLOR_BG,
                    border_radius=12,
                    padding=12,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Actividad de Pesca", size=12, color=COLOR_MUTED),
                                    ft.Text(
                                        f"{hoy['calificacion']} ({hoy['puntaje']}%)",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=color_nota,
                                    ),
                                ],
                            ),
                            ft.Text(estrellas_str, size=18, color=COLOR_WARNING),
                        ],
                    ),
                ),
                ft.Text(hoy["consejo"], size=13, color=COLOR_TEXT),
            ],
        ),
    )

    # Bloques de horas pico del día
    def caja_horario(titulo: str, horario: str, color_borde: str):
        return ft.Container(
            expand=True,
            bgcolor=COLOR_CARD,
            border_radius=14,
            padding=12,
            border=ft.Border.all(1, color_borde),
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text(titulo, size=11, color=COLOR_MUTED, weight=ft.FontWeight.BOLD),
                    ft.Text(horario, size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                ],
            ),
        )

    tarjeta_horas = ft.Column(
        spacing=10,
        controls=[
            ft.Text("Horas Pico de Alimentación (Hoy)", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            ft.Row(
                spacing=10,
                controls=[
                    caja_horario("PERÍODO MAYOR 1", hoy["mayor_1"], COLOR_ACCENT),
                    caja_horario("PERÍODO MAYOR 2", hoy["mayor_2"], COLOR_ACCENT),
                ],
            ),
            ft.Row(
                spacing=10,
                controls=[
                    caja_horario("PERÍODO MENOR 1", hoy["menor_1"], COLOR_INFO),
                    caja_horario("PERÍODO MENOR 2", hoy["menor_2"], COLOR_INFO),
                ],
            ),
            ft.Container(
                bgcolor=COLOR_CARD_ALT,
                border_radius=12,
                padding=10,
                content=ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.WB_TWILIGHT, color=COLOR_WARNING, size=20),
                        ft.Text(
                            "Bono de río tropical: El cambio de luz (05:30–07:30 y 17:00–18:45) dispara el ataque en superficie.",
                            size=12,
                            color=COLOR_TEXT,
                            expand=True,
                        ),
                    ],
                ),
            ),
        ],
    )

    # Pronóstico de los próximos 7 días
    lista_semana = ft.Column(spacing=8)
    for dia in semana:
        es_top = dia["puntaje"] >= 76
        badge_bg = COLOR_ACCENT if es_top else COLOR_CARD_ALT
        badge_fg = COLOR_BG if es_top else COLOR_TEXT

        lista_semana.controls.append(
            ft.Container(
                bgcolor=COLOR_CARD,
                border_radius=12,
                padding=12,
                border=ft.Border.all(1, COLOR_BORDER),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Text(dia["icono"], size=24),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            f"{dia['fecha_str']} • {dia['fase']}",
                                            weight=ft.FontWeight.BOLD,
                                            color=COLOR_TEXT,
                                        ),
                                        ft.Text(
                                            f"Pico: {dia['mayor_1']}  |  Luz: {dia['iluminacion']}%",
                                            size=11,
                                            color=COLOR_MUTED,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        ft.Container(
                            bgcolor=badge_bg,
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            content=ft.Text(
                                f"{dia['calificacion']} ({dia['puntaje']}%)",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=badge_fg,
                            ),
                        ),
                    ],
                ),
            )
        )

    return ft.ListView(
        expand=True,
        spacing=14,
        padding=16,
        controls=[
            tarjeta_hoy,
            tarjeta_horas,
            ft.Text("Pronóstico Próximos 7 Días", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
            lista_semana,
        ],
    )
