# Solitario Klondike

Juego de solitario Klondike completo desarrollado en Python con Pygame.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Pygame](https://img.shields.io/badge/Pygame-2.5+-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Características

- Reglas completas del solitario Klondike
- Drag & drop para mover cartas
- Doble clic para mover la carta al lugar ideal automáticamente
- Clic derecho para enviar directamente a la fundación
- Auto-resolver cuando todas las cartas están visibles
- 3 temas visuales: Clásico, Moderno, Minimalista
- Imagen de reverso personalizada (PNG, JPG, JPEG, BMP) con explorador de archivos integrado
- 5 niveles de dificultad
- Deshacer movimientos (Ctrl+Z)
- Guardado automático de partidas
- Contador de movimientos y temporizador
- Soporte para pantalla completa (F11)
- Empaquetable como `.deb` para Debian/Ubuntu

## Requisitos

- Python 3.8+
- Pygame 2.5+

## Instalación y ejecución

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python3 main.py
```

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

## Temas Personalizados

Crear una carpeta en `themes/mi_tema/` con un `theme.json`:

```json
{
  "name": "Mi Tema",
  "background": [34, 120, 60],
  "card_front": [255, 255, 255],
  "card_back": [30, 60, 150],
  "card_back_pattern": [20, 45, 120],
  "card_border": [60, 60, 60],
  "red_suit": [200, 30, 30],
  "black_suit": [20, 20, 20],
  "slot_color": [24, 90, 45],
  "slot_border": [18, 70, 35],
  "button_bg": [40, 90, 50],
  "button_hover": [50, 110, 65],
  "button_text": [240, 240, 220],
  "text_color": [240, 240, 220],
  "menu_bg": [25, 80, 45],
  "menu_border": [200, 180, 100],
  "highlight": [255, 215, 0],
  "card_back_style": "crosshatch"
}
```

Estilos de reverso: `crosshatch`, `gradient`, `plain`.

Imágenes opcionales en la carpeta del tema:
- `card_back.png` — reverso de cartas (100×145 px)
- `background.png` — fondo de mesa (1100×750 px)

## Empaquetar como .deb

```bash
chmod +x build_deb.sh
./build_deb.sh
sudo dpkg -i solitario-klondike_1.0_amd64.deb
```

El script usa PyInstaller (`--onedir`) para generar un binario autocontenido con Python + Pygame + assets, evitando conflictos con el `python3-pygame` del sistema.

Para desinstalar:

```bash
sudo apt remove solitario-klondike
```

## Estructura del Proyecto

```
solitario_game/
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias Python
├── build_deb.sh            # Script para empaquetar como .deb
├── assets/                 # Iconos PNG de palos
│   ├── hearts.png
│   ├── diamonds.png
│   ├── clubs.png
│   └── spades.png
├── src/
│   ├── constants.py        # Constantes globales
│   ├── card.py             # Modelo de carta y mazo
│   ├── game_logic.py       # Lógica del juego Klondike
│   ├── theme.py            # Sistema de temas
│   ├── renderer.py         # Renderizado de cartas y UI
│   ├── game_gui.py         # Interfaz gráfica principal
│   └── file_browser.py     # Explorador de archivos integrado
├── themes/
│   ├── classic/
│   ├── modern/
│   └── minimalist/
└── saves/
    └── config.json         # Configuración del jugador (tema, dificultad)
```

## Licencia

MIT — ver [LICENSE](LICENSE).
