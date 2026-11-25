import asyncio
import inspect
import urllib.parse
import webbrowser
import flet as ft
from config import (
    CLUB_NAME,
    DEFAULT_PESCADOR,
    COLOR_BG,
    COLOR_CARD,
    COLOR_CARD_ALT,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_ACCENT,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_INFO,
    COLOR_TEXT,
    COLOR_MUTED,
)
from database.db_manager import DatabaseManager
from services.sync_service import SyncService
from services.gps_service import GPSService


def construir_club_view(
    page: ft.Page,
    db: DatabaseManager,
    sync: SyncService,
    refrescar_badge,
    abrir_en_chat: bool = True,
):
    gps = GPSService(page)
    estado_chat = {"activo": True, "poll_token": 0}

    # =========================================================================
    # SUB-VISTA A: CHAT EN LÍNEA DEL CLUB
    # =========================================================================
    txt_usuario_chat = ft.TextField(
        label="Tu nombre",
        value=DEFAULT_PESCADOR,
        width=115,
        height=44,
        text_size=12,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )

    lbl_estado_red = ft.Text("Verificando conexión...", size=11, color=COLOR_INFO, weight=ft.FontWeight.W_600)

    lista_mensajes = ft.ListView(
        expand=True,
        spacing=8,
        padding=10,
        auto_scroll=True,
    )

    def actualizar_estado_red():
        en_linea = sync.hay_internet(timeout=1.2)
        if en_linea:
            lbl_estado_red.value = "🟢 En línea • Chat activo"
            lbl_estado_red.color = COLOR_ACCENT
        else:
            lbl_estado_red.value = "🟠 Sin señal • Mensajes en cola offline"
            lbl_estado_red.color = COLOR_WARNING

    def renderizar_mensajes():
        mi_nombre = (txt_usuario_chat.value or DEFAULT_PESCADOR).strip().lower()
        mensajes = db.obtener_mensajes_chat(60)
        lista_mensajes.controls.clear()

        if not mensajes:
            lista_mensajes.controls.append(
                ft.Container(
                    padding=20,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(
                        f"Bienvenido al chat del Club {CLUB_NAME}.\n"
                        "Escribe un mensaje o envía tu ubicación GPS a tus compañeros.",
                        size=12,
                        color=COLOR_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            )
            return

        for m in mensajes:
            es_mio = m["remitente"].strip().lower() == mi_nombre
            es_gps = m.get("tipo") == "gps"
            sincronizado = m.get("sync_status") == 1

            bg_burbuja = COLOR_PRIMARY if es_mio else COLOR_CARD_ALT
            if es_gps:
                bg_burbuja = "#064E3B" if es_mio else "#1E3A5F"

            icono_estado = "✓✓" if sincronizado else "🕒"
            color_estado = COLOR_ACCENT if sincronizado else COLOR_WARNING

            burbuja = ft.Container(
                bgcolor=bg_burbuja,
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                border=ft.Border.all(1, COLOR_ACCENT if es_gps else COLOR_BORDER),
                width=275,
                content=ft.Column(
                    spacing=3,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "Tú" if es_mio else m["remitente"],
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_ACCENT if not es_mio else COLOR_TEXT,
                                ),
                                ft.Text(
                                    f"{m['hora_local']} {icono_estado if es_mio else ''}",
                                    size=10,
                                    color=color_estado if es_mio else COLOR_MUTED,
                                ),
                            ],
                        ),
                        ft.Text(m["mensaje"], size=13, color=COLOR_TEXT, selectable=True),
                    ],
                ),
            )

            lista_mensajes.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.END if es_mio else ft.MainAxisAlignment.START,
                    controls=[burbuja],
                )
            )

    sync.on_chat_updated = lambda: (renderizar_mensajes(), page.update())

    txt_mensaje = ft.TextField(
        hint_text="Escribe al grupo...",
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
        on_submit=lambda e: enviar_mensaje_texto(e),
    )

    def enviar_mensaje_texto(e=None, texto_forzado: str = "", tipo: str = "texto"):
        contenido = texto_forzado if texto_forzado else txt_mensaje.value
        if not contenido or not contenido.strip():
            return

        remitente = txt_usuario_chat.value.strip() or DEFAULT_PESCADOR
        db.registrar_mensaje_chat(remitente=remitente, mensaje=contenido.strip(), tipo=tipo)
        if not texto_forzado:
            txt_mensaje.value = ""

        renderizar_mensajes()
        refrescar_badge()
        sync.sincronizar_en_segundo_plano()
        page.update()

    async def enviar_gps_al_chat(e):
        lbl_estado_red.value = "Fijando satélites GPS para el chat..."
        lbl_estado_red.color = COLOR_WARNING
        page.update()

        try:
            pos = await gps.obtener_posicion_actual()
            lat, lon = pos["lat"], pos["lon"]
            texto_gps = (
                f"📍 Mi ubicación actual en el río:\n"
                f"Lat: {lat}, Lon: {lon}\n"
                f"Mapa: https://maps.google.com/?q={lat},{lon}"
            )
            enviar_mensaje_texto(texto_forzado=texto_gps, tipo="gps")
        except Exception as ex:
            lbl_estado_red.value = f"GPS: {ex}"
            lbl_estado_red.color = COLOR_WARNING
            page.update()
            return

        actualizar_estado_red()
        page.update()

    # Botones rápidos para usar en el bote sin escribir
    chips_rapidos = ft.Row(
        scroll=ft.ScrollMode.AUTO,
        spacing=6,
        controls=[
            ft.Button(
                "📍 Mi GPS",
                bgcolor=COLOR_CARD_ALT,
                color=COLOR_ACCENT,
                on_click=enviar_gps_al_chat,
            ),
            ft.Button(
                "🎣 ¡Hay pique!",
                bgcolor=COLOR_CARD_ALT,
                color=COLOR_TEXT,
                on_click=lambda _: enviar_mensaje_texto(texto_forzado="🎣 ¡Hay buen pique activo por aquí!"),
            ),
            ft.Button(
                "🌊 Río subiendo",
                bgcolor=COLOR_CARD_ALT,
                color=COLOR_INFO,
                on_click=lambda _: enviar_mensaje_texto(texto_forzado="🌊 Ojo: el río está subiendo y trae corriente."),
            ),
            ft.Button(
                "⛵ Ya regresamos",
                bgcolor=COLOR_CARD_ALT,
                color=COLOR_WARNING,
                on_click=lambda _: enviar_mensaje_texto(texto_forzado="⛵ Ya recogimos, vamos regresando al puerto."),
            ),
        ],
    )

    actualizar_estado_red()
    renderizar_mensajes()

    # Hilo ligero de actualización periódica mientras el chat esté abierto
    async def ciclo_actualizacion_chat():
        estado_chat["poll_token"] += 1
        token_local = estado_chat["poll_token"]
        while estado_chat["activo"] and estado_chat["poll_token"] == token_local:
            await asyncio.sleep(8)
            if not estado_chat["activo"] or estado_chat["poll_token"] != token_local:
                break
            actualizar_estado_red()
            sync.sincronizar_en_segundo_plano()
            renderizar_mensajes()
            page.update()

    if hasattr(page, "run_task"):
        page.run_task(ciclo_actualizacion_chat)

    vista_chat = ft.Column(
        expand=True,
        spacing=8,
        controls=[
            ft.Container(
                bgcolor=COLOR_CARD,
                border_radius=12,
                padding=10,
                border=ft.Border.all(1, COLOR_BORDER),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(f"Chat Club {CLUB_NAME}", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                                lbl_estado_red,
                            ],
                        ),
                        txt_usuario_chat,
                    ],
                ),
            ),
            ft.Container(
                expand=True,
                bgcolor=COLOR_BG,
                border_radius=14,
                border=ft.Border.all(1, COLOR_BORDER),
                content=lista_mensajes,
            ),
            chips_rapidos,
            ft.Row(
                spacing=8,
                controls=[
                    txt_mensaje,
                    ft.IconButton(
                        icon=ft.Icons.SEND_ROUNDED,
                        icon_color=COLOR_TEXT,
                        bgcolor=COLOR_PRIMARY,
                        tooltip="Enviar mensaje",
                        on_click=enviar_mensaje_texto,
                    ),
                ],
            ),
        ],
    )

    # =========================================================================
    # SUB-VISTA B: RANKING Y DIVISOR DE GASTOS ("LA VACA")
    # =========================================================================
    ranking = db.obtener_ranking_club()

    lista_records = ft.Column(spacing=6)
    if ranking["records_especie"]:
        for r in ranking["records_especie"]:
            lista_records.controls.append(
                ft.Container(
                    bgcolor=COLOR_CARD_ALT,
                    border_radius=10,
                    padding=10,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=1,
                                controls=[
                                    ft.Text(r["especie"], weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                                    ft.Text(f"Por {r['pescador']} • {r['senuelo']}", size=11, color=COLOR_MUTED),
                                ],
                            ),
                            ft.Text(f"{r['max_peso']} kg", size=15, weight=ft.FontWeight.BOLD, color=COLOR_WARNING),
                        ],
                    ),
                )
            )
    else:
        lista_records.controls.append(
            ft.Text("Aún no hay capturas registradas para el ranking.", size=12, color=COLOR_MUTED)
        )

    lista_posiciones = ft.Column(spacing=6)
    for idx, p in enumerate(ranking["tabla_pescadores"], start=1):
        medalla = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"#{idx}"))
        lista_posiciones.controls.append(
            ft.Container(
                bgcolor=COLOR_CARD_ALT,
                border_radius=10,
                padding=10,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"{medalla}  {p['pescador']}", weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                        ft.Text(
                            f"{p['total']} capturas ({p['kilos_totales']} kg)",
                            size=12,
                            color=COLOR_ACCENT,
                            weight=ft.FontWeight.W_600,
                        ),
                    ],
                ),
            )
        )

    tarjeta_ranking = ft.Container(
        bgcolor=COLOR_CARD,
        border_radius=16,
        padding=16,
        border=ft.Border.all(1, COLOR_BORDER),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"Ranking Club {CLUB_NAME}", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                        ft.Icon(ft.Icons.EMOJI_EVENTS, color=COLOR_WARNING),
                    ],
                ),
                ft.Text("Récords por Especie", size=13, weight=ft.FontWeight.BOLD, color=COLOR_ACCENT),
                lista_records,
                ft.Text("Tabla General de Pescadores", size=13, weight=ft.FontWeight.BOLD, color=COLOR_ACCENT),
                lista_posiciones,
            ],
        ),
    )

    txt_participantes = ft.TextField(
        label="Integrantes (separados por coma)",
        value=f"{DEFAULT_PESCADOR}, Compañero 1, Compañero 2",
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )
    txt_concepto = ft.TextField(
        label="Gasto (ej. Gasolina, Hielo, Carnada)",
        expand=True,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )
    txt_monto = ft.TextField(
        label="Monto",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=105,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )
    txt_pagador = ft.TextField(
        label="Pagó",
        value=DEFAULT_PESCADOR,
        width=120,
        bgcolor=COLOR_CARD_ALT,
        border_color=COLOR_PRIMARY,
    )

    lbl_resumen_vaca = ft.Text("", size=13, color=COLOR_TEXT)
    lista_gastos_ui = ft.Column(spacing=6)
    texto_compartir_cache = {"msg": ""}

    def recalcular_vaca(e=None):
        gastos = db.obtener_gastos()
        lista_gastos_ui.controls.clear()

        nombres = [n.strip() for n in txt_participantes.value.split(",") if n.strip()]
        if not nombres:
            nombres = [DEFAULT_PESCADOR]

        aportes = {n: 0.0 for n in nombres}
        total_gastado = 0.0

        for g in gastos:
            monto = float(g["monto"])
            pagador = g["pagado_por"]
            total_gastado += monto
            aportes[pagador] = aportes.get(pagador, 0.0) + monto

            lista_gastos_ui.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"• {g['concepto']} ({pagador})", size=12, color=COLOR_MUTED),
                        ft.Text(f"{monto:.2f}", size=12, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                    ],
                )
            )

        todos_nombres = list(aportes.keys())
        cuota = total_gastado / max(1, len(todos_nombres))

        lineas = [
            f"Total jornada: {total_gastado:.2f}  |  Cuota c/u: {cuota:.2f}",
            "-----------------------------------",
        ]
        for persona, puso in aportes.items():
            saldo = puso - cuota
            if saldo > 0.01:
                lineas.append(f"• {persona}: puso {puso:.2f} -> RECIBE +{saldo:.2f}")
            elif saldo < -0.01:
                lineas.append(f"• {persona}: puso {puso:.2f} -> DEBE {abs(saldo):.2f}")
            else:
                lineas.append(f"• {persona}: puso {puso:.2f} -> AL DÍA")

        lbl_resumen_vaca.value = "\n".join(lineas)
        texto_compartir_cache["msg"] = f"*Cuenta de Salida - Club {CLUB_NAME}*\n" + "\n".join(lineas)
        if e:
            page.update()

    def agregar_gasto(e):
        if not txt_concepto.value.strip():
            return
        try:
            monto = float(txt_monto.value.replace(",", "."))
        except ValueError:
            return

        db.registrar_gasto(txt_concepto.value, txt_pagador.value or DEFAULT_PESCADOR, monto)
        txt_concepto.value = ""
        txt_monto.value = ""
        recalcular_vaca()
        page.update()

    def reiniciar_vaca(e):
        db.limpiar_gastos()
        recalcular_vaca()
        page.update()

    async def compartir_vaca_whatsapp(e):
        url = f"https://wa.me/?text={urllib.parse.quote(texto_compartir_cache['msg'])}"
        try:
            res = page.launch_url(url)
            if inspect.iscoroutine(res):
                await res
        except Exception:
            webbrowser.open(url)

    recalcular_vaca()

    tarjeta_vaca = ft.Container(
        bgcolor=COLOR_CARD,
        border_radius=16,
        padding=16,
        border=ft.Border.all(1, COLOR_BORDER),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("La Vaca (Gastos del Viaje)", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_SWEEP,
                            icon_color=COLOR_DANGER,
                            tooltip="Limpiar gastos de salida",
                            on_click=reiniciar_vaca,
                        ),
                    ],
                ),
                txt_participantes,
                ft.Row(spacing=8, controls=[txt_concepto, txt_monto]),
                ft.Row(
                    spacing=8,
                    controls=[
                        txt_pagador,
                        ft.Button(
                            "Sumar gasto",
                            icon=ft.Icons.ADD,
                            bgcolor=COLOR_PRIMARY,
                            color=COLOR_TEXT,
                            expand=True,
                            on_click=agregar_gasto,
                        ),
                    ],
                ),
                lista_gastos_ui,
                ft.Container(
                    bgcolor=COLOR_BG,
                    border_radius=12,
                    padding=12,
                    content=lbl_resumen_vaca,
                ),
                ft.Button(
                    "Enviar cuenta por WhatsApp",
                    icon=ft.Icons.SHARE,
                    bgcolor=COLOR_ACCENT,
                    color=COLOR_BG,
                    width=400,
                    on_click=compartir_vaca_whatsapp,
                ),
            ],
        ),
    )

    vista_ranking_gastos = ft.ListView(
        expand=True,
        spacing=14,
        controls=[tarjeta_ranking, tarjeta_vaca],
    )

    # =========================================================================
    # SELECTOR SUPERIOR DE SUB-SECCIONES (CHAT vs RANKING/GASTOS)
    # =========================================================================
    contenedor_subvista = ft.Container(expand=True)
    btn_chat = ft.Button("Chat del Club", icon=ft.Icons.CHAT, expand=True)
    btn_ranking = ft.Button("Ranking y Vaca", icon=ft.Icons.EMOJI_EVENTS, expand=True)

    def cambiar_subvista(idx: int):
        def _handler(e=None):
            if idx == 0:
                estado_chat["activo"] = True
                btn_chat.bgcolor = COLOR_PRIMARY
                btn_chat.color = COLOR_TEXT
                btn_ranking.bgcolor = COLOR_CARD_ALT
                btn_ranking.color = COLOR_MUTED
                contenedor_subvista.content = vista_chat
            else:
                estado_chat["activo"] = False
                btn_chat.bgcolor = COLOR_CARD_ALT
                btn_chat.color = COLOR_MUTED
                btn_ranking.bgcolor = COLOR_PRIMARY
                btn_ranking.color = COLOR_TEXT
                contenedor_subvista.content = vista_ranking_gastos

            if e:
                page.update()
        return _handler

    btn_chat.on_click = cambiar_subvista(0)
    btn_ranking.on_click = cambiar_subvista(1)

    cambiar_subvista(0 if abrir_en_chat else 1)()

    return ft.Container(
        expand=True,
        padding=14,
        content=ft.Column(
            expand=True,
            spacing=10,
            controls=[
                ft.Row(spacing=8, controls=[btn_chat, btn_ranking]),
                contenedor_subvista,
            ],
        ),
    )
