import os
import math
from config import BASE_DIR

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

NUDOS_CUSTOM_DIR = os.path.join(BASE_DIR, "assets", "nudos")
NUDOS_GEN_DIR = os.path.join(BASE_DIR, "assets", "nudos_generados")

# Paleta de colores de alto contraste
C_FONDO = (13, 14, 21)
C_GRID = (28, 32, 48)
C_MULTI = (16, 185, 129)     # Verde esmeralda: Multifilamento / Línea principal
C_LIDER = (56, 189, 248)     # Azul cielo: Fluorocarbono / Nylon
C_GUAYA = (245, 158, 11)     # Ámbar: Guaya de acero / Tope
C_METAL = (203, 213, 225)    # Gris metálico: Anzuelo / Grapa / Destorcedor
C_FLECHA = (250, 204, 21)    # Amarillo brillante: Dirección de movimiento
C_TEXTO = (248, 250, 252)
C_MUTED = (148, 163, 184)


NUDOS_CATALOGO = [
    {
        "slug": "fg",
        "corto": "Nudo FG",
        "nombre": "Nudo FG (Multifilamento a Líder)",
        "uso": "Unión ultra delgada para lanzar señuelos sin que golpee las anillas.",
        "resistencia": "95 %",
        "pasos": [
            "Paso 1: Mantén tenso el multifilamento (verde) y cruza el líder de fluorocarbono (azul) por debajo formando una X.",
            "Paso 2: Enrolla el líder alternando por encima y por debajo del multifilamento unas 18 a 20 veces bien apretadas.",
            "Paso 3: Asegura el trenzado haciendo 3 medios nudos simples abrazando tanto el multifilamento como el líder.",
            "Paso 4: Corta el sobrante del líder al ras, quema la punta para crear un tope y cierra con 4 medios nudos más.",
        ],
    },
    {
        "slug": "albright",
        "corto": "Albright",
        "nombre": "Nudo Albright (Empate rápido en el río)",
        "uso": "Unión rápida en el bote entre multifilamento y líder grueso.",
        "resistencia": "85 %",
        "pasos": [
            "Paso 1: Forma un bucle cerrado en U (unos 10 cm) con el extremo del líder grueso (azul).",
            "Paso 2: Introduce el multifilamento (verde) por el ojo del bucle y enrolla 10 vueltas sobre ambas patas.",
            "Paso 3: Pasa la punta del multifilamento de vuelta por el ojo del bucle en el mismo sentido en que entró.",
            "Paso 4: Humedece con saliva y hala firme de ambas líneas para que las vueltas se asienten sin montarse.",
        ],
    },
    {
        "slug": "uni_doble",
        "corto": "Uni Doble",
        "nombre": "Nudo Uni Doble (Línea con Línea)",
        "uso": "Empate universal y muy resistente para unir dos líneas de igual o distinto grosor.",
        "resistencia": "90 %",
        "pasos": [
            "Paso 1: Superpón unos 15 cm de ambas líneas en paralelo (verde y azul en sentidos opuestos).",
            "Paso 2: Con la punta izquierda (verde) forma un lazo y da 5 vueltas abrazando ambas líneas; cierra suave.",
            "Paso 3: Repite exactamente lo mismo con la punta derecha (azul), dando 5 vueltas por dentro de su propio lazo.",
            "Paso 4: Humedece ambos nudos y tira de las dos líneas principales hasta que los nudos choquen en el centro.",
        ],
    },
    {
        "slug": "palomar",
        "corto": "Palomar",
        "nombre": "Nudo Palomar (Señuelos, Grapas y Anzuelos)",
        "uso": "El más rápido y seguro para atar grapas, destorcedores y anzuelos.",
        "resistencia": "95 %",
        "pasos": [
            "Paso 1: Dobla unos 15 cm de línea y pasa el doblez por el ojo de la grapa o anzuelo.",
            "Paso 2: Haz un nudo simple suelto con la línea doble dejando la grapa colgando abajo.",
            "Paso 3: Abre el lazo superior y pasa la grapa o señuelo completo por dentro del bucle.",
            "Paso 4: Humedece el nudo y tira firme de la línea principal hasta cerrar por completo.",
        ],
    },
    {
        "slug": "clinch",
        "corto": "Clinch Mejorado",
        "nombre": "Nudo Clinch Mejorado (Anzuelos y Plomadas)",
        "uso": "Clásico infalible para atar anzuelos de carnada, destorcedores y señuelos en nylon o fluorocarbono.",
        "resistencia": "90 %",
        "pasos": [
            "Paso 1: Pasa la punta de la línea por el ojo del anzuelo o destorcedor dejando unos 15 cm libres.",
            "Paso 2: Da 5 a 6 vueltas enrollando la punta alrededor de la línea principal.",
            "Paso 3: Pasa la punta por el primer hueco que quedó justo encima del ojo del anzuelo.",
            "Paso 4: Pasa esa misma punta por el bucle grande recién formado, humedece y hala firme hasta apretar.",
        ],
    },
    {
        "slug": "rapala",
        "corto": "Nudo Rapala",
        "nombre": "Nudo Rapala (Lazo libre para señuelos)",
        "uso": "Deja un lazo abierto para que minnows y crankbaits naden con máxima acción.",
        "resistencia": "85 %",
        "pasos": [
            "Paso 1: Haz un nudo simple en la línea a unos 12 cm de la punta sin apretarlo.",
            "Paso 2: Pasa la punta por la argolla del señuelo y vuelve a meterla por el centro del nudo simple.",
            "Paso 3: Da 3 vueltas con la punta alrededor de la línea principal por encima del nudo.",
            "Paso 4: Pasa la punta otra vez por el nudo simple y por el bucle recién formado; humedece y aprieta.",
        ],
    },
    {
        "slug": "guaya",
        "corto": "Guaya Acero",
        "nombre": "Empate de Guaya de Acero (Payara / Picúa)",
        "uso": "Indispensable para peces de dentadura cortante usando guaya recubierta o alambre.",
        "resistencia": "100 %",
        "pasos": [
            "Paso 1: Pasa la guaya de acero (ámbar) por el tubo de crimpar (sleeve) y luego por el ojo del destorcedor.",
            "Paso 2: Regresa la punta de la guaya por dentro del tubo formando una pequeña gasa cerrada.",
            "Paso 3: Aplasta el centro del tubo con un alicate de presión (sin morder los bordes del tubo).",
            "Paso 4: Repite el mismo armado en el otro extremo con una grapa reforzada para cambiar señuelos rápido.",
        ],
    },
]


def _cargar_fuentes():
    try:
        f_title = ImageFont.truetype("arialbd.ttf", 22)
        f_label = ImageFont.truetype("arialbd.ttf", 17)
        f_small = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        f_title = ImageFont.load_default()
        f_label = ImageFont.load_default()
        f_small = ImageFont.load_default()
    return f_title, f_label, f_small


def _dibujar_flecha(draw, x1: int, y1: int, x2: int, y2: int, color=C_FLECHA):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=4)
    angulo = math.atan2(y2 - y1, x2 - x1)
    largo = 13
    a1 = angulo + math.radians(150)
    a2 = angulo - math.radians(150)
    p1 = (x2 + largo * math.cos(a1), y2 + largo * math.sin(a1))
    p2 = (x2 + largo * math.cos(a2), y2 + largo * math.sin(a2))
    draw.polygon([(x2, y2), p1, p2], fill=color)


def _dibujar_grapa(draw, cx: int, cy: int):
    draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=C_METAL, width=5)
    draw.rounded_rectangle([cx + 16, cy - 10, cx + 68, cy + 10], radius=8, outline=C_METAL, width=4)


def _renderizar_diagrama_paso(slug: str, paso_idx: int, ruta_salida: str):
    ancho, alto = 720, 360
    img = Image.new("RGB", (ancho, alto), C_FONDO)
    draw = ImageDraw.Draw(img)
    f_title, f_label, f_small = _cargar_fuentes()

    # Cuadrícula técnica de fondo
    for gx in range(0, ancho, 40):
        draw.line([(gx, 0), (gx, alto)], fill=C_GRID, width=1)
    for gy in range(0, alto, 40):
        draw.line([(0, gy), (ancho, gy)], fill=C_GRID, width=1)

    # Encabezado superior con número de paso
    draw.rounded_rectangle([20, 16, 175, 54], radius=10, fill=(124, 58, 237))
    draw.text((38, 24), f"PASO {paso_idx + 1} DE 4", fill=C_TEXTO, font=f_title)

    # Leyenda rápida de colores
    draw.rectangle([430, 26, 448, 44], fill=C_MULTI)
    draw.text((456, 25), "Multi", fill=C_MUTED, font=f_small)
    draw.rectangle([520, 26, 538, 44], fill=C_LIDER)
    draw.text((546, 25), "Líder", fill=C_MUTED, font=f_small)
    draw.rectangle([605, 26, 623, 44], fill=C_GUAYA)
    draw.text((631, 25), "Guaya", fill=C_MUTED, font=f_small)

    # --- ILUSTRACIONES ESPECÍFICAS POR NUDO Y PASO ---
    if slug == "fg":
        draw.line([(60, 190), (660, 190)], fill=C_MULTI, width=8)
        if paso_idx == 0:
            draw.line([(360, 95), (360, 295)], fill=C_LIDER, width=8)
            _dibujar_flecha(draw, 395, 120, 395, 265)
            draw.text((220, 315), "Cruza el líder formando una X con el multi tenso", fill=C_TEXTO, font=f_label)
        elif paso_idx == 1:
            for i in range(12):
                x = 240 + i * 18
                color_cruce = C_LIDER if i % 2 == 0 else (14, 116, 144)
                draw.line([(x, 165), (x + 12, 215)], fill=color_cruce, width=7)
            _dibujar_flecha(draw, 240, 140, 455, 140)
            draw.text((195, 315), "20 vueltas cruzadas alternando arriba y abajo", fill=C_TEXTO, font=f_label)
        elif paso_idx == 2:
            for i in range(12):
                x = 220 + i * 16
                draw.line([(x, 168), (x + 10, 212)], fill=C_LIDER, width=7)
            for k in range(3):
                xk = 430 + k * 24
                draw.ellipse([xk - 8, 174, xk + 8, 206], outline=C_MULTI, width=5)
            _dibujar_flecha(draw, 430, 145, 505, 145)
            draw.text((190, 315), "3 medios nudos con el multi abrazando ambas líneas", fill=C_TEXTO, font=f_label)
        else:
            for i in range(14):
                x = 210 + i * 14
                draw.line([(x, 172), (x + 8, 208)], fill=C_LIDER, width=7)
            for k in range(4):
                xk = 415 + k * 16
                draw.ellipse([xk - 6, 176, xk + 6, 204], outline=C_MULTI, width=5)
            draw.ellipse([196, 180, 214, 200], fill=C_GUAYA)
            draw.text((185, 315), "Corta sobrante, quema punta (tope) y cierra", fill=C_TEXTO, font=f_label)

    elif slug == "albright":
        if paso_idx == 0:
            draw.arc([160, 130, 520, 250], start=90, end=270, fill=C_LIDER, width=8)
            draw.line([(340, 130), (620, 130)], fill=C_LIDER, width=8)
            draw.line([(340, 250), (620, 250)], fill=C_LIDER, width=8)
            draw.text((215, 315), "Dobla el líder grueso formando un bucle en U", fill=C_TEXTO, font=f_label)
        elif paso_idx == 1:
            draw.arc([160, 130, 520, 250], start=90, end=270, fill=C_LIDER, width=8)
            draw.line([(340, 130), (620, 130)], fill=C_LIDER, width=8)
            draw.line([(340, 250), (620, 250)], fill=C_LIDER, width=8)
            for i in range(9):
                x = 270 + i * 22
                draw.line([(x, 120), (x + 10, 260)], fill=C_MULTI, width=6)
            _dibujar_flecha(draw, 270, 100, 460, 100)
            draw.text((195, 315), "Enrolla 10 vueltas con el multi sobre ambas patas", fill=C_TEXTO, font=f_label)
        elif paso_idx == 2:
            draw.arc([160, 130, 520, 250], start=90, end=270, fill=C_LIDER, width=8)
            draw.line([(340, 130), (620, 130)], fill=C_LIDER, width=8)
            draw.line([(340, 250), (620, 250)], fill=C_LIDER, width=8)
            for i in range(9):
                x = 270 + i * 22
                draw.line([(x, 120), (x + 10, 260)], fill=C_MULTI, width=6)
            draw.line([(260, 190), (110, 190)], fill=C_MULTI, width=6)
            _dibujar_flecha(draw, 230, 190, 115, 190)
            draw.text((185, 315), "Saca la punta del multi por dentro del ojo izquierdo", fill=C_TEXTO, font=f_label)
        else:
            draw.line([(80, 190), (260, 190)], fill=C_MULTI, width=8)
            for i in range(10):
                x = 260 + i * 16
                draw.rectangle([x, 168, x + 12, 212], fill=C_MULTI, outline=C_FONDO)
            draw.line([(420, 182), (640, 182)], fill=C_LIDER, width=8)
            draw.line([(420, 198), (520, 198)], fill=C_LIDER, width=7)
            _dibujar_flecha(draw, 160, 155, 85, 155)
            _dibujar_flecha(draw, 540, 155, 635, 155)
            draw.text((215, 315), "Humedece y hala firme de ambos extremos", fill=C_TEXTO, font=f_label)

    elif slug == "uni_doble":
        if paso_idx == 0:
            draw.line([(80, 175), (490, 175)], fill=C_MULTI, width=7)
            draw.line([(230, 205), (640, 205)], fill=C_LIDER, width=7)
            _dibujar_flecha(draw, 250, 145, 470, 145, C_MULTI)
            _dibujar_flecha(draw, 470, 235, 250, 235, C_LIDER)
            draw.text((185, 315), "Superpón 15 cm de ambas líneas en paralelo", fill=C_TEXTO, font=f_label)
        elif paso_idx == 1:
            draw.line([(80, 175), (490, 175)], fill=C_MULTI, width=7)
            draw.line([(230, 205), (640, 205)], fill=C_LIDER, width=7)
            draw.ellipse([235, 145, 355, 225], outline=C_MULTI, width=5)
            for i in range(5):
                x = 260 + i * 16
                draw.line([(x, 162), (x + 8, 218)], fill=C_MULTI, width=5)
            draw.text((175, 315), "Forma un lazo con la línea verde y da 5 vueltas", fill=C_TEXTO, font=f_label)
        elif paso_idx == 2:
            draw.line([(80, 175), (490, 175)], fill=C_MULTI, width=7)
            draw.line([(230, 205), (640, 205)], fill=C_LIDER, width=7)
            for i in range(5):
                x = 240 + i * 14
                draw.rectangle([x, 168, x + 10, 212], fill=C_MULTI)
            draw.ellipse([375, 145, 495, 225], outline=C_LIDER, width=5)
            for i in range(5):
                x = 400 + i * 16
                draw.line([(x, 162), (x + 8, 218)], fill=C_LIDER, width=5)
            draw.text((175, 315), "Repite el mismo lazo y 5 vueltas con la línea azul", fill=C_TEXTO, font=f_label)
        else:
            draw.line([(80, 190), (285, 190)], fill=C_MULTI, width=8)
            for i in range(5):
                x = 285 + i * 14
                draw.rectangle([x, 170, x + 11, 210], fill=C_MULTI, outline=C_FONDO)
            for i in range(5):
                x = 360 + i * 14
                draw.rectangle([x, 170, x + 11, 210], fill=C_LIDER, outline=C_FONDO)
            draw.line([(435, 190), (640, 190)], fill=C_LIDER, width=8)
            _dibujar_flecha(draw, 190, 150, 95, 150)
            _dibujar_flecha(draw, 530, 150, 625, 150)
            draw.text((185, 315), "Humedece y tira hasta que ambos nudos choquen", fill=C_TEXTO, font=f_label)

    elif slug == "palomar":
        if paso_idx == 0:
            _dibujar_grapa(draw, 520, 190)
            draw.line([(100, 175), (505, 182)], fill=C_MULTI, width=6)
            draw.line([(100, 205), (505, 198)], fill=C_MULTI, width=6)
            _dibujar_flecha(draw, 350, 150, 490, 150)
            draw.text((195, 315), "Dobla la línea y pasa el lazo por el ojo de la grapa", fill=C_TEXTO, font=f_label)
        elif paso_idx == 1:
            _dibujar_grapa(draw, 360, 255)
            draw.ellipse([290, 140, 430, 210], outline=C_MULTI, width=6)
            draw.line([(100, 175), (290, 175)], fill=C_MULTI, width=6)
            draw.line([(430, 175), (580, 175)], fill=C_MULTI, width=6)
            draw.text((185, 315), "Haz un nudo simple dejando la grapa colgando", fill=C_TEXTO, font=f_label)
        elif paso_idx == 2:
            _dibujar_grapa(draw, 360, 175)
            draw.ellipse([270, 115, 450, 235], outline=C_MULTI, width=6)
            _dibujar_flecha(draw, 360, 275, 360, 205)
            draw.text((185, 315), "Pasa la grapa o señuelo por dentro del bucle abierto", fill=C_TEXTO, font=f_label)
        else:
            _dibujar_grapa(draw, 480, 190)
            draw.ellipse([415, 172, 462, 208], fill=C_MULTI)
            draw.line([(100, 190), (415, 190)], fill=C_MULTI, width=8)
            _dibujar_flecha(draw, 220, 155, 110, 155)
            draw.text((220, 315), "Humedece y tira firme hasta apretar junto al ojo", fill=C_TEXTO, font=f_label)

    elif slug == "clinch":
        if paso_idx == 0:
            _dibujar_grapa(draw, 520, 190)
            draw.line([(100, 185), (502, 185)], fill=C_LIDER, width=7)
            draw.line([(502, 202), (320, 202)], fill=C_LIDER, width=6)
            _dibujar_flecha(draw, 470, 230, 330, 230)
            draw.text((195, 315), "Pasa la punta por el ojo y regresa hacia atrás", fill=C_TEXTO, font=f_label)
        elif paso_idx == 1:
            _dibujar_grapa(draw, 520, 190)
            draw.line([(100, 190), (502, 190)], fill=C_LIDER, width=7)
            for i in range(6):
                x = 300 + i * 24
                draw.ellipse([x, 170, x + 16, 210], outline=C_LIDER, width=5)
            _dibujar_flecha(draw, 430, 145, 305, 145)
            draw.text((195, 315), "Da 5 a 6 vueltas alrededor de la línea principal", fill=C_TEXTO, font=f_label)
        elif paso_idx == 2:
            _dibujar_grapa(draw, 520, 190)
            draw.line([(100, 190), (502, 190)], fill=C_LIDER, width=7)
            for i in range(6):
                x = 290 + i * 22
                draw.ellipse([x, 172, x + 15, 208], outline=C_LIDER, width=5)
            draw.arc([435, 130, 495, 205], start=0, end=180, fill=C_FLECHA, width=5)
            _dibujar_flecha(draw, 465, 180, 465, 125)
            draw.text((175, 315), "Mete la punta por el hueco junto al ojo y por el bucle", fill=C_TEXTO, font=f_label)
        else:
            _dibujar_grapa(draw, 500, 190)
            draw.line([(100, 190), (390, 190)], fill=C_LIDER, width=8)
            for i in range(6):
                x = 390 + i * 14
                draw.rectangle([x, 172, x + 11, 208], fill=C_LIDER, outline=C_FONDO)
            _dibujar_flecha(draw, 220, 155, 110, 155)
            draw.text((205, 315), "Humedece y desliza las vueltas hasta topar el ojo", fill=C_TEXTO, font=f_label)

    elif slug == "rapala":
        if paso_idx == 0:
            _dibujar_grapa(draw, 540, 190)
            draw.ellipse([280, 160, 340, 220], outline=C_LIDER, width=6)
            draw.line([(100, 190), (280, 190)], fill=C_LIDER, width=6)
            draw.line([(340, 190), (460, 190)], fill=C_LIDER, width=6)
            draw.text((195, 315), "Haz un nudo simple abierto antes de la argolla", fill=C_TEXTO, font=f_label)
        elif paso_idx == 1:
            _dibujar_grapa(draw, 540, 190)
            draw.ellipse([280, 160, 340, 220], outline=C_LIDER, width=6)
            draw.line([(100, 190), (522, 190)], fill=C_LIDER, width=6)
            draw.line([(522, 205), (310, 205)], fill=C_LIDER, width=6)
            _dibujar_flecha(draw, 460, 232, 325, 232)
            draw.text((175, 315), "Pasa por la argolla y regresa por el centro del nudo", fill=C_TEXTO, font=f_label)
        elif paso_idx == 2:
            _dibujar_grapa(draw, 540, 190)
            draw.ellipse([330, 160, 390, 220], outline=C_LIDER, width=6)
            for i in range(3):
                x = 245 + i * 22
                draw.ellipse([x, 170, x + 16, 210], outline=C_LIDER, width=5)
            draw.line([(100, 190), (522, 190)], fill=C_LIDER, width=6)
            draw.text((200, 315), "Da 3 vueltas alrededor de la línea principal", fill=C_TEXTO, font=f_label)
        else:
            _dibujar_grapa(draw, 520, 190)
            draw.ellipse([390, 165, 502, 215], outline=C_LIDER, width=6)
            draw.rectangle([335, 174, 390, 206], fill=C_LIDER)
            draw.line([(100, 190), (335, 190)], fill=C_LIDER, width=7)
            draw.text((185, 315), "Aprieta dejando el lazo libre para dar movimiento", fill=C_TEXTO, font=f_label)

    else:  # guaya
        if paso_idx == 0:
            _dibujar_grapa(draw, 530, 190)
            draw.rectangle([320, 174, 385, 206], fill=C_METAL)
            draw.line([(100, 190), (512, 190)], fill=C_GUAYA, width=6)
            _dibujar_flecha(draw, 220, 155, 480, 155)
            draw.text((180, 315), "Pasa la guaya por el tubo sleeve y el destorcedor", fill=C_TEXTO, font=f_label)
        elif paso_idx == 1:
            _dibujar_grapa(draw, 530, 190)
            draw.rectangle([320, 170, 385, 210], fill=C_METAL)
            draw.line([(100, 184), (512, 184)], fill=C_GUAYA, width=6)
            draw.line([(512, 198), (275, 198)], fill=C_GUAYA, width=6)
            _dibujar_flecha(draw, 460, 232, 300, 232)
            draw.text((185, 315), "Regresa la punta por dentro del tubo formando gasa", fill=C_TEXTO, font=f_label)
        elif paso_idx == 2:
            _dibujar_grapa(draw, 530, 190)
            draw.rectangle([320, 172, 385, 208], fill=C_FLECHA)
            draw.line([(100, 184), (512, 184)], fill=C_GUAYA, width=6)
            draw.line([(512, 198), (320, 198)], fill=C_GUAYA, width=6)
            _dibujar_flecha(draw, 352, 115, 352, 165)
            _dibujar_flecha(draw, 352, 265, 352, 215)
            draw.text((180, 315), "Aplasta el centro del tubo con alicate de presión", fill=C_TEXTO, font=f_label)
        else:
            _dibujar_grapa(draw, 140, 190)
            _dibujar_grapa(draw, 540, 190)
            draw.rectangle([225, 174, 275, 206], fill=C_METAL)
            draw.rectangle([425, 174, 475, 206], fill=C_METAL)
            draw.line([(160, 190), (522, 190)], fill=C_GUAYA, width=7)
            draw.text((175, 315), "Repite en el otro extremo con grapa reforzada", fill=C_TEXTO, font=f_label)

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    img.save(ruta_salida, "PNG")


def obtener_media_nudo(slug: str) -> dict:
    """
    Devuelve un diccionario con:
    - 'pasos': lista con las 4 rutas de imagen PNG/JPG para cada paso.
    - 'gif': ruta del archivo GIF animado que reproduce los 4 pasos en bucle.
    """
    os.makedirs(NUDOS_CUSTOM_DIR, exist_ok=True)
    os.makedirs(NUDOS_GEN_DIR, exist_ok=True)

    rutas_pasos = []
    for idx in range(4):
        num = idx + 1
        ruta_personalizada = None
        for ext in (".gif", ".png", ".jpg", ".jpeg", ".webp"):
            candidato = os.path.join(NUDOS_CUSTOM_DIR, f"{slug}_paso_{num}{ext}")
            if os.path.exists(candidato):
                ruta_personalizada = candidato
                break

        if ruta_personalizada:
            rutas_pasos.append(ruta_personalizada)
            continue

        ruta_gen = os.path.join(NUDOS_GEN_DIR, f"{slug}_paso_{num}.png")
        if not os.path.exists(ruta_gen) and Image is not None:
            _renderizar_diagrama_paso(slug, idx, ruta_gen)
        rutas_pasos.append(ruta_gen)

    # Genera también un GIF animado en bucle con los 4 pasos
    ruta_gif = os.path.join(NUDOS_GEN_DIR, f"{slug}_animado.gif")
    if Image is not None and not os.path.exists(ruta_gif):
        cuadros = []
        for r in rutas_pasos:
            if os.path.exists(r):
                cuadros.append(Image.open(r).convert("P", palette=Image.Palette.ADAPTIVE))
        if len(cuadros) >= 2:
            cuadros[0].save(
                ruta_gif,
                save_all=True,
                append_images=cuadros[1:],
                duration=1600,
                loop=0,
            )

    return {
        "pasos": rutas_pasos,
        "gif": ruta_gif if os.path.exists(ruta_gif) else (rutas_pasos[0] if rutas_pasos else ""),
    }
