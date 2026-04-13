"""
Renderizador de cartas y elementos visuales del Solitario Klondike.
"""
import math
import os
import pygame
from src.constants import (
    CARD_WIDTH, CARD_HEIGHT, CARD_RADIUS,
    VALUE_NAMES, SUIT_COLORS,
    WINDOW_WIDTH, WINDOW_HEIGHT,
)

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')


class CardRenderer:
    """Genera y cachea superficies de cartas para el tema actual."""

    def __init__(self, theme):
        self.theme = theme
        self.cache = {}
        self.back_surface = None
        self.slot_surface = None
        self._font_large = None
        self._font_small = None
        self._font_symbol = None
        self._suit_icons = {}       # suit -> Surface original (con alpha)
        self._suit_icon_cache = {}  # (suit, size) -> Surface escalada y coloreada
        self._load_suit_icons()
        self._init_fonts()
        self._build_cache()

    def _load_suit_icons(self):
        """Carga los PNG de assets/ para cada palo."""
        self._suit_icons.clear()
        self._suit_icon_cache.clear()
        for suit in ('hearts', 'diamonds', 'clubs', 'spades'):
            path = os.path.join(ASSETS_DIR, f'{suit}.png')
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self._suit_icons[suit] = img
                except Exception:
                    pass

    def _get_suit_icon(self, suit, size, color):
        """Devuelve el ícono del palo escalado y coloreado, desde caché."""
        key = (suit, size, color)
        if key not in self._suit_icon_cache:
            orig = self._suit_icons.get(suit)
            if orig is None:
                self._suit_icon_cache[key] = None
                return None
            dim = max(1, int(size * 1.8))
            scaled = pygame.transform.smoothscale(orig, (dim, dim))
            # Colorear: llenar con color destino y usar alpha del PNG como máscara
            colored = pygame.Surface((dim, dim), pygame.SRCALPHA)
            colored.fill((*color, 255))
            # Convertir RGB del scaled a blanco puro (conserva alpha original)
            white_mask = scaled.copy()
            white_mask.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
            # MULT: resultado = (color, alpha_original)
            colored.blit(white_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self._suit_icon_cache[key] = colored
        return self._suit_icon_cache[key]

    def _init_fonts(self):
        pygame.font.init()
        font_name = self.theme.get('font_name')
        fn = font_name or 'dejavusans'
        self._font_large = pygame.font.SysFont(fn, 24, bold=True)
        self._font_small = pygame.font.SysFont(fn, 14, bold=True)
        self._font_symbol = pygame.font.SysFont(fn, 30)
        self._font_corner = pygame.font.SysFont(fn, 17, bold=True)
        self._font_center = pygame.font.SysFont(fn, 44, bold=True)

    def _build_cache(self):
        self.cache.clear()
        from src.constants import SUITS, VALUES
        for suit in SUITS:
            for value in VALUES:
                key = (suit, value)
                self.cache[key] = self._render_card_front(suit, value)
        self.back_surface = self._render_card_back()
        self.slot_surface = self._render_slot()

    def reload_theme(self, theme):
        self.theme = theme
        self._suit_icon_cache.clear()
        self._init_fonts()
        self._build_cache()

    def _rounded_rect_surface(self, w, h, color, border_color=None, border_width=2, radius=CARD_RADIUS):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(surf, color, rect, border_radius=radius)
        if border_color:
            pygame.draw.rect(surf, border_color, rect, border_width, border_radius=radius)
        return surf

    def _draw_suit_shape(self, surf, suit, cx, cy, size, color):
        icon = self._get_suit_icon(suit, size, color)
        if icon is not None:
            iw, ih = icon.get_size()
            surf.blit(icon, (cx - iw // 2, cy - ih // 2))
            return
        # Fallback: dibujo programático
        s = size
        if suit == 'hearts':
            pts = []
            for i in range(40):
                t = i * math.pi * 2 / 40
                hx = 16 * (math.sin(t) ** 3)
                hy = -(13 * math.cos(t) - 5 * math.cos(2*t)
                       - 2 * math.cos(3*t) - math.cos(4*t))
                scale = s / 16.5
                pts.append((int(cx + hx * scale), int(cy + hy * scale * 0.88 + s * 0.04)))
            if len(pts) >= 3:
                pygame.draw.polygon(surf, color, pts)

        elif suit == 'diamonds':
            pts = [(cx,          cy - s * 0.55),
                   (cx + s * 0.38, cy),
                   (cx,          cy + s * 0.55),
                   (cx - s * 0.38, cy)]
            pygame.draw.polygon(surf, color, [(int(a), int(b)) for a, b in pts])

        elif suit == 'clubs':
            r = int(s * 0.25)
            pygame.draw.circle(surf, color, (int(cx),           int(cy - r * 0.82)), r)
            pygame.draw.circle(surf, color, (int(cx - r * 1.0), int(cy + r * 0.32)), r)
            pygame.draw.circle(surf, color, (int(cx + r * 1.0), int(cy + r * 0.32)), r)
            sw = max(2, int(s * 0.12))
            sh = int(s * 0.30)
            pygame.draw.rect(surf, color, (int(cx - sw // 2), int(cy + r * 0.32), sw, sh))
            bw = int(s * 0.46)
            pygame.draw.rect(surf, color,
                             (int(cx - bw // 2), int(cy + r * 0.32 + sh - 2),
                              bw, max(3, int(s * 0.13))))

        elif suit == 'spades':
            pts = []
            for i in range(40):
                t = i * math.pi * 2 / 40
                hx = 16 * (math.sin(t) ** 3)
                hy = -(13 * math.cos(t) - 5 * math.cos(2*t)
                       - 2 * math.cos(3*t) - math.cos(4*t))
                scale = (s * 0.88) / 16.5
                pts.append((int(cx + hx * scale),
                            int(cy - s * 0.10 - hy * scale * 0.82)))
            if len(pts) >= 3:
                pygame.draw.polygon(surf, color, pts)
            sw = max(2, int(s * 0.12))
            sh = int(s * 0.28)
            stem_top = int(cy + s * 0.26)
            pygame.draw.rect(surf, color, (int(cx - sw // 2), stem_top, sw, sh))
            bw = int(s * 0.46)
            pygame.draw.rect(surf, color,
                             (int(cx - bw // 2), stem_top + sh - 2,
                              bw, max(3, int(s * 0.13))))

    def _get_pip_positions(self, value):
        L, C, R = 0.0, 0.5, 1.0
        T1 = 0.0
        T2 = 0.25
        M  = 0.5
        B2 = 0.75
        B1 = 1.0
        layouts = {
            2:  [(C, T1), (C, B1)],
            3:  [(C, T1), (C, M), (C, B1)],
            4:  [(L, T1), (R, T1), (L, B1), (R, B1)],
            5:  [(L, T1), (R, T1), (C, M), (L, B1), (R, B1)],
            6:  [(L, T1), (R, T1), (L, M), (R, M), (L, B1), (R, B1)],
            7:  [(L, T1), (R, T1), (C, 0.33), (L, M), (R, M), (L, B1), (R, B1)],
            8:  [(L, T1), (R, T1), (C, 0.33), (L, M), (R, M), (C, 0.67), (L, B1), (R, B1)],
            9:  [(L, T1), (R, T1), (L, 0.33), (R, 0.33), (C, M),
                 (L, 0.67), (R, 0.67), (L, B1), (R, B1)],
            10: [(L, T1), (R, T1), (C, 0.22), (L, 0.33), (R, 0.33),
                 (L, 0.67), (R, 0.67), (C, 0.78), (L, B1), (R, B1)],
        }
        return layouts.get(value, [])

    def _render_card_front(self, suit, value):
        t = self.theme
        W, H = CARD_WIDTH, CARD_HEIGHT

        # Base con borde
        surf = self._rounded_rect_surface(W, H, t['card_front'], t['card_border'], 2)

        # Gradiente suave (brillo en la parte superior)
        gradient = pygame.Surface((W, H), pygame.SRCALPHA)
        grad_h = H // 3
        for gy in range(grad_h):
            alpha = int(22 * (1 - gy / grad_h))
            pygame.draw.line(gradient, (255, 255, 255, alpha), (3, gy), (W - 3, gy))
        surf.blit(gradient, (0, 0))

        # Borde decorativo interior
        inner = pygame.Rect(4, 4, W - 8, H - 8)
        border_col = t['card_border']
        inner_col = (border_col[0], border_col[1], border_col[2], 50)
        pygame.draw.rect(surf, inner_col, inner, 1, border_radius=CARD_RADIUS - 2)

        color_key = 'red_suit' if SUIT_COLORS[suit] == 'red' else 'black_suit'
        suit_color = t[color_key]
        val_str = VALUE_NAMES[value]

        # ── Esquina superior izquierda ──────────────────────────────────────
        val_surf = self._font_corner.render(val_str, True, suit_color)
        vw = val_surf.get_width()
        corner_cx = max(15, 5 + vw // 2)
        surf.blit(val_surf, (corner_cx - vw // 2, 4))
        self._draw_suit_shape(surf, suit, corner_cx, 30, 7, suit_color)

        # Esquina inferior derecha (rotada 180°)
        val_surf2 = pygame.transform.rotate(val_surf, 180)
        surf.blit(val_surf2, (W - corner_cx - vw // 2, H - 19))
        self._draw_suit_shape(surf, suit, W - corner_cx, H - 32, 7, suit_color)

        # ── Contenido central ──────────────────────────────────────────────
        pip_margin_x = 22
        pip_top = 32
        pip_bot = H - 32
        pip_area_h = pip_bot - pip_top
        center_x = W // 2
        center_y = H // 2

        if value == 1:
            # AS: símbolo grande con anillo decorativo
            self._draw_suit_shape(surf, suit, center_x, center_y, 30, suit_color)
            ring_color = (*suit_color, 60)
            ring_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, ring_color, (center_x, center_y), 30, 2)
            surf.blit(ring_surf, (0, 0))

        elif 2 <= value <= 10:
            positions = self._get_pip_positions(value)
            pip_size = 10 if value <= 5 else 8
            pip_area_w = W - 2 * pip_margin_x
            col_left   = pip_margin_x + pip_area_w * 0.22
            col_center = pip_margin_x + pip_area_w * 0.50
            col_right  = pip_margin_x + pip_area_w * 0.78

            for (xf, yf) in positions:
                if xf == 0.0:
                    px = col_left
                elif xf == 1.0:
                    px = col_right
                else:
                    px = col_center
                py = pip_top + yf * pip_area_h
                self._draw_suit_shape(surf, suit, int(px), int(py), pip_size, suit_color)

        else:
            # J, Q, K: marco decorativo + letra grande
            frame_margin = 14
            frame_rect = pygame.Rect(frame_margin, pip_top - 4, W - frame_margin * 2, pip_area_h + 8)
            frame_col = (*suit_color, 30)
            frame_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.rect(frame_surf, frame_col, frame_rect, border_radius=4)
            pygame.draw.rect(frame_surf, (*suit_color, 90), frame_rect, 1, border_radius=4)
            surf.blit(frame_surf, (0, 0))

            fig_font = pygame.font.SysFont(
                self.theme.get('font_name') or 'dejavusans', 50, bold=True)
            fig = fig_font.render(val_str, True, suit_color)
            fx = (W - fig.get_width()) // 2
            fy = (H - fig.get_height()) // 2
            surf.blit(fig, (fx, fy))

            pass  # Sin iconos de palo en J, Q, K

        return surf

    def _render_card_back(self):
        t = self.theme
        if 'card_back' in self.theme.custom_images:
            img = self.theme.custom_images['card_back']
            return pygame.transform.smoothscale(img, (CARD_WIDTH, CARD_HEIGHT))

        surf = self._rounded_rect_surface(
            CARD_WIDTH, CARD_HEIGHT,
            t['card_back'], t['card_border'], 2
        )
        style = t.get('card_back_style', 'crosshatch')
        pattern_color = t['card_back_pattern']
        W, H = CARD_WIDTH, CARD_HEIGHT

        if style == 'crosshatch':
            for i in range(-H, W + H, 10):
                pygame.draw.line(surf, pattern_color, (i, 0), (i + H, H), 1)
                pygame.draw.line(surf, pattern_color, (i + H, 0), (i, H), 1)
            pygame.draw.rect(surf, pattern_color, pygame.Rect(7, 7, W - 14, H - 14), 2, border_radius=5)
            pygame.draw.rect(surf, pattern_color, pygame.Rect(11, 11, W - 22, H - 22), 1, border_radius=3)
        elif style == 'gradient':
            for gy in range(6, H - 6):
                frac = gy / H
                r = int(t['card_back'][0] * (1 - frac * 0.35))
                g = int(t['card_back'][1] * (1 - frac * 0.35))
                b = int(t['card_back'][2] * (1 - frac * 0.35))
                pygame.draw.line(surf, (max(0, r), max(0, g), max(0, b)), (6, gy), (W - 6, gy))
            pygame.draw.rect(surf, pattern_color, pygame.Rect(10, 10, W - 20, H - 20), 1, border_radius=5)
            pygame.draw.rect(surf, pattern_color, pygame.Rect(14, 14, W - 28, H - 28), 1, border_radius=3)
        elif style == 'plain':
            pygame.draw.rect(surf, pattern_color, pygame.Rect(8, 8, W - 16, H - 16), 2, border_radius=5)
            for gx in range(16, W - 16, 12):
                pygame.draw.line(surf, (*pattern_color[:3], 80) if len(pattern_color) == 3 else pattern_color,
                                 (gx, 12), (gx, H - 12), 1)
            for gy in range(16, H - 16, 12):
                pygame.draw.line(surf, (*pattern_color[:3], 80) if len(pattern_color) == 3 else pattern_color,
                                 (12, gy), (W - 12, gy), 1)

        return surf

    def _render_slot(self):
        t = self.theme
        surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT)
        # Fondo semitransparente
        color = list(t['slot_color']) + [100] if len(t['slot_color']) == 3 else list(t['slot_color'])
        pygame.draw.rect(surf, color, rect, border_radius=CARD_RADIUS)
        pygame.draw.rect(surf, t['slot_border'], rect, 2, border_radius=CARD_RADIUS)
        return surf

    def get_front(self, suit, value):
        return self.cache.get((suit, value))

    def get_back(self):
        return self.back_surface

    def get_slot(self):
        return self.slot_surface

    def draw_card(self, screen, card, x=None, y=None, highlight=False, dragging=False):
        """Dibuja una carta en pantalla con soporte de animación de volteo."""
        px = int(x if x is not None else card.x)
        py = int(y if y is not None else card.y)

        shadow_offset = 5 if dragging else 2
        shadow_alpha = 100 if dragging else 55
        shadow = pygame.Surface((CARD_WIDTH + shadow_offset * 2, CARD_HEIGHT + shadow_offset * 2), pygame.SRCALPHA)
        shadow_color = (*self.theme['card_shadow'][:3], shadow_alpha)
        pygame.draw.rect(shadow, shadow_color,
                         pygame.Rect(0, 0, CARD_WIDTH + shadow_offset * 2, CARD_HEIGHT + shadow_offset * 2),
                         border_radius=CARD_RADIUS + 2)
        screen.blit(shadow, (px - shadow_offset + 1, py + shadow_offset))

        if card.flipping:
            progress = card.flip_progress
            scale = abs(math.cos(progress * math.pi))
            scale = max(scale, 0.02)
            if progress < 0.5:
                draw_surf = self.get_back()
            else:
                draw_surf = self.get_front(card.suit, card.value) if card.face_up else self.get_back()
            if draw_surf:
                scaled_w = max(1, int(CARD_WIDTH * scale))
                scaled_s = pygame.transform.scale(draw_surf, (scaled_w, CARD_HEIGHT))
                ox = (CARD_WIDTH - scaled_w) // 2
                screen.blit(scaled_s, (px + ox, py))
            return

        if card.face_up:
            surf = self.get_front(card.suit, card.value)
        else:
            surf = self.get_back()

        if surf:
            screen.blit(surf, (px, py))

        if highlight:
            hl = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(hl, (*self.theme['highlight'], 90),
                             pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT),
                             border_radius=CARD_RADIUS)
            pygame.draw.rect(hl, self.theme['highlight'],
                             pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT),
                             3, border_radius=CARD_RADIUS)
            screen.blit(hl, (px, py))

    def draw_slot(self, screen, x, y, label=''):
        screen.blit(self.get_slot(), (x, y))
        if label:
            font = self._font_corner
            txt = font.render(label, True, self.theme['slot_border'])
            tx = x + (CARD_WIDTH - txt.get_width()) // 2
            ty = y + (CARD_HEIGHT - txt.get_height()) // 2
            screen.blit(txt, (tx, ty))


class UIRenderer:
    """Renderiza elementos de interfaz (botones, textos, menús)."""

    def __init__(self, theme):
        self.theme = theme
        self._font = pygame.font.SysFont(None, 24)
        self._font_large = pygame.font.SysFont(None, 36)
        self._font_small = pygame.font.SysFont(None, 20)
        self._font_title = pygame.font.SysFont(None, 52, bold=True)

    def reload_theme(self, theme):
        self.theme = theme

    def draw_button(self, screen, rect, text, hover=False, disabled=False, accent=False):
        t = self.theme
        if accent and not disabled:
            color = self.theme.get('highlight', t['button_hover']) if hover else t['button_hover']
        else:
            color = t['button_hover'] if hover and not disabled else t['button_bg']
        if disabled:
            color = tuple(min(255, c + 40) for c in t['button_bg'])
        pygame.draw.rect(screen, color, rect, border_radius=7)
        pygame.draw.rect(screen, t['text_color'], rect, 1, border_radius=7)
        txt_color = t['button_text'] if not disabled else tuple(min(255, c + 60) for c in t['button_text'])
        txt = self._font.render(text, True, txt_color)
        tx = rect.x + (rect.width - txt.get_width()) // 2
        ty = rect.y + (rect.height - txt.get_height()) // 2
        screen.blit(txt, (tx, ty))
        return rect

    def draw_text(self, screen, text, x, y, color=None, font=None, center=False):
        f = font or self._font
        c = color or self.theme['text_color']
        surf = f.render(text, True, c)
        if center:
            x = x - surf.get_width() // 2
        screen.blit(surf, (x, y))
        return surf.get_rect(topleft=(x, y))

    def draw_panel(self, screen, rect, alpha=220):
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        bg = self.theme['menu_bg']
        pygame.draw.rect(panel, (*bg, alpha), pygame.Rect(0, 0, rect.width, rect.height), border_radius=12)
        pygame.draw.rect(panel, self.theme['menu_border'], pygame.Rect(0, 0, rect.width, rect.height), 2, border_radius=12)
        screen.blit(panel, (rect.x, rect.y))

    def draw_info_bar(self, screen, moves, elapsed, passes_left, difficulty):
        bar_rect = pygame.Rect(0, WINDOW_HEIGHT - 36, WINDOW_WIDTH, 36)
        pygame.draw.rect(screen, self.theme['menu_bg'], bar_rect)
        pygame.draw.line(screen, self.theme['menu_border'], (0, WINDOW_HEIGHT - 36), (WINDOW_WIDTH, WINDOW_HEIGHT - 36))

        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        time_str = f"Tiempo: {mins:02d}:{secs:02d}"
        move_str = f"Movimientos: {moves}"
        pass_str = f"Pasadas restantes: {passes_left}"
        diff_str = f"Dificultad: {difficulty}"

        y = WINDOW_HEIGHT - 28
        self.draw_text(screen, move_str, 15, y, font=self._font_small)
        self.draw_text(screen, time_str, 220, y, font=self._font_small)
        self.draw_text(screen, pass_str, 380, y, font=self._font_small)
        self.draw_text(screen, diff_str, 600, y, font=self._font_small)
