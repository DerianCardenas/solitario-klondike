"""
Constantes globales del juego Solitario Klondike.
"""

# --- Ventana ---
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 670
FPS = 60
TITLE = "Solitario Klondike"

# --- Cartas ---
CARD_WIDTH = 85
CARD_HEIGHT = 125
CARD_RADIUS = 7
CARD_GAP_X = 15
CARD_GAP_Y_FACE_DOWN = 18
CARD_GAP_Y_FACE_UP = 28

# --- Layout ---
MARGIN_TOP = 20
MARGIN_LEFT = 30
FOUNDATION_START_X = MARGIN_LEFT + CARD_WIDTH + CARD_GAP_X + CARD_WIDTH + CARD_GAP_X + 30
TABLEAU_TOP = MARGIN_TOP + CARD_HEIGHT + 30

# --- Palos y valores ---
SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
SUIT_SYMBOLS = {'hearts': '♥', 'diamonds': '♦', 'clubs': '♣', 'spades': '♠'}
SUIT_COLORS = {'hearts': 'red', 'diamonds': 'red', 'clubs': 'black', 'spades': 'black'}
VALUES = list(range(1, 14))  # 1=A, 2-10, 11=J, 12=Q, 13=K
VALUE_NAMES = {1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
               8: '8', 9: '9', 10: '10', 11: 'J', 12: 'Q', 13: 'K'}

# --- Dificultades ---
DIFFICULTIES = {
    'Principiante': {'max_passes': 5, 'draw_count': 1, 'undo_enabled': True},
    'Fácil':        {'max_passes': 4, 'draw_count': 1, 'undo_enabled': True},
    'Normal':       {'max_passes': 3, 'draw_count': 1, 'undo_enabled': True},
    'Difícil':      {'max_passes': 2, 'draw_count': 1, 'undo_enabled': True},
    'Profesional':  {'max_passes': 2, 'draw_count': 3, 'undo_enabled': False},
}
DIFFICULTY_ORDER = ['Principiante', 'Fácil', 'Normal', 'Difícil', 'Profesional']

# --- Colores base ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
DARK_GRAY = (100, 100, 100)
GREEN = (34, 120, 60)
RED = (200, 40, 40)
DARK_RED = (160, 30, 30)
BLUE = (50, 100, 200)

# --- Animación ---
ANIMATION_SPEED = 18  # pixels per frame
SNAP_THRESHOLD = 60
