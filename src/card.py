"""
Modelo de carta y mazo para Solitario Klondike.
"""
import random
from src.constants import SUITS, VALUES, SUIT_COLORS


class Card:
    """Representa una carta individual."""

    def __init__(self, suit: str, value: int):
        self.suit = suit
        self.value = value
        self._face_up = False
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self.animating = False
        self.flipping = False
        self.flip_progress = 0.0

    @property
    def face_up(self):
        return self._face_up

    @face_up.setter
    def face_up(self, value):
        self._face_up = value

    @property
    def color(self) -> str:
        return SUIT_COLORS[self.suit]

    @property
    def is_red(self) -> bool:
        return self.color == 'red'

    @property
    def is_black(self) -> bool:
        return self.color == 'black'

    def flip(self):
        self._face_up = not self._face_up

    def start_flip_animation(self):
        """Inicia la animación de volteo (llamar DESPUÉS de cambiar face_up)."""
        self.flipping = True
        self.flip_progress = 0.0

    def update_flip(self, dt):
        if not self.flipping:
            return
        self.flip_progress += dt * 5.0
        if self.flip_progress >= 1.0:
            self.flip_progress = 1.0
            self.flipping = False

    def can_stack_on_tableau(self, other: 'Card') -> bool:
        if other is None:
            return self.value == 13
        return (self.color != other.color) and (self.value == other.value - 1)

    def can_stack_on_foundation(self, top_card: 'Card') -> bool:
        if top_card is None:
            return self.value == 1
        return (self.suit == top_card.suit) and (self.value == top_card.value + 1)

    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y

    def start_animation(self, tx, ty):
        self.target_x = tx
        self.target_y = ty
        self.animating = True

    def update_animation(self, speed=18):
        if not self.animating:
            return
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist < 1.5:
            self.x = self.target_x
            self.y = self.target_y
            self.animating = False
        else:
            factor = min(0.28, speed / max(dist, 1))
            self.x += dx * factor
            self.y += dy * factor

    def to_dict(self):
        return {
            'suit': self.suit,
            'value': self.value,
            'face_up': self._face_up,
        }

    @classmethod
    def from_dict(cls, d):
        c = cls(d['suit'], d['value'])
        c._face_up = d['face_up']
        return c

    def __repr__(self):
        from src.constants import VALUE_NAMES, SUIT_SYMBOLS
        state = '↑' if self._face_up else '↓'
        return f"{VALUE_NAMES[self.value]}{SUIT_SYMBOLS[self.suit]}{state}"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.value == other.value

    def __hash__(self):
        return hash((self.suit, self.value))


def create_deck() -> list:
    """Crea y baraja un mazo estándar de 52 cartas."""
    deck = [Card(suit, value) for suit in SUITS for value in VALUES]
    random.shuffle(deck)
    return deck
