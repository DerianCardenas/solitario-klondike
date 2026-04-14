"""
Sistema de temas para Solitario Klondike.
Cada tema define colores, fuentes y estilos de renderizado.
Los temas pueden ser personalizados colocando archivos en /themes/<nombre>/
"""
import os
import json
import pygame

THEMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'themes')


# ── Definiciones de temas integrados ──────────────────────────────────────────

BUILTIN_THEMES = {
    'classic': {
        'name': 'Clásico',
        'background': (34, 120, 60),
        'card_front': (255, 255, 255),
        'card_back': (30, 60, 150),
        'card_back_pattern': (20, 45, 120),
        'card_border': (60, 60, 60),
        'card_shadow': (0, 0, 0, 60),
        'red_suit': (200, 30, 30),
        'black_suit': (20, 20, 20),
        'slot_color': (24, 90, 45),
        'slot_border': (18, 70, 35),
        'button_bg': (40, 90, 50),
        'button_hover': (50, 110, 65),
        'button_text': (240, 240, 220),
        'text_color': (240, 240, 220),
        'menu_bg': (25, 80, 45),
        'menu_border': (200, 180, 100),
        'highlight': (255, 215, 0),
        'font_name': None,
        'card_back_style': 'crosshatch',
    },
    'modern': {
        'name': 'Moderno',
        'background': (45, 52, 64),
        'card_front': (248, 248, 248),
        'card_back': (94, 129, 172),
        'card_back_pattern': (76, 110, 155),
        'card_border': (70, 80, 95),
        'card_shadow': (0, 0, 0, 80),
        'red_suit': (191, 97, 106),
        'black_suit': (59, 66, 82),
        'slot_color': (59, 66, 82),
        'slot_border': (76, 86, 106),
        'button_bg': (76, 86, 106),
        'button_hover': (94, 129, 172),
        'button_text': (236, 239, 244),
        'text_color': (236, 239, 244),
        'menu_bg': (46, 52, 64),
        'menu_border': (136, 192, 208),
        'highlight': (136, 192, 208),
        'font_name': None,
        'card_back_style': 'gradient',
    },
    'minimalist': {
        'name': 'Minimalista',
        'background': (240, 237, 230),
        'card_front': (255, 255, 255),
        'card_back': (180, 175, 165),
        'card_back_pattern': (165, 160, 150),
        'card_border': (200, 195, 185),
        'card_shadow': (0, 0, 0, 30),
        'red_suit': (180, 80, 70),
        'black_suit': (60, 60, 55),
        'slot_color': (220, 215, 205),
        'slot_border': (200, 195, 185),
        'button_bg': (200, 195, 185),
        'button_hover': (180, 175, 165),
        'button_text': (60, 60, 55),
        'text_color': (60, 60, 55),
        'menu_bg': (235, 230, 220),
        'menu_border': (180, 175, 165),
        'highlight': (120, 160, 140),
        'font_name': None,
        'card_back_style': 'plain',
    },
}


class Theme:
    """Gestiona el tema actual y carga temas personalizados."""

    def __init__(self, theme_name='classic', custom_card_back_path=None):
        self.current_name = theme_name
        self.data = {}
        self.custom_images = {}
        self.custom_card_back_path = custom_card_back_path  # ruta absoluta elegida por el usuario
        self.load(theme_name)

    def load(self, theme_name):
        self.current_name = theme_name
        if theme_name in BUILTIN_THEMES:
            self.data = dict(BUILTIN_THEMES[theme_name])
        else:
            # Intentar cargar tema personalizado
            theme_path = os.path.join(THEMES_DIR, theme_name)
            config_path = os.path.join(theme_path, 'theme.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    custom = json.load(f)
                # Partir del tema clásico como base
                self.data = dict(BUILTIN_THEMES['classic'])
                for key, val in custom.items():
                    if isinstance(val, list):
                        self.data[key] = tuple(val)
                    else:
                        self.data[key] = val
            else:
                self.data = dict(BUILTIN_THEMES['classic'])

        # Cargar imágenes personalizadas si existen
        self.custom_images = {}
        theme_path = os.path.join(THEMES_DIR, theme_name)
        if os.path.isdir(theme_path):
            for fname in os.listdir(theme_path):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    key = os.path.splitext(fname)[0]
                    try:
                        img = pygame.image.load(os.path.join(theme_path, fname)).convert_alpha()
                        self.custom_images[key] = img
                    except Exception:
                        pass

        # Imagen de reverso personalizada por el usuario (tiene prioridad sobre la del tema)
        self._apply_custom_card_back()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]

    def set_custom_card_back(self, path):
        """Aplica una imagen de reverso personalizada desde una ruta de archivo."""
        self.custom_card_back_path = path
        self._apply_custom_card_back()

    def clear_custom_card_back(self):
        """Elimina la imagen de reverso personalizada, vuelve al tema."""
        self.custom_card_back_path = None
        self.custom_images.pop('card_back', None)
        # Recargar la imagen del tema si existe
        theme_path = os.path.join(THEMES_DIR, self.current_name)
        for fname in ('card_back.png', 'card_back.jpg', 'card_back.jpeg'):
            full = os.path.join(theme_path, fname)
            if os.path.exists(full):
                try:
                    self.custom_images['card_back'] = pygame.image.load(full).convert_alpha()
                except Exception:
                    pass
                break

    def _apply_custom_card_back(self):
        """Carga la imagen de reverso personalizada si hay una ruta configurada."""
        if self.custom_card_back_path and os.path.exists(self.custom_card_back_path):
            try:
                img = pygame.image.load(self.custom_card_back_path).convert_alpha()
                self.custom_images['card_back'] = img
            except Exception:
                self.custom_card_back_path = None

    @staticmethod
    def available_themes():
        """Lista temas disponibles (integrados + personalizados)."""
        themes = list(BUILTIN_THEMES.keys())
        if os.path.isdir(THEMES_DIR):
            for name in os.listdir(THEMES_DIR):
                path = os.path.join(THEMES_DIR, name)
                if os.path.isdir(path) and name not in themes:
                    if os.path.exists(os.path.join(path, 'theme.json')):
                        themes.append(name)
        return themes

    @staticmethod
    def theme_display_name(theme_name):
        if theme_name in BUILTIN_THEMES:
            return BUILTIN_THEMES[theme_name]['name']
        return theme_name.replace('_', ' ').title()
