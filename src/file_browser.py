"""
Explorador de archivos implementado en Pygame.
Se usa para seleccionar imágenes sin depender de tkinter.
"""
import os
import pygame

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp'}

# Colores internos del browser
_BG         = (30,  35,  45)
_PANEL      = (40,  47,  60)
_BORDER     = (80,  95, 120)
_HIGHLIGHT  = (94, 129, 172)
_TEXT       = (220, 225, 235)
_TEXT_DIM   = (140, 150, 165)
_TEXT_DIR   = (180, 200, 240)
_TEXT_IMG   = (140, 210, 150)
_SCROLLBAR  = (70,  82, 100)
_SCROLLTHUMB= (110, 130, 160)
_BTN_OK     = (60, 130,  70)
_BTN_CANCEL = (130, 60,  60)
_BTN_HOVER  = (200, 215, 235)
_INPUT_BG   = (25,  30,  40)
_INPUT_BORDER_ACTIVE = (136, 192, 208)


class FileBrowser:
    """
    Explorador de archivos modal renderizado con Pygame.
    Uso:
        browser = FileBrowser(screen, theme)
        path = browser.run()   # bloquea hasta que el usuario elige o cancela
        # path es str o None
    """

    PANEL_W = 780
    PANEL_H = 520
    ROW_H   = 32
    VISIBLE_ROWS = 12

    def __init__(self, screen, theme=None):
        self.screen = screen
        self.theme  = theme
        self.clock  = pygame.time.Clock()

        # Obtener dimensiones reales del screen
        self.screen_w, self.screen_h = screen.get_size()

        pygame.font.init()
        fn = (theme.get('font_name') if theme else None) or 'dejavusans'
        self._font      = pygame.font.SysFont(fn, 17)
        self._font_sm   = pygame.font.SysFont(fn, 14)
        self._font_bold = pygame.font.SysFont(fn, 17, bold=True)
        self._font_path = pygame.font.SysFont('monospace', 13)

        self.px = (self.screen_w  - self.PANEL_W) // 2
        self.py = (self.screen_h - self.PANEL_H) // 2

        self.current_dir  = os.path.expanduser('~')
        self.entries      = []   # lista de (name, is_dir, full_path)
        self.scroll       = 0
        self.selected_idx = -1
        self.selected_path= ''

        # Barra de ruta editable
        self.path_input   = self.current_dir
        self.path_editing = False
        self.cursor_vis   = True
        self._cursor_timer= 0.0

        self._load_dir(self.current_dir)

    # ── Carga de directorio ───────────────────────────────────────────────

    def _load_dir(self, path):
        if not os.path.isdir(path):
            return
        self.current_dir  = path
        self.path_input   = path
        self.scroll       = 0
        self.selected_idx = -1
        self.selected_path= ''
        self.entries = []

        # Entrada para subir un nivel
        parent = os.path.dirname(path)
        if parent != path:
            self.entries.append(('..', True, parent))

        try:
            names = sorted(os.listdir(path), key=lambda n: (not os.path.isdir(os.path.join(path, n)), n.lower()))
        except PermissionError:
            names = []

        for name in names:
            if name.startswith('.'):
                continue
            full = os.path.join(path, name)
            is_dir = os.path.isdir(full)
            ext = os.path.splitext(name)[1].lower()
            if is_dir or ext in IMAGE_EXTENSIONS:
                self.entries.append((name, is_dir, full))

    # ── Loop principal ────────────────────────────────────────────────────

    def run(self):
        """Ejecuta el browser modal. Retorna la ruta elegida o None."""
        while True:
            dt = self.clock.tick(60) / 1000.0
            self._cursor_timer += dt
            if self._cursor_timer >= 0.5:
                self._cursor_timer = 0.0
                self.cursor_vis = not self.cursor_vis

            for event in pygame.event.get():
                result = self._handle_event(event)
                if result is not None:   # None = seguir, str o '' = terminar
                    return result if result else None

            self._draw()
            pygame.display.flip()

    # ── Eventos ───────────────────────────────────────────────────────────

    def _handle_event(self, event):
        if event.type == pygame.QUIT:
            return ''   # cancelar

        elif event.type == pygame.KEYDOWN:
            return self._handle_key(event)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = self._to_panel(event.pos)
            if event.button == 1:
                return self._handle_click(mx, my)
            elif event.button == 4:   # scroll arriba
                self.scroll = max(0, self.scroll - 1)
            elif event.button == 5:   # scroll abajo
                max_scroll = max(0, len(self.entries) - self.VISIBLE_ROWS)
                self.scroll = min(max_scroll, self.scroll + 1)

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(
                len(self.entries) - self.VISIBLE_ROWS,
                self.scroll - event.y
            ))

        return None

    def _handle_key(self, event):
        if self.path_editing:
            if event.key == pygame.K_RETURN:
                # Intentar navegar a la ruta escrita
                p = self.path_input.strip()
                if os.path.isdir(p):
                    self._load_dir(p)
                    self.path_editing = False
                elif os.path.isfile(p) and os.path.splitext(p)[1].lower() in IMAGE_EXTENSIONS:
                    return p
                else:
                    self.path_input = self.current_dir  # revertir
                    self.path_editing = False
            elif event.key == pygame.K_ESCAPE:
                self.path_input = self.current_dir
                self.path_editing = False
            elif event.key == pygame.K_BACKSPACE:
                self.path_input = self.path_input[:-1]
            else:
                if event.unicode and event.unicode.isprintable():
                    self.path_input += event.unicode
        else:
            if event.key == pygame.K_ESCAPE:
                return ''
            elif event.key == pygame.K_RETURN and self.selected_path:
                if os.path.isdir(self.selected_path):
                    self._load_dir(self.selected_path)
                else:
                    return self.selected_path
            elif event.key == pygame.K_UP:
                self.selected_idx = max(0, self.selected_idx - 1)
                self._update_selected()
                self._ensure_visible()
            elif event.key == pygame.K_DOWN:
                self.selected_idx = min(len(self.entries) - 1, self.selected_idx + 1)
                self._update_selected()
                self._ensure_visible()
        return None

    def _handle_click(self, mx, my):
        pw, ph = self.PANEL_W, self.PANEL_H

        # Clic fuera del panel = cancelar
        if not (0 <= mx <= pw and 0 <= my <= ph):
            return ''

        # Barra de ruta
        path_rect = self._path_bar_rect()
        if path_rect.collidepoint(mx, my):
            self.path_editing = True
            self.cursor_vis = True
            self._cursor_timer = 0.0
            return None

        # Botón Cancelar
        btn_cancel, btn_ok = self._button_rects()
        if btn_cancel.collidepoint(mx, my):
            return ''
        if btn_ok.collidepoint(mx, my):
            if self.selected_path and os.path.isfile(self.selected_path):
                return self.selected_path
            return None

        # Lista de archivos
        list_rect = self._list_rect()
        if list_rect.collidepoint(mx, my):
            row = (my - list_rect.y) // self.ROW_H
            idx = self.scroll + row
            if 0 <= idx < len(self.entries):
                if self.selected_idx == idx:
                    # Doble clic (segundo clic en el mismo)
                    name, is_dir, full = self.entries[idx]
                    if is_dir:
                        self._load_dir(full)
                    else:
                        return full
                else:
                    self.selected_idx = idx
                    self._update_selected()
            self.path_editing = False

        return None

    def _update_selected(self):
        if 0 <= self.selected_idx < len(self.entries):
            self.selected_path = self.entries[self.selected_idx][2]
        else:
            self.selected_path = ''

    def _ensure_visible(self):
        if self.selected_idx < self.scroll:
            self.scroll = self.selected_idx
        elif self.selected_idx >= self.scroll + self.VISIBLE_ROWS:
            self.scroll = self.selected_idx - self.VISIBLE_ROWS + 1

    # ── Coordenadas ───────────────────────────────────────────────────────

    def _to_panel(self, pos):
        return (pos[0] - self.px, pos[1] - self.py)

    def _path_bar_rect(self):
        return pygame.Rect(12, 44, self.PANEL_W - 24, 28)

    def _list_rect(self):
        return pygame.Rect(12, 82, self.PANEL_W - 28, self.VISIBLE_ROWS * self.ROW_H)

    def _button_rects(self):
        bw, bh = 120, 36
        by = self.PANEL_H - bh - 12
        btn_cancel = pygame.Rect(self.PANEL_W - 2 * bw - 20, by, bw, bh)
        btn_ok     = pygame.Rect(self.PANEL_W - bw - 8,      by, bw, bh)
        return btn_cancel, btn_ok

    # ── Dibujo ────────────────────────────────────────────────────────────

    def _draw(self):
        # Overlay oscuro
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        pw, ph = self.PANEL_W, self.PANEL_H
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(panel, _PANEL, (0, 0, pw, ph), border_radius=10)
        pygame.draw.rect(panel, _BORDER, (0, 0, pw, ph), 2, border_radius=10)

        # Título
        title = self._font_bold.render("Seleccionar imagen para el reverso", True, _TEXT)
        panel.blit(title, (12, 12))

        # Barra de ruta
        path_rect = self._path_bar_rect()
        border_col = _INPUT_BORDER_ACTIVE if self.path_editing else _BORDER
        pygame.draw.rect(panel, _INPUT_BG, path_rect, border_radius=4)
        pygame.draw.rect(panel, border_col, path_rect, 1, border_radius=4)
        display_path = self.path_input
        # Truncar por la izquierda si es muy largo
        max_w = path_rect.width - 10
        path_surf = self._font_path.render(display_path, True, _TEXT)
        if path_surf.get_width() > max_w:
            # Mostrar solo el final
            while path_surf.get_width() > max_w and len(display_path) > 1:
                display_path = display_path[1:]
                path_surf = self._font_path.render('…' + display_path, True, _TEXT)
            path_surf = self._font_path.render('…' + display_path, True, _TEXT)
        panel.blit(path_surf, (path_rect.x + 5, path_rect.y + 7))
        if self.path_editing and self.cursor_vis:
            cx = path_rect.x + 5 + path_surf.get_width() + 1
            pygame.draw.line(panel, _TEXT, (cx, path_rect.y + 5), (cx, path_rect.y + 22), 1)

        # Lista
        list_rect = self._list_rect()
        pygame.draw.rect(panel, _BG, list_rect, border_radius=4)
        pygame.draw.rect(panel, _BORDER, list_rect, 1, border_radius=4)

        visible = self.entries[self.scroll: self.scroll + self.VISIBLE_ROWS]
        for i, (name, is_dir, full) in enumerate(visible):
            ry = list_rect.y + i * self.ROW_H
            row_rect = pygame.Rect(list_rect.x + 1, ry + 1, list_rect.width - 2, self.ROW_H - 1)
            abs_idx = self.scroll + i

            if abs_idx == self.selected_idx:
                pygame.draw.rect(panel, _HIGHLIGHT, row_rect, border_radius=3)

            icon = '📁 ' if is_dir else '🖼 '
            color = _TEXT_DIR if is_dir else _TEXT_IMG
            if name == '..':
                icon = '⬆ '
                color = _TEXT_DIM

            # Icono ASCII simple (pygame no renderiza emoji bien en todos los sistemas)
            icon_char = '[D]' if is_dir else '[I]'
            if name == '..':
                icon_char = '[^]'
            ic_surf = self._font_sm.render(icon_char, True, _TEXT_DIM)
            panel.blit(ic_surf, (list_rect.x + 6, ry + (self.ROW_H - ic_surf.get_height()) // 2))

            txt_surf = self._font.render(name, True, color)
            panel.blit(txt_surf, (list_rect.x + 36, ry + (self.ROW_H - txt_surf.get_height()) // 2))

        # Scrollbar
        if len(self.entries) > self.VISIBLE_ROWS:
            sb_x = list_rect.right + 2
            sb_y = list_rect.y
            sb_h = list_rect.height
            sb_w = 10
            pygame.draw.rect(panel, _SCROLLBAR, (sb_x, sb_y, sb_w, sb_h), border_radius=4)
            ratio = self.VISIBLE_ROWS / len(self.entries)
            thumb_h = max(20, int(sb_h * ratio))
            thumb_y = sb_y + int((sb_h - thumb_h) * self.scroll / max(1, len(self.entries) - self.VISIBLE_ROWS))
            pygame.draw.rect(panel, _SCROLLTHUMB, (sb_x, thumb_y, sb_w, thumb_h), border_radius=4)

        # Archivo seleccionado
        sel_y = list_rect.bottom + 8
        if self.selected_path and os.path.isfile(self.selected_path):
            sel_text = f"Seleccionado: {os.path.basename(self.selected_path)}"
            sel_surf = self._font_sm.render(sel_text, True, _TEXT_IMG)
        else:
            sel_surf = self._font_sm.render("Doble clic o Enter para abrir carpeta / seleccionar imagen", True, _TEXT_DIM)
        panel.blit(sel_surf, (12, sel_y))

        # Botones
        mx_raw, my_raw = pygame.mouse.get_pos()
        mx, my = mx_raw - self.px, my_raw - self.py
        btn_cancel, btn_ok = self._button_rects()

        ok_enabled = bool(self.selected_path and os.path.isfile(self.selected_path))
        self._draw_button(panel, btn_cancel, "Cancelar", mx, my, _BTN_CANCEL)
        self._draw_button(panel, btn_ok, "Aceptar", mx, my, _BTN_OK, disabled=not ok_enabled)

        # Leyenda teclas
        hint = self._font_sm.render("↑↓ navegar  |  Enter abrir/aceptar  |  ESC cancelar", True, _TEXT_DIM)
        panel.blit(hint, (12, self.PANEL_H - 20))

        self.screen.blit(panel, (self.px, self.py))

    def _draw_button(self, surf, rect, text, mx, my, base_color, disabled=False):
        if disabled:
            color = tuple(max(0, c - 40) for c in base_color)
            text_color = _TEXT_DIM
        elif rect.collidepoint(mx, my):
            color = tuple(min(255, c + 40) for c in base_color)
            text_color = (255, 255, 255)
        else:
            color = base_color
            text_color = _TEXT
        pygame.draw.rect(surf, color, rect, border_radius=6)
        pygame.draw.rect(surf, _BORDER, rect, 1, border_radius=6)
        t = self._font_bold.render(text, True, text_color)
        surf.blit(t, (rect.x + (rect.width - t.get_width()) // 2,
                      rect.y + (rect.height - t.get_height()) // 2))
