# Solitario Klondike - Información del Proyecto

## Descripción

Juego de solitario Klondike completo desarrollado en Python con Pygame.

## Cómo ejecutar

```bash
# Crear entorno virtual e instalar dependencias
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Ejecutar el juego
venv/bin/python3 main.py
```

## Requisitos

- Python 3.8+
- Pygame 2.5+

## Estructura del Proyecto

```
solitario_game/
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias Python
├── build_deb.sh            # Script para empaquetar como .deb
├── solitario-klondike.spec # Spec de PyInstaller
├── assets/                 # Iconos PNG de palos (hearts, diamonds, clubs, spades)
├── src/
│   ├── __init__.py
│   ├── constants.py        # Constantes globales
│   ├── card.py             # Modelo de carta y mazo
│   ├── game_logic.py       # Lógica del juego Klondike
│   ├── theme.py            # Sistema de temas
│   ├── renderer.py         # Renderizado de cartas y UI
│   ├── game_gui.py         # Interfaz gráfica principal
│   └── file_browser.py     # Explorador de archivos integrado en Pygame
├── themes/
│   ├── classic/            # Tema clásico
│   ├── modern/             # Tema moderno
│   └── minimalist/         # Tema minimalista
└── saves/                  # Partidas guardadas (autosave.json, config.json)
```

## Módulos principales

- `main.py` — Inicializa Pygame y lanza el loop principal del juego.
- `src/card.py` — Define las clases `Card` y `Deck` con toda la lógica de baraja.
- `src/game_logic.py` — Implementa las reglas del Klondike: tableau, fundaciones, mazo, movimientos válidos, deshacer, guardar/cargar.
- `src/game_gui.py` — Maneja eventos del ratón (drag & drop, clics, doble clic), teclado y el loop de la UI.
- `src/file_browser.py` — Explorador de archivos integrado en Pygame para seleccionar imágenes de reverso sin depender de tkinter.
- `src/renderer.py` — Dibuja cartas, slots, fundaciones y todos los elementos visuales.
- `src/theme.py` — Carga y gestiona temas desde `themes/*/theme.json` e imágenes opcionales.
- `src/constants.py` — Colores, tamaños, posiciones y configuración global.

## Controles

| Acción | Control |
|--------|---------|
| Mover cartas | Arrastrar con clic izquierdo |
| Mover carta al lugar ideal | Doble clic sobre la carta |
| Enviar a fundación | Clic derecho sobre la carta |
| Voltear carta del mazo | Clic en el mazo (esquina sup. izq.) |
| Deshacer | Ctrl+Z |
| Nuevo juego | Ctrl+N |
| Pantalla completa | F11 |
| Menú | ESC |

## Niveles de Dificultad

| Nivel | Pasadas | Cartas por volteo | Deshacer |
|-------|---------|-------------------|----------|
| Principiante | 5 | 1 | Sí |
| Fácil | 4 | 1 | Sí |
| Normal | 3 | 1 | Sí |
| Difícil | 2 | 1 | Sí |
| Profesional | 2 | 3 | No |

## Temas Visuales

Hay 3 temas incluidos: `classic`, `modern`, `minimalist`. Cada uno tiene un `theme.json` con colores y estilo de reverso de carta.

Para crear un tema personalizado, agregar una carpeta en `themes/mi_tema/` con su `theme.json`. Opcionalmente se puede incluir `card_back.png` (100×145 px) y `background.png` (1100×750 px).

Estilos de reverso disponibles: `crosshatch`, `gradient`, `plain`.

## Guardado de partidas

Las partidas se guardan automáticamente en `saves/autosave.json`. La configuración del jugador (tema, dificultad) se persiste en `saves/config.json`.

> **Nota pendiente**: al instalar el `.deb`, la ruta `saves/` queda en `/usr/lib/solitario-klondike/_internal/saves/` que es de solo lectura. Pendiente migrar a `~/.local/share/solitario-klondike/` para que el guardado funcione correctamente tras la instalación.

## Empaquetar como .deb

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
chmod +x build_deb.sh
./build_deb.sh
sudo dpkg -i solitario-klondike_1.0_amd64.deb
```

El script usa PyInstaller (`--onedir`) para generar un binario autocontenido con Python + Pygame + assets, evitando conflictos con `python3-pygame` del sistema (Debian 12 trae v2.1, el juego requiere v2.5+).

## Iconos de palos (assets/)

Los iconos se cargan desde `assets/{suit}.png` (hearts, diamonds, clubs, spades) en `renderer.py`.
- Se cargan en `CardRenderer.__init__` vía `_load_suit_icons()`
- `_get_suit_icon(suit, size, color)` escala y coloriza el PNG usando el canal alpha como máscara
- Si un PNG no existe, cae al dibujo programático original en `_draw_suit_shape()`

### Tamaños de iconos por zona (renderer.py)

| Zona | Tamaño |
|------|--------|
| Esquinas (valor + icono) | 7 |
| Pips cartas 2–5 | 10 |
| Pips cartas 6–10 | 8 |
| As (centro) | 30 |
| J, Q, K | sin icono de palo (solo letra) |

---

## Historial de cambios relevantes

### Doble clic (game_gui.py)
- `_on_double_click(pos)`: nuevo método que mueve la carta al lugar ideal.
  - Desde waste o tableau: intenta fundación primero, luego tableau.
  - Desde fundación: devuelve la carta al tableau.
- Detección en `_handle_events` con umbral de 0.35 s y tolerancia de 15 px.
- Atributos añadidos en `__init__`: `_last_click_time`, `_last_click_pos`, `_double_click_threshold`.

### Auto-resolver (game_logic.py + game_gui.py)
- `can_auto_solve()` ya no bloquea si hay cartas en el waste (solo bloquea si hay cartas en el stock o cartas ocultas en el tableau). `auto_solve_step()` ya manejaba el waste correctamente.
- La pantalla de victoria ahora muestra el tiempo y movimientos correctos porque `_check_win()` congela `self.elapsed` en el momento exacto de la victoria.

### Algoritmo de reparto (game_logic.py — `_deal`)
- Reintenta hasta 20 veces (promedio ~1.17 intentos) buscando un reparto donde haya al menos 1 As visible en el tableau, o máximo 2 Ases enterrados bajo cartas ocultas.
- Elimina los repartos con los 4 Ases enterrados (era el 2.1% de las partidas con el shuffle puro).
- La aleatoriedad se mantiene prácticamente intacta.

### Imagen de reverso personalizada (theme.py + game_gui.py + file_browser.py)
- Nueva tab "Reverso" en Configuración con selector de archivo integrado en Pygame.
- **Explorador de archivos propio** (`src/file_browser.py`) — no depende de tkinter, evita problemas de foco en Linux.
  - Navegación por carpetas con clic/doble clic o teclado (↑↓, Enter).
  - Barra de ruta editable — puedes escribir una ruta directamente.
  - Solo muestra carpetas e imágenes (PNG, JPG, JPEG, BMP).
  - Scrollbar lateral y soporte de rueda del ratón.
  - Botones "Cancelar" y "Aceptar" (habilitado solo con imagen seleccionada).
  - Clic fuera del panel cancela.
- Soporta PNG, JPG, JPEG, BMP.
- La ruta se persiste en `saves/config.json` como `card_back_path`.
- `Theme.set_custom_card_back(path)` aplica la imagen con prioridad sobre la del tema.
- `Theme.clear_custom_card_back()` vuelve al reverso del tema activo.
- La imagen se escala automáticamente al tamaño de carta (85×125 px) en `_render_card_back()`.
- Preview en tiempo real visible en la misma pantalla de configuración.
- El browser usa `self.display` (ventana real) y obtiene dimensiones dinámicamente con `screen.get_size()`.

### Bug en undo (game_logic.py)
- `undo()` sumaba `self.moves += 1` al deshacer en vez de restar. Corregido a `self.moves = max(0, self.moves - 1)`.
