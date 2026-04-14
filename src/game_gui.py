"""
Interfaz gráfica principal del Solitario Klondike.
Maneja el bucle de juego, drag & drop, menús y rendering.
"""
import os
import sys
import time
import pygame
from src.constants import *
from src.card import Card
from src.game_logic import GameState
from src.theme import Theme
from src.renderer import CardRenderer, UIRenderer


SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'saves')
AUTOSAVE_PATH = os.path.join(SAVES_DIR, 'autosave.json')
CONFIG_PATH = os.path.join(SAVES_DIR, 'config.json')
TOOLBAR_H = 44


class SolitaireGUI:
    """Aplicación principal del solitario."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        self.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.fullscreen = False
        self.clock = pygame.time.Clock()
        self.running = True

        # Configuración persistente
        self.config = self._load_config()
        self.theme = Theme(self.config.get('theme', 'classic'),
                           custom_card_back_path=self.config.get('card_back_path'))
        self.card_renderer = CardRenderer(self.theme)
        self.ui = UIRenderer(self.theme)

        # Estado
        self.game = None
        self.state = 'menu'  # 'menu', 'playing', 'paused', 'win', 'settings'
        self.dragging = False
        self.drag_cards = []
        self.drag_source = None  # ('tableau', col, card_idx) o ('waste',) o ('foundation', idx)
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.hover_button = None
        self.menu_selection = 0
        self.settings_tab = 'difficulty'
        self._card_back_error = ''   # mensaje de error al cargar imagen

        # Layout positions (calculadas al inicio)
        self._calc_layout()

        # Animaciones
        self.animating_cards = []
        self.win_animation_start = 0
        self.win_cards = []

        self.auto_solving = False
        self.auto_solve_timer = 0.0

        # Doble clic
        self._last_click_time = 0.0
        self._last_click_pos = (0, 0)
        self._double_click_threshold = 0.35  # segundos

    def _calc_layout(self):
        """Calcula posiciones de todos los slots."""
        top = TOOLBAR_H + MARGIN_TOP
        self.stock_pos = (MARGIN_LEFT, top)
        self.waste_pos = (MARGIN_LEFT + CARD_WIDTH + CARD_GAP_X, top)
        self.foundation_pos = []
        for i in range(4):
            x = FOUNDATION_START_X + i * (CARD_WIDTH + CARD_GAP_X)
            self.foundation_pos.append((x, top))
        self.tableau_pos = []
        tableau_start_x = MARGIN_LEFT
        gap = (WINDOW_WIDTH - 2 * MARGIN_LEFT - 7 * CARD_WIDTH) // 6
        for i in range(7):
            x = tableau_start_x + i * (CARD_WIDTH + gap)
            self.tableau_pos.append((x, TOOLBAR_H + TABLEAU_TOP))

    # ── Configuración ─────────────────────────────────────────────────────

    def _load_config(self):
        import json
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {'theme': 'classic', 'difficulty': 'Normal'}

    def _save_config(self):
        import json
        os.makedirs(SAVES_DIR, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self.config, f)

    def _change_theme(self, name):
        self.theme.load(name)
        self.card_renderer.reload_theme(self.theme)
        self.ui.reload_theme(self.theme)
        self.config['theme'] = name
        self._save_config()

    def _change_card_back(self, path):
        """Aplica una imagen de reverso personalizada."""
        self._card_back_error = ''
        try:
            import pygame as _pg
            # Validar que pygame puede cargar la imagen
            test = _pg.image.load(path)
            self.theme.set_custom_card_back(path)
            self.card_renderer.reload_theme(self.theme)
            self.config['card_back_path'] = path
            self._save_config()
        except Exception as e:
            self._card_back_error = f'No se pudo cargar la imagen'

    def _clear_card_back(self):
        """Elimina el reverso personalizado y vuelve al del tema."""
        self.theme.clear_custom_card_back()
        self.card_renderer.reload_theme(self.theme)
        self.config.pop('card_back_path', None)
        self._card_back_error = ''
        self._save_config()

    def _open_file_dialog(self):
        """Abre el explorador de archivos integrado para seleccionar una imagen."""
        try:
            from src.file_browser import FileBrowser
            # El browser necesita dibujar sobre el display real, no el surface interno
            browser = FileBrowser(self.display, self.theme)
            path = browser.run()
            if path:
                self._change_card_back(path)
        except Exception as e:
            self._card_back_error = f'Error: {str(e)[:50]}'
    # ── Bucle principal ───────────────────────────────────────────────────

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            disp_size = self.display.get_size()
            if disp_size == (WINDOW_WIDTH, WINDOW_HEIGHT):
                self.display.blit(self.screen, (0, 0))
            else:
                scaled = pygame.transform.smoothscale(self.screen, disp_size)
                self.display.blit(scaled, (0, 0))
            pygame.display.flip()
        if self.game and not self.game.won:
            self.game.save(AUTOSAVE_PATH)
        pygame.quit()

    # ── Eventos ───────────────────────────────────────────────────────────

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.WINDOWRESIZED:
                pass  # pygame 2.x actualiza el tamaño automáticamente
            elif event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.display = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.MOUSEMOTION:
                gx, gy = self._to_game_pos(event.pos)
                self.mouse_x, self.mouse_y = gx, gy
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                gpos = self._to_game_pos(event.pos)
                now = time.time()
                dx = abs(gpos[0] - self._last_click_pos[0])
                dy = abs(gpos[1] - self._last_click_pos[1])
                if (now - self._last_click_time) < self._double_click_threshold and dx < 15 and dy < 15:
                    if self.state == 'playing':
                        self._on_double_click(gpos)
                    self._last_click_time = 0.0  # reset para no triple-clic
                else:
                    self._on_click(gpos)
                    self._last_click_time = now
                    self._last_click_pos = gpos
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._on_release(self._to_game_pos(event.pos))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.state == 'playing':
                    self._try_auto_foundation(self._to_game_pos(event.pos))
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _to_game_pos(self, pos):
        dw, dh = self.display.get_size()
        return (pos[0] * WINDOW_WIDTH / dw, pos[1] * WINDOW_HEIGHT / dh)

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        pygame.display.toggle_fullscreen()

    def _on_click(self, pos):
        x, y = pos
        if self.state == 'menu':
            self._menu_click(x, y)
        elif self.state == 'settings':
            self._settings_click(x, y)
        elif self.state == 'playing':
            self._game_click(x, y)
        elif self.state == 'win':
            self._win_click(x, y)

    def _on_release(self, pos):
        if self.state == 'playing' and self.dragging:
            self._drop_cards(pos)
            self.dragging = False
            self.drag_cards = []
            self.drag_source = None

    def _on_key(self, key):
        if key == pygame.K_ESCAPE:
            if self.state == 'playing':
                self.game.pause()
                self.state = 'menu'
            elif self.state == 'settings':
                self.state = 'menu'
            elif self.state == 'menu':
                if self.game:
                    self.game.resume()
                    self.state = 'playing'
        elif key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
            if self.state == 'playing' and self.game:
                self.game.undo()
        elif key == pygame.K_n and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self._new_game()
        elif key == pygame.K_F11:
            self._toggle_fullscreen()

    # ── Lógica de click en el juego ───────────────────────────────────────

    def _game_click(self, x, y):
        # Botones superiores de la barra
        btn_rects = self._get_toolbar_rects()
        for name, rect in btn_rects.items():
            if rect.collidepoint(x, y):
                self._toolbar_action(name)
                return

        # Stock click
        sx, sy = self.stock_pos
        if sx <= x <= sx + CARD_WIDTH and sy <= y <= sy + CARD_HEIGHT:
            self.game.draw_from_stock()
            return

        # Waste - iniciar drag
        if self.game.waste:
            wx, wy = self._waste_card_pos()
            if wx <= x <= wx + CARD_WIDTH and wy <= y <= wy + CARD_HEIGHT:
                card = self.game.waste[-1]
                self.dragging = True
                self.drag_cards = [card]
                self.drag_source = ('waste',)
                self.drag_offset_x = x - wx
                self.drag_offset_y = y - wy
                return

        # Foundation - iniciar drag
        for fi, (fx, fy) in enumerate(self.foundation_pos):
            if fx <= x <= fx + CARD_WIDTH and fy <= y <= fy + CARD_HEIGHT:
                if self.game.foundations[fi]:
                    card = self.game.foundations[fi][-1]
                    self.dragging = True
                    self.drag_cards = [card]
                    self.drag_source = ('foundation', fi)
                    self.drag_offset_x = x - fx
                    self.drag_offset_y = y - fy
                    return

        # Tableau - iniciar drag
        for col_idx in range(7):
            col = self.game.tableau[col_idx]
            if not col:
                continue
            tx, ty = self.tableau_pos[col_idx]
            # Recorrer de abajo hacia arriba
            for ci in range(len(col) - 1, -1, -1):
                card = col[ci]
                card_y = ty + self._card_y_offset(col, ci)
                card_h = CARD_HEIGHT if ci == len(col) - 1 else (
                    CARD_GAP_Y_FACE_UP if card.face_up else CARD_GAP_Y_FACE_DOWN
                )
                if tx <= x <= tx + CARD_WIDTH and card_y <= y <= card_y + card_h:
                    if card.face_up:
                        # Drag sub-pila
                        self.dragging = True
                        self.drag_cards = col[ci:]
                        self.drag_source = ('tableau', col_idx, ci)
                        self.drag_offset_x = x - tx
                        self.drag_offset_y = y - card_y
                        return
                    elif ci == len(col) - 1:
                        # Voltear carta boca abajo (no debería pasar en juego normal)
                        pass
                    break

    def _drop_cards(self, pos):
        """Suelta las cartas arrastradas."""
        if not self.drag_cards or not self.drag_source:
            return

        x, y = pos
        dropped = False

        # Intentar soltar en fundación (solo 1 carta)
        if len(self.drag_cards) == 1:
            for fi, (fx, fy) in enumerate(self.foundation_pos):
                if fx - 20 <= x <= fx + CARD_WIDTH + 20 and fy - 20 <= y <= fy + CARD_HEIGHT + 20:
                    dropped = self._execute_move_to_foundation(fi)
                    if dropped:
                        break

        # Intentar soltar en tableau
        if not dropped:
            for col_idx in range(7):
                tx, ty = self.tableau_pos[col_idx]
                col = self.game.tableau[col_idx]
                # Calcular área de drop
                col_bottom = ty + (self._card_y_offset(col, len(col) - 1) + CARD_HEIGHT if col else CARD_HEIGHT)
                if tx - 15 <= x <= tx + CARD_WIDTH + 15 and ty - 15 <= y <= col_bottom + 15:
                    dropped = self._execute_move_to_tableau(col_idx)
                    if dropped:
                        break

    def _execute_move_to_foundation(self, fi):
        src = self.drag_source
        if src[0] == 'waste':
            return self.game.move_waste_to_foundation(fi)
        elif src[0] == 'tableau':
            return self.game.move_tableau_to_foundation(src[1], fi)
        elif src[0] == 'foundation':
            return False  # No mover entre fundaciones
        return False

    def _execute_move_to_tableau(self, col_idx):
        src = self.drag_source
        if src[0] == 'waste':
            return self.game.move_waste_to_tableau(col_idx)
        elif src[0] == 'tableau':
            return self.game.move_tableau_to_tableau(src[1], src[2], col_idx)
        elif src[0] == 'foundation':
            return self.game.move_foundation_to_tableau(src[1], col_idx)
        return False

    def _try_auto_foundation(self, pos):
        """Intento automático de mover a fundación con clic derecho."""
        x, y = pos
        # Waste
        if self.game.waste:
            wx, wy = self._waste_card_pos()
            if wx <= x <= wx + CARD_WIDTH and wy <= y <= wy + CARD_HEIGHT:
                card = self.game.waste[-1]
                self.game.auto_move_to_foundation(card, 'waste', 0)
                return

        # Tableau top card
        for col_idx in range(7):
            col = self.game.tableau[col_idx]
            if not col:
                continue
            tx, ty = self.tableau_pos[col_idx]
            card = col[-1]
            card_y = ty + self._card_y_offset(col, len(col) - 1)
            if tx <= x <= tx + CARD_WIDTH and card_y <= y <= card_y + CARD_HEIGHT:
                if card.face_up:
                    self.game.auto_move_to_foundation(card, 'tableau', col_idx)
                    return

    def _on_double_click(self, pos):
        """Doble clic: mueve la carta al lugar ideal (fundación o tableau)."""
        x, y = pos
        # Waste
        if self.game.waste:
            wx, wy = self._waste_card_pos()
            if wx <= x <= wx + CARD_WIDTH and wy <= y <= wy + CARD_HEIGHT:
                card = self.game.waste[-1]
                # Intentar fundación primero
                if self.game.auto_move_to_foundation(card, 'waste', 0):
                    return
                # Luego tableau
                for col_idx in range(7):
                    if self.game.move_waste_to_tableau(col_idx):
                        return
                return

        # Tableau
        for col_idx in range(7):
            col = self.game.tableau[col_idx]
            if not col:
                continue
            tx, ty = self.tableau_pos[col_idx]
            card = col[-1]
            card_y = ty + self._card_y_offset(col, len(col) - 1)
            if tx <= x <= tx + CARD_WIDTH and card_y <= y <= card_y + CARD_HEIGHT:
                if card.face_up:
                    # Intentar fundación primero
                    if self.game.auto_move_to_foundation(card, 'tableau', col_idx):
                        return
                    # Luego mover a otro tableau
                    for dest_col in range(7):
                        if dest_col == col_idx:
                            continue
                        if self.game.move_tableau_to_tableau(col_idx, len(col) - 1, dest_col):
                            return
                return

        # Foundation (doble clic devuelve al tableau)
        for fi, (fx, fy) in enumerate(self.foundation_pos):
            if fx <= x <= fx + CARD_WIDTH and fy <= y <= fy + CARD_HEIGHT:
                if self.game.foundations[fi]:
                    card = self.game.foundations[fi][-1]
                    for dest_col in range(7):
                        if self.game.move_foundation_to_tableau(fi, dest_col):
                            return
                return

    # ── Posiciones de cartas ──────────────────────────────────────────────

    def _card_y_offset(self, col, idx):
        offset = 0
        for i in range(idx):
            if col[i].face_up:
                offset += CARD_GAP_Y_FACE_UP
            else:
                offset += CARD_GAP_Y_FACE_DOWN
        return offset

    def _waste_card_pos(self):
        wx, wy = self.waste_pos
        # En modo 3 cartas, mostrar las últimas 3
        draw_count = self.game.settings['draw_count']
        if draw_count == 3 and len(self.game.waste) > 1:
            offset = min(len(self.game.waste) - 1, 2) * 22
            return wx + offset, wy
        return wx, wy

    # ── Toolbar ───────────────────────────────────────────────────────────

    def _get_toolbar_rects(self):
        rects = {}
        bw, bh = 88, 28
        y = (TOOLBAR_H - bh) // 2
        names = ['Deshacer', 'Guardar', 'Nuevo', 'Menú']
        if self.game and self.game.can_auto_solve():
            names.append('Auto Resolver')
        total_w = len(names) * (bw + 6) - 6
        start_x = WINDOW_WIDTH - total_w - 10
        for i, name in enumerate(names):
            rects[name] = pygame.Rect(start_x + i * (bw + 6), y, bw, bh)
        return rects

    def _toolbar_action(self, name):
        if name == 'Deshacer':
            if self.game.can_undo():
                self.game.undo()
        elif name == 'Menú':
            self.game.pause()
            self.state = 'menu'
        elif name == 'Guardar':
            self.game.save(AUTOSAVE_PATH)
        elif name == 'Nuevo':
            self._new_game()
        elif name == 'Auto Resolver':
            self.auto_solving = True
            self.auto_solve_timer = 0.0

    # ── Menú ──────────────────────────────────────────────────────────────

    def _menu_click(self, x, y):
        btns = self._get_menu_buttons()
        for name, rect in btns.items():
            if rect.collidepoint(x, y):
                if name == 'Continuar' and self.game:
                    self.game.resume()
                    self.state = 'playing'
                elif name == 'Nuevo Juego':
                    self._new_game()
                elif name == 'Reiniciar':
                    if self.game:
                        self.game.reset_with_same_deal()
                        self.state = 'playing'
                elif name == 'Cargar Partida':
                    self._load_game()
                elif name == 'Configuración':
                    self.state = 'settings'
                elif name == 'Salir':
                    self.running = False

    def _get_menu_buttons(self):
        btns = {}
        bw, bh = 260, 44
        cx = WINDOW_WIDTH // 2 - bw // 2
        start_y = 230
        gap = 54
        names = []
        if self.game:
            names.append('Continuar')
        names.extend(['Nuevo Juego'])
        if self.game:
            names.append('Reiniciar')
        if os.path.exists(AUTOSAVE_PATH):
            names.append('Cargar Partida')
        names.extend(['Configuración', 'Salir'])
        for i, name in enumerate(names):
            btns[name] = pygame.Rect(cx, start_y + i * gap, bw, bh)
        return btns

    def _new_game(self):
        diff = self.config.get('difficulty', 'Normal')
        self.game = GameState(diff)
        self.state = 'playing'

    def _load_game(self):
        try:
            self.game = GameState.load(AUTOSAVE_PATH)
            self.state = 'playing'
        except Exception as e:
            print(f"Error al cargar: {e}")

    # ── Settings ──────────────────────────────────────────────────────────

    def _settings_click(self, x, y):
        btns = self._get_settings_elements()
        # Tabs
        for tab_name, rect in btns.get('tabs', {}).items():
            if rect.collidepoint(x, y):
                self.settings_tab = tab_name
                self._card_back_error = ''
                return
        # Items
        for item_name, rect in btns.get('items', {}).items():
            if rect.collidepoint(x, y):
                if self.settings_tab == 'difficulty':
                    self.config['difficulty'] = item_name
                    self._save_config()
                elif self.settings_tab == 'theme':
                    self._change_theme(item_name)
                return
        # Botones de reverso
        if self.settings_tab == 'card_back':
            if btns.get('btn_choose') and btns['btn_choose'].collidepoint(x, y):
                self._open_file_dialog()
                return
            if btns.get('btn_clear') and btns['btn_clear'].collidepoint(x, y):
                self._clear_card_back()
                return
        # Back
        if btns.get('back') and btns['back'].collidepoint(x, y):
            self.state = 'menu'

    def _get_settings_elements(self):
        elements = {'tabs': {}, 'items': {}}
        panel_x, panel_y = 200, 100
        panel_w, panel_h = 700, 500

        # Tabs
        tab_names = ['difficulty', 'theme', 'card_back']
        tab_labels = {'difficulty': 'Dificultad', 'theme': 'Tema Visual', 'card_back': 'Reverso'}
        for i, tn in enumerate(tab_names):
            elements['tabs'][tn] = pygame.Rect(panel_x + 20 + i * 160, panel_y + 15, 150, 36)

        # Items según tab
        item_y = panel_y + 80
        if self.settings_tab == 'difficulty':
            for i, diff in enumerate(DIFFICULTY_ORDER):
                elements['items'][diff] = pygame.Rect(panel_x + 40, item_y + i * 55, panel_w - 80, 45)
        elif self.settings_tab == 'theme':
            themes = Theme.available_themes()
            for i, t_name in enumerate(themes):
                elements['items'][t_name] = pygame.Rect(panel_x + 40, item_y + i * 55, panel_w - 80, 45)
        elif self.settings_tab == 'card_back':
            elements['btn_choose'] = pygame.Rect(panel_x + 40, item_y, 260, 44)
            elements['btn_clear'] = pygame.Rect(panel_x + 320, item_y, 200, 44)

        elements['back'] = pygame.Rect(panel_x + panel_w - 120, panel_y + panel_h - 50, 100, 36)
        return elements

    # ── Win screen ────────────────────────────────────────────────────────

    def _win_click(self, x, y):
        cx = WINDOW_WIDTH // 2
        btn_rect = pygame.Rect(cx - 100, 450, 200, 44)
        if btn_rect.collidepoint(x, y):
            self._new_game()
        btn2 = pygame.Rect(cx - 100, 510, 200, 44)
        if btn2.collidepoint(x, y):
            self.game = None
            self.state = 'menu'

    # ── Update ────────────────────────────────────────────────────────────

    def _update(self, dt):
        if self.state == 'playing' and self.game:
            if self.game.won and self.state != 'win':
                self.state = 'win'
                self.win_animation_start = time.time()

            if self.auto_solving:
                if not self.game.can_auto_solve() and not self.game.won:
                    self.auto_solving = False
                else:
                    self.auto_solve_timer -= dt
                    if self.auto_solve_timer <= 0:
                        moved = self.game.auto_solve_step()
                        if not moved:
                            self.auto_solving = False
                        self.auto_solve_timer = 0.15

    # ── Draw ──────────────────────────────────────────────────────────────

    def _draw(self):
        self.screen.fill(self.theme['background'])

        if self.state == 'playing' and self.game:
            self._draw_game()
        elif self.state == 'menu':
            self._draw_menu()
        elif self.state == 'settings':
            self._draw_settings()
        elif self.state == 'win':
            self._draw_game()
            self._draw_win_overlay()

    def _draw_game(self):
        g = self.game
        cr = self.card_renderer

        # Slot del stock
        cr.draw_slot(self.screen, *self.stock_pos, label='' if g.stock else 'X')
        if g.stock:
            cr.draw_card(self.screen, g.stock[-1], *self.stock_pos)
            # Indicador de cantidad
            if len(g.stock) > 1:
                self.ui.draw_text(self.screen, str(len(g.stock)),
                                  self.stock_pos[0] + CARD_WIDTH - 8,
                                  self.stock_pos[1] - 2,
                                  font=self.ui._font_small)

        # Slot del waste
        cr.draw_slot(self.screen, *self.waste_pos)
        draw_count = g.settings['draw_count']
        if g.waste:
            if draw_count == 3:
                # Mostrar hasta 3 cartas desplegadas
                start = max(0, len(g.waste) - 3)
                for i, wi in enumerate(range(start, len(g.waste))):
                    card = g.waste[wi]
                    wx = self.waste_pos[0] + i * 22
                    wy = self.waste_pos[1]
                    is_top = (wi == len(g.waste) - 1)
                    # No dibujar si está siendo arrastrada
                    if self.dragging and self.drag_source and self.drag_source[0] == 'waste' and is_top:
                        continue
                    cr.draw_card(self.screen, card, wx, wy)
            else:
                card = g.waste[-1]
                if not (self.dragging and self.drag_source and self.drag_source[0] == 'waste'):
                    cr.draw_card(self.screen, card, *self.waste_pos)

        # Fundaciones
        suit_labels = ['A', 'A', 'A', 'A']
        for fi in range(4):
            fx, fy = self.foundation_pos[fi]
            cr.draw_slot(self.screen, fx, fy, label=suit_labels[fi])
            if g.foundations[fi]:
                top = g.foundations[fi][-1]
                if self.dragging and self.drag_source and self.drag_source[0] == 'foundation' and self.drag_source[1] == fi:
                    if len(g.foundations[fi]) > 1:
                        cr.draw_card(self.screen, g.foundations[fi][-2], fx, fy)
                else:
                    cr.draw_card(self.screen, top, fx, fy)

        # Tableau
        for col_idx in range(7):
            tx, ty = self.tableau_pos[col_idx]
            col = g.tableau[col_idx]
            cr.draw_slot(self.screen, tx, ty, label='K' if not col else '')
            for ci, card in enumerate(col):
                # No dibujar cartas que están siendo arrastradas
                if (self.dragging and self.drag_source and
                        self.drag_source[0] == 'tableau' and
                        self.drag_source[1] == col_idx and
                        ci >= self.drag_source[2]):
                    continue
                cy = ty + self._card_y_offset(col, ci)
                cr.draw_card(self.screen, card, tx, cy)

        # Cartas arrastradas
        if self.dragging and self.drag_cards:
            for i, card in enumerate(self.drag_cards):
                dx = self.mouse_x - self.drag_offset_x
                dy = self.mouse_y - self.drag_offset_y + i * CARD_GAP_Y_FACE_UP
                cr.draw_card(self.screen, card, dx, dy, highlight=(i == 0), dragging=True)

        # Toolbar superior
        self._draw_top_toolbar()

    def _draw_top_toolbar(self):
        g = self.game
        bar_rect = pygame.Rect(0, 0, WINDOW_WIDTH, TOOLBAR_H)
        pygame.draw.rect(self.screen, self.theme['menu_bg'], bar_rect)
        pygame.draw.line(self.screen, self.theme['menu_border'],
                         (0, TOOLBAR_H - 1), (WINDOW_WIDTH, TOOLBAR_H - 1), 2)

        elapsed = g.get_elapsed()
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        ty = (TOOLBAR_H - 16) // 2
        self.ui.draw_text(self.screen, f"Movimientos: {g.moves}", 12, ty, font=self.ui._font_small)
        self.ui.draw_text(self.screen, f"Tiempo: {mins:02d}:{secs:02d}", 175, ty, font=self.ui._font_small)
        self.ui.draw_text(self.screen, f"Pasadas: {g.remaining_passes()}", 315, ty, font=self.ui._font_small)
        self.ui.draw_text(self.screen, g.difficulty, 435, ty, font=self.ui._font_small)

        btn_rects = self._get_toolbar_rects()
        mx, my = self.mouse_x, self.mouse_y
        for name, rect in btn_rects.items():
            hover = rect.collidepoint(mx, my)
            disabled = (name == 'Deshacer' and not g.can_undo())
            accent = (name == 'Auto Resolver' and self.auto_solving)
            self.ui.draw_button(self.screen, rect, name, hover=hover, disabled=disabled, accent=accent)

    def _draw_menu(self):
        # Título
        self.ui.draw_text(self.screen, "Solitario Klondike",
                          WINDOW_WIDTH // 2, 100,
                          font=self.ui._font_title, center=True)
        self.ui.draw_text(self.screen, "- Juego de Cartas -",
                          WINDOW_WIDTH // 2, 155,
                          font=self.ui._font, center=True)

        btns = self._get_menu_buttons()
        mx, my = self.mouse_x, self.mouse_y
        for name, rect in btns.items():
            hover = rect.collidepoint(mx, my)
            self.ui.draw_button(self.screen, rect, name, hover=hover)

        # Info de controles
        self.ui.draw_text(self.screen, "Clic derecho: enviar a fundación | Ctrl+Z: deshacer | ESC: menú",
                          WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50,
                          font=self.ui._font_small, center=True)

    def _draw_settings(self):
        panel_x, panel_y = 200, 100
        panel_w, panel_h = 700, 500
        self.ui.draw_panel(self.screen, pygame.Rect(panel_x, panel_y, panel_w, panel_h))

        self.ui.draw_text(self.screen, "Configuración", panel_x + 20, panel_y - 35,
                          font=self.ui._font_large)

        elements = self._get_settings_elements()
        mx, my = self.mouse_x, self.mouse_y
        tab_labels = {'difficulty': 'Dificultad', 'theme': 'Tema Visual', 'card_back': 'Reverso'}

        # Tabs
        for tab_name, rect in elements['tabs'].items():
            active = (tab_name == self.settings_tab)
            color = self.theme['highlight'] if active else self.theme['button_bg']
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, self.theme['menu_border'], rect, 1, border_radius=6)
            self.ui.draw_text(self.screen, tab_labels[tab_name],
                              rect.x + rect.width // 2, rect.y + 8,
                              font=self.ui._font_small, center=True)

        # Items
        for item_name, rect in elements['items'].items():
            hover = rect.collidepoint(mx, my)
            is_selected = False
            label = item_name

            if self.settings_tab == 'difficulty':
                is_selected = (item_name == self.config.get('difficulty', 'Normal'))
                settings = DIFFICULTIES[item_name]
                desc = f"  ({settings['max_passes']} pasadas, {settings['draw_count']} carta(s)"
                if not settings['undo_enabled']:
                    desc += ", sin deshacer"
                desc += ")"
                label = item_name + desc
            elif self.settings_tab == 'theme':
                is_selected = (item_name == self.config.get('theme', 'classic'))
                label = Theme.theme_display_name(item_name)

            color = self.theme['highlight'] if is_selected else (
                self.theme['button_hover'] if hover else self.theme['button_bg']
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, self.theme['menu_border'], rect, 1, border_radius=6)
            txt_color = self.theme['menu_bg'] if is_selected else self.theme['button_text']
            self.ui.draw_text(self.screen, label, rect.x + 15, rect.y + 12,
                              color=txt_color, font=self.ui._font_small)

        # Tab reverso de carta
        if self.settings_tab == 'card_back':
            self._draw_card_back_tab(elements, panel_x, panel_y, panel_w)

        # Botón volver
        if elements.get('back'):
            hover = elements['back'].collidepoint(mx, my)
            self.ui.draw_button(self.screen, elements['back'], "Volver", hover=hover)

    def _draw_card_back_tab(self, elements, panel_x, panel_y, panel_w):
        mx, my = self.mouse_x, self.mouse_y
        item_y = panel_y + 80

        # Botón elegir imagen
        if elements.get('btn_choose'):
            r = elements['btn_choose']
            self.ui.draw_button(self.screen, r, "Elegir imagen...",
                                hover=r.collidepoint(mx, my))

        # Botón quitar
        if elements.get('btn_clear'):
            r = elements['btn_clear']
            has_custom = bool(self.config.get('card_back_path'))
            self.ui.draw_button(self.screen, r, "Quitar imagen",
                                hover=r.collidepoint(mx, my), disabled=not has_custom)

        # Mensaje de error
        if self._card_back_error:
            self.ui.draw_text(self.screen, self._card_back_error,
                              panel_x + 40, item_y + 55,
                              color=(220, 80, 80), font=self.ui._font_small)

        # Ruta actual
        path = self.config.get('card_back_path', '')
        if path:
            import os as _os
            label = _os.path.basename(path)
            self.ui.draw_text(self.screen, f"Actual: {label}",
                              panel_x + 40, item_y + 55 if not self._card_back_error else item_y + 75,
                              font=self.ui._font_small)
        else:
            self.ui.draw_text(self.screen, "Sin imagen personalizada (usando la del tema)",
                              panel_x + 40, item_y + 55,
                              font=self.ui._font_small)

        # Preview del reverso actual
        back_surf = self.card_renderer.get_back()
        if back_surf:
            preview_w, preview_h = 85, 125
            preview_x = panel_x + panel_w - preview_w - 40
            preview_y = item_y + 20
            scaled = pygame.transform.smoothscale(back_surf, (preview_w, preview_h))
            self.screen.blit(scaled, (preview_x, preview_y))
            pygame.draw.rect(self.screen, self.theme['menu_border'],
                             pygame.Rect(preview_x, preview_y, preview_w, preview_h), 2, border_radius=7)
            self.ui.draw_text(self.screen, "Vista previa",
                              preview_x + preview_w // 2, preview_y + preview_h + 6,
                              font=self.ui._font_small, center=True)

        # Formatos soportados
        self.ui.draw_text(self.screen, "Formatos: PNG, JPG, JPEG, BMP",
                          panel_x + 40, item_y + 110, font=self.ui._font_small)

    def _draw_win_overlay(self):
        # Overlay semi-transparente
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        cx = WINDOW_WIDTH // 2
        self.ui.draw_text(self.screen, "VICTORIA!", cx, 200,
                          font=self.ui._font_title, center=True,
                          color=self.theme['highlight'])

        elapsed = self.game.get_elapsed()
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        self.ui.draw_text(self.screen, f"Tiempo: {mins:02d}:{secs:02d}  |  Movimientos: {self.game.moves}",
                          cx, 300, font=self.ui._font_large, center=True)
        self.ui.draw_text(self.screen, f"Dificultad: {self.game.difficulty}",
                          cx, 350, font=self.ui._font, center=True)

        btn_rect = pygame.Rect(cx - 100, 450, 200, 44)
        mx, my = self.mouse_x, self.mouse_y
        self.ui.draw_button(self.screen, btn_rect, "Nuevo Juego",
                            hover=btn_rect.collidepoint(mx, my))

        btn2 = pygame.Rect(cx - 100, 510, 200, 44)
        self.ui.draw_button(self.screen, btn2, "Menú Principal",
                            hover=btn2.collidepoint(mx, my))
