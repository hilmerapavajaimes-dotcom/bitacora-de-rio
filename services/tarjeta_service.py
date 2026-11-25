import os
from datetime import datetime
from config import CLUB_NAME, FICHAS_DIR

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None


def generar_ficha_captura(
    ruta_foto_origen: str,
    especie: str,
    peso_kg: float,
    senuelo: str,
    color_senuelo: str,
    estructura: str,
    pescador: str,
) -> str:
    """
    Estampa una tarjeta visual con los datos de la captura y el nombre del club
    sobre la foto elegida y devuelve la ruta de la imagen lista para WhatsApp.
    """
    if Image is None:
        raise RuntimeError("Instala Pillow (pip install pillow) para generar fichas con foto.")

    if not ruta_foto_origen or not os.path.exists(ruta_foto_origen):
        raise FileNotFoundError("No se encontró la fotografía seleccionada.")

    os.makedirs(FICHAS_DIR, exist_ok=True)

    img = Image.open(ruta_foto_origen).convert("RGB")
    ancho_obj = 1080
    proporcion = ancho_obj / float(img.width)
    alto_obj = int(float(img.height) * proporcion)
    img = img.resize((ancho_obj, alto_obj), Image.Resampling.LANCZOS)

    # Lienzo con banda inferior oscura estilo tarjeta deportiva
    alto_banda = 250
    lienzo = Image.new("RGB", (ancho_obj, alto_obj + alto_banda), (15, 18, 28))
    lienzo.paste(img, (0, 0))

    draw = ImageDraw.Draw(lienzo)

    # Línea de acento superior en la banda (Verde Esmeralda)
    draw.rectangle([0, alto_obj, ancho_obj, alto_obj + 8], fill=(16, 185, 129))

    # Etiqueta superior izquierda en la foto con el nombre del club
    draw.rounded_rectangle([28, 28, 430, 86], radius=14, fill=(124, 58, 237))

    try:
        font_club = ImageFont.truetype("arialbd.ttf", 28)
        font_titulo = ImageFont.truetype("arialbd.ttf", 44)
        font_sub = ImageFont.truetype("arial.ttf", 26)
        font_meta = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        font_club = ImageFont.load_default()
        font_titulo = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_meta = ImageFont.load_default()

    draw.text((48, 42), f"CLUB {CLUB_NAME.upper()}", fill=(255, 255, 255), font=font_club)

    y_base = alto_obj + 28
    draw.text(
        (36, y_base),
        f"{especie.upper()}  •  {peso_kg:.2f} KG",
        fill=(248, 250, 252),
        font=font_titulo,
    )

    detalle_senuelo = f"Señuelo: {senuelo}"
    if color_senuelo:
        detalle_senuelo += f" ({color_senuelo})"
    draw.text((36, y_base + 64), detalle_senuelo, fill=(16, 185, 129), font=font_sub)

    fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    pie = f"Pescador: {pescador}   |   Zona: {estructura or 'Río'}   |   {fecha_str}"
    draw.text((36, y_base + 115), pie, fill=(148, 163, 184), font=font_meta)

    nombre_archivo = f"ficha_{especie.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    ruta_salida = os.path.join(FICHAS_DIR, nombre_archivo)
    lienzo.save(ruta_salida, "JPEG", quality=92)
    return ruta_salida
