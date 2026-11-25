import os
import math
from config import BASE_DIR

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICON_PNG_PATH = os.path.join(ASSETS_DIR, "icon.png")
ICON_ICO_PATH = os.path.join(ASSETS_DIR, "icon.ico")


def generar_icono_hd(ruta_png: str = ICON_PNG_PATH, ruta_ico: str = ICON_ICO_PATH):
    """Genera un ícono moderno 1024x1024 con anti-aliasing (supersampling 2x)."""
    if Image is None:
        return

    os.makedirs(os.path.dirname(ruta_png), exist_ok=True)
    size = 2048  # Se dibuja al doble de resolución para bordes perfectamente suaves
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Fondo degradado vertical (Violeta oscuro -> Azul noche profundo)
    grad = Image.new("RGBA", (size, size))
    g_draw = ImageDraw.Draw(grad)
    c_top = (46, 16, 101)     # #2E1065
    c_bot = (13, 17, 28)      # #0D111C
    for y in range(size):
        t = y / float(size - 1)
        r = int(c_top[0] * (1 - t) + c_bot[0] * t)
        g = int(c_top[1] * (1 - t) + c_bot[1] * t)
        b = int(c_top[2] * (1 - t) + c_bot[2] * t)
        g_draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Máscara redondeada estilo Android Adaptive Icon
    mask = Image.new("L", (size, size), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.rounded_rectangle([64, 64, size - 64, size - 64], radius=420, fill=255)
    img = Image.composite(grad, img, mask)
    draw = ImageDraw.Draw(img)

    # Borde sutil brillante
    draw.rounded_rectangle(
        [72, 72, size - 72, size - 72],
        radius=412,
        outline=(124, 58, 237, 210),
        width=22,
    )

    # 2. Aro solar / lunar dorado en el fondo
    cx, cy = size // 2, int(size * 0.44)
    draw.ellipse(
        [cx - 460, cy - 460, cx + 460, cy + 460],
        fill=(245, 158, 11, 35),
        outline=(245, 158, 11, 180),
        width=18,
    )
    draw.ellipse(
        [cx - 360, cy - 360, cx + 360, cy + 360],
        fill=(16, 185, 129, 28),
    )

    # 3. Silueta estilizada de pez depredador (Pavón / Payara) en salto dinámico
    cuerpo_pez = [
        (540, 960),   # Cola superior
        (730, 860),   # Pedúnculo caudal
        (960, 680),   # Lomo / Aleta dorsal
        (1240, 670),  # Cabeza superior
        (1490, 810),  # Hocico
        (1340, 930),  # Mandíbula inferior
        (1060, 995),  # Vientre
        (740, 945),   # Base cola inferior
        (520, 1090),  # Cola inferior
        (630, 955),   # Centro horquilla cola
    ]
    draw.polygon(cuerpo_pez, fill=(16, 185, 129, 255))  # Verde esmeralda vibrante

    # Franja dorsal y aleta pectoral de acento
    aleta_dorsal = [(930, 690), (1050, 560), (1180, 670)]
    draw.polygon(aleta_dorsal, fill=(52, 211, 153, 255))

    aleta_pectoral = [(1080, 885), (970, 1020), (1160, 955)]
    draw.polygon(aleta_pectoral, fill=(5, 150, 105, 255))

    # Ojo del pez
    draw.ellipse([1320, 765, 1378, 823], fill=(13, 17, 28, 255))
    draw.ellipse([1336, 777, 1360, 801], fill=(248, 250, 252, 255))

    # 4. Anzuelo estilizado dorado debajo del pez
    draw.arc([880, 980, 1220, 1320], start=10, end=195, fill=(250, 204, 21, 255), width=28)
    draw.line([(1206, 1140), (1206, 940)], fill=(250, 204, 21, 255), width=28)
    # Punta con muerte del anzuelo
    draw.polygon([(885, 1130), (845, 1060), (935, 1095)], fill=(250, 204, 21, 255))

    # 5. Ondas de río en la parte inferior
    for idx, (y_base, color_onda, grosor) in enumerate([
        (1420, (56, 189, 248, 235), 34),
        (1545, (16, 185, 129, 220), 30),
        (1665, (124, 58, 237, 210), 26),
    ]):
        puntos_onda = []
        for x in range(260, size - 260, 16):
            fase = (x / 190.0) + (idx * 1.1)
            y = y_base + int(math.sin(fase) * 34)
            puntos_onda.append((x, y))
        draw.line(puntos_onda, fill=color_onda, width=grosor, joint="curve")

    # Reducción suave a 1024x1024
    final_png = img.resize((1024, 1024), Image.Resampling.LANCZOS)
    final_png.save(ruta_png, "PNG")

    # Versión .ICO para barra de tareas en Windows
    final_png.save(
        ruta_ico,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (32, 32)],
    )


def asegurar_icono_app() -> str:
    """Verifica que exista assets/icon.png; si no existe, lo genera al instante."""
    if not os.path.exists(ICON_PNG_PATH):
        generar_icono_hd()
    return ICON_PNG_PATH if os.path.exists(ICON_PNG_PATH) else ""
