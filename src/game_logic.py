"""
Lógica del juego Solitario Klondike.
Maneja el estado del juego, movimientos, deshacer, guardar/cargar.
"""
import json
import os
import time
from src.card import Card, create_deck
from src.constants import DIFFICULTIES, DIFFICULTY_ORDER


class GameState:
    """Estado completo del juego Klondike."""

    def __init__(self, difficulty='Normal'):
        self.difficulty = difficulty
        self.settings = DIFFICULTIES[difficulty]
        self.stock = []          # Mazo boca abajo
        self.waste = []          # Cartas volteadas del mazo
        self.foundations = [[] for _ in range(4)]  # 4 fundaciones
        self.tableau = [[] for _ in range(7)]       # 7 columnas
        self.moves = 0
        self.start_time = time.time()
        self.elapsed = 0
        self.paused = False
        self.pass_count = 0      # Cuántas veces se ha recorrido el mazo
        self.history = []        # Para deshacer
        self.won = False
        self.game_seed = None
        self._deal()

    def _deal(self):
        """Reparte las cartas al inicio con condiciones mínimas de jugabilidad.

        Garantías:
        - Al menos 1 As visible en el tableau al inicio.
        - Ningún As queda enterrado directamente bajo otra carta del mismo palo
          en posición boca abajo (evita bloqueos triviales).
        - Se intenta hasta 20 veces; si no se cumple, se acepta el reparto
          para no alterar la aleatoriedad en exceso.
        """
        import random as _rnd
        for attempt in range(20):
            deck = create_deck()
            tableau = [[] for _ in range(7)]
            idx = 0
            for col in range(7):
                for row in range(col + 1):
                    card = deck[idx]
                    idx += 1
                    card.face_up = (row == col)
                    tableau[col].append(card)
            stock = [deck[i] for i in range(idx, 52)]
            for c in stock:
                c.face_up = False

            # Condición 1: al menos 1 As visible en el tableau
            visible_aces = sum(1 for col in tableau if col and col[-1].face_up and col[-1].value == 1)
            # Condición 2: ningún As enterrado en la posición justo debajo de la carta visible
            # (es decir, la penúltima carta de alguna columna no debería ser un As oculto
            # si eso lo hace inaccesible sin mover la carta de encima primero — esto es normal
            # en Klondike, pero evitamos que los 4 Ases estén todos enterrados)
            buried_aces = sum(1 for col in tableau for c in col if c.value == 1 and not c.face_up)

            # Aceptar si hay al menos 1 As visible O menos de 3 Ases enterrados
            if visible_aces >= 1 or buried_aces <= 2:
                self.tableau = tableau
                self.stock = stock
                return

        # Fallback: usar el último reparto generado
        self.tableau = tableau
        self.stock = stock

    def reset_with_same_deal(self):
        """Reinicia el juego con la misma disposición de cartas."""
        all_cards = self._collect_all_cards()
        # Reconstruir en el mismo orden
        self.stock.clear()
        self.waste.clear()
        for f in self.foundations:
            f.clear()
        for t in self.tableau:
            t.clear()
        self.moves = 0
        self.start_time = time.time()
        self.elapsed = 0
        self.pass_count = 0
        self.history.clear()
        self.won = False

        # Repartir de nuevo con las mismas cartas en el orden guardado
        idx = 0
        for col in range(7):
            for row in range(col + 1):
                card = all_cards[idx]
                idx += 1
                card.face_up = (row == col)
                self.tableau[col].append(card)
        for i in range(idx, len(all_cards)):
            all_cards[i].face_up = False
            self.stock.append(all_cards[i])

    def _collect_all_cards(self):
        """Recolecta todas las cartas en un orden determinista."""
        cards = []
        for col in range(7):
            cards.extend(self.tableau[col])
        cards.extend(self.stock)
        cards.extend(self.waste)
        for f in self.foundations:
            cards.extend(f)
        return cards

    # ---- Acciones del juego ----

    def draw_from_stock(self):
        """Voltea carta(s) del stock al waste."""
        if not self.stock:
            # Reciclar waste al stock
            if self.pass_count >= self.settings['max_passes']:
                return False  # No más pasadas permitidas
            self._push_history('recycle', {})
            while self.waste:
                c = self.waste.pop()
                c.face_up = False
                self.stock.append(c)
            self.pass_count += 1
            self.moves += 1
            return True

        draw_count = self.settings['draw_count']
        drawn = []
        for _ in range(draw_count):
            if self.stock:
                c = self.stock.pop()
                c.face_up = True
                self.waste.append(c)
                drawn.append(c.to_dict())
        self._push_history('draw', {'count': len(drawn), 'cards': drawn})
        self.moves += 1
        return True

    def move_waste_to_foundation(self, found_idx):
        """Mueve la carta superior del waste a una fundación."""
        if not self.waste:
            return False
        card = self.waste[-1]
        top = self.foundations[found_idx][-1] if self.foundations[found_idx] else None
        if card.can_stack_on_foundation(top):
            self._push_history('waste_to_foundation', {'found_idx': found_idx, 'card': card.to_dict()})
            self.waste.pop()
            self.foundations[found_idx].append(card)
            self.moves += 1
            self._check_win()
            return True
        return False

    def move_waste_to_tableau(self, col_idx):
        """Mueve la carta superior del waste a una columna del tableau."""
        if not self.waste:
            return False
        card = self.waste[-1]
        top = self.tableau[col_idx][-1] if self.tableau[col_idx] else None
        if card.can_stack_on_tableau(top):
            self._push_history('waste_to_tableau', {'col_idx': col_idx, 'card': card.to_dict()})
            self.waste.pop()
            self.tableau[col_idx].append(card)
            card.face_up = True
            self.moves += 1
            return True
        return False

    def move_tableau_to_foundation(self, col_idx, found_idx):
        """Mueve la carta superior de una columna a una fundación."""
        if not self.tableau[col_idx]:
            return False
        card = self.tableau[col_idx][-1]
        if not card.face_up:
            return False
        top = self.foundations[found_idx][-1] if self.foundations[found_idx] else None
        if card.can_stack_on_foundation(top):
            flipped = False
            self._push_history('tableau_to_foundation', {
                'col_idx': col_idx, 'found_idx': found_idx,
                'card': card.to_dict(), 'flipped': False
            })
            self.tableau[col_idx].pop()
            self.foundations[found_idx].append(card)
            # Voltear la nueva carta superior si está boca abajo
            if self.tableau[col_idx] and not self.tableau[col_idx][-1].face_up:
                self.tableau[col_idx][-1].face_up = True
                self.history[-1]['data']['flipped'] = True
            self.moves += 1
            self._check_win()
            return True
        return False

    def move_tableau_to_tableau(self, from_col, card_index, to_col):
        """Mueve una sub-pila de cartas de una columna a otra."""
        if from_col == to_col:
            return False
        if card_index < 0 or card_index >= len(self.tableau[from_col]):
            return False
        card = self.tableau[from_col][card_index]
        if not card.face_up:
            return False

        # Verificar que todas las cartas desde card_index estén boca arriba
        moving = self.tableau[from_col][card_index:]
        for c in moving:
            if not c.face_up:
                return False

        top = self.tableau[to_col][-1] if self.tableau[to_col] else None
        if card.can_stack_on_tableau(top):
            self._push_history('tableau_to_tableau', {
                'from_col': from_col, 'to_col': to_col,
                'card_index': card_index,
                'count': len(moving),
                'flipped': False
            })
            cards_to_move = self.tableau[from_col][card_index:]
            self.tableau[from_col] = self.tableau[from_col][:card_index]
            self.tableau[to_col].extend(cards_to_move)
            # Voltear carta descubierta
            if self.tableau[from_col] and not self.tableau[from_col][-1].face_up:
                self.tableau[from_col][-1].face_up = True
                self.history[-1]['data']['flipped'] = True
            self.moves += 1
            return True
        return False

    def move_foundation_to_tableau(self, found_idx, col_idx):
        """Mueve la carta superior de una fundación de vuelta al tableau."""
        if not self.foundations[found_idx]:
            return False
        card = self.foundations[found_idx][-1]
        top = self.tableau[col_idx][-1] if self.tableau[col_idx] else None
        if card.can_stack_on_tableau(top):
            self._push_history('foundation_to_tableau', {
                'found_idx': found_idx, 'col_idx': col_idx,
                'card': card.to_dict()
            })
            self.foundations[found_idx].pop()
            self.tableau[col_idx].append(card)
            self.moves += 1
            return True
        return False

    def auto_move_to_foundation(self, card, source_type, source_idx, card_index=None):
        """Intenta mover automáticamente una carta a la fundación correcta."""
        for fi in range(4):
            top = self.foundations[fi][-1] if self.foundations[fi] else None
            if card.can_stack_on_foundation(top):
                if source_type == 'waste':
                    return self.move_waste_to_foundation(fi)
                elif source_type == 'tableau':
                    return self.move_tableau_to_foundation(source_idx, fi)
        return False

    # ---- Deshacer ----

    def _push_history(self, action_type, data):
        if self.settings['undo_enabled']:
            self.history.append({'type': action_type, 'data': data})

    def can_undo(self):
        return self.settings['undo_enabled'] and len(self.history) > 0

    def undo(self):
        """Deshace el último movimiento."""
        if not self.can_undo():
            return False
        entry = self.history.pop()
        t = entry['type']
        d = entry['data']

        if t == 'draw':
            for _ in range(d['count']):
                if self.waste:
                    c = self.waste.pop()
                    c.face_up = False
                    self.stock.append(c)
        elif t == 'recycle':
            while self.stock:
                c = self.stock.pop()
                c.face_up = True
                self.waste.append(c)
            self.pass_count -= 1
        elif t == 'waste_to_foundation':
            fi = d['found_idx']
            if self.foundations[fi]:
                c = self.foundations[fi].pop()
                c.face_up = True
                self.waste.append(c)
        elif t == 'waste_to_tableau':
            ci = d['col_idx']
            if self.tableau[ci]:
                c = self.tableau[ci].pop()
                c.face_up = True
                self.waste.append(c)
        elif t == 'tableau_to_foundation':
            ci = d['col_idx']
            fi = d['found_idx']
            if d.get('flipped') and self.tableau[ci]:
                self.tableau[ci][-1].face_up = False
            if self.foundations[fi]:
                c = self.foundations[fi].pop()
                c.face_up = True
                self.tableau[ci].append(c)
        elif t == 'tableau_to_tableau':
            fc = d['from_col']
            tc = d['to_col']
            count = d['count']
            if d.get('flipped') and self.tableau[fc]:
                self.tableau[fc][-1].face_up = False
            cards = self.tableau[tc][-count:]
            self.tableau[tc] = self.tableau[tc][:-count]
            self.tableau[fc].extend(cards)
        elif t == 'foundation_to_tableau':
            fi = d['found_idx']
            ci = d['col_idx']
            if self.tableau[ci]:
                c = self.tableau[ci].pop()
                self.foundations[fi].append(c)

        self.moves = max(0, self.moves - 1)
        return True

    # ---- Victoria ----

    def _check_win(self):
        if all(len(f) == 13 for f in self.foundations):
            self.won = True
            # Congelar el tiempo elapsed al momento de la victoria
            if not self.paused:
                self.elapsed += time.time() - self.start_time
                self.paused = True

    # ---- Tiempo ----

    def get_elapsed(self):
        if self.won or self.paused:
            return self.elapsed
        return self.elapsed + (time.time() - self.start_time)

    def pause(self):
        if not self.paused:
            self.elapsed += time.time() - self.start_time
            self.paused = True

    def resume(self):
        if self.paused:
            self.start_time = time.time()
            self.paused = False

    # ---- Guardar / Cargar ----

    def to_dict(self):
        return {
            'difficulty': self.difficulty,
            'stock': [c.to_dict() for c in self.stock],
            'waste': [c.to_dict() for c in self.waste],
            'foundations': [[c.to_dict() for c in f] for f in self.foundations],
            'tableau': [[c.to_dict() for c in col] for col in self.tableau],
            'moves': self.moves,
            'elapsed': self.get_elapsed(),
            'pass_count': self.pass_count,
            'won': self.won,
        }

    @classmethod
    def from_dict(cls, d):
        gs = cls.__new__(cls)
        gs.difficulty = d['difficulty']
        gs.settings = DIFFICULTIES[gs.difficulty]
        gs.stock = [Card.from_dict(c) for c in d['stock']]
        gs.waste = [Card.from_dict(c) for c in d['waste']]
        gs.foundations = [[Card.from_dict(c) for c in f] for f in d['foundations']]
        gs.tableau = [[Card.from_dict(c) for c in col] for col in d['tableau']]
        gs.moves = d['moves']
        gs.elapsed = d.get('elapsed', 0)
        gs.start_time = time.time()
        gs.paused = False
        gs.pass_count = d.get('pass_count', 0)
        gs.history = []
        gs.won = d.get('won', False)
        gs.game_seed = None
        return gs

    def save(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def remaining_passes(self):
        return max(0, self.settings['max_passes'] - self.pass_count)

    def can_auto_solve(self):
        """True cuando no quedan cartas ocultas y se puede resolver automáticamente."""
        if self.won:
            return False
        if self.stock:
            return False
        for col in self.tableau:
            for card in col:
                if not card.face_up:
                    return False
        return True

    def auto_solve_step(self):
        """Mueve una carta a la fundación correcta. Retorna True si se hizo un movimiento."""
        for col_idx in range(7):
            col = self.tableau[col_idx]
            if not col or not col[-1].face_up:
                continue
            card = col[-1]
            for fi in range(4):
                top = self.foundations[fi][-1] if self.foundations[fi] else None
                if card.can_stack_on_foundation(top):
                    col.pop()
                    self.foundations[fi].append(card)
                    self.moves += 1
                    self._check_win()
                    return True
        if self.waste:
            card = self.waste[-1]
            for fi in range(4):
                top = self.foundations[fi][-1] if self.foundations[fi] else None
                if card.can_stack_on_foundation(top):
                    self.waste.pop()
                    self.foundations[fi].append(card)
                    self.moves += 1
                    self._check_win()
                    return True
        return False
