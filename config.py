import os

APP_NAME = "Bitácora de Río"
CLUB_NAME = "Los Panemas"
DEFAULT_PESCADOR = "Ilmer"

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "pesca_local.db")
MAP_CACHE_DIR = os.path.join(BASE_DIR, "map_cache")
FICHAS_DIR = os.path.join(BASE_DIR, "fichas_capturas")

# URL y clave de tu backend (Supabase / API REST)
SYNC_API_URL = ""
SYNC_API_KEY = ""

# Coordenadas iniciales del mapa (Río Orinoco / Puerto Ayacucho)
DEFAULT_LAT = 5.6639
DEFAULT_LON = -67.6236

# Paleta moderna Android Dark / Purple / Emerald
COLOR_BG = "#0D0E15"
COLOR_CARD = "#171926"
COLOR_CARD_ALT = "#202334"
COLOR_BORDER = "#2C3047"
COLOR_PRIMARY = "#7C3AED"
COLOR_PRIMARY_DARK = "#4C1D95"
COLOR_ACCENT = "#10B981"
COLOR_WARNING = "#F59E0B"
COLOR_DANGER = "#EF4444"
COLOR_INFO = "#38BDF8"
COLOR_TEXT = "#F8FAFC"
COLOR_MUTED = "#94A3B8"

# Catálogo completo de especies regionales
ESPECIES_RIO = [
    "Pavón",
    "Payara",
    "Morocoto",
    "Morocoto Piedrero",
    "Bagre Rayado",
    "Cajaro",
    "Bagre Dorado",
    "Valentón / Lau-lau",
    "Picúa / Bicuda",
    "Palometa",
    "Curvina",
    "Cubanita (Cabeza de Manteco)",
    "Cachama",
    "Caribe / Piraña",
    "Sardina / Bocachico",
    "Otra",
]

ESTADOS_RIO = [
    "Subiendo",
    "Bajando",
    "Estancado",
    "Seco / Verano",
]

CLARIDAD_AGUA = [
    "Clara",
    "Turbia / Barrosa",
    "Oscura / Negra",
]

TIPOS_SENUELO = [
    "Minnow / Media agua",
    "Popper / Superficie",
    "Crankbait / Paleta larga",
    "Jig / Vinilo",
    "Masa fermentada de maíz",
    "Masa de trigo / queso",
    "Masa de plátano maduro",
    "Carnada viva (Sardina/Bocachico)",
    "Filete / Posta de pescado",
    "Fruta / Semilla natural",
]

COLORES_SENUELO = [
    "Cromado / Plateado",
    "Payaso / Firetiger",
    "Hueso / Blanco",
    "Verde Limón / Fluorescente",
    "Dorado / Naranja",
    "Negro / Oscuro",
    "Natural / Masa",
]

ESTRUCTURAS_RIO = [
    "Boca de caño",
    "Raudal / Corriente",
    "Piedra / Laja sumergida",
    "Remanso / Pozo",
    "Palizada / Troncos",
    "Playón / Orilla",
]
