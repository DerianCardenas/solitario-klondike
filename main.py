#!/usr/bin/env python3
"""
Solitario Klondike - Juego de cartas
Archivo principal ejecutable.

Uso:
    python3 main.py

Controles:
    - Clic izquierdo: seleccionar y arrastrar cartas
    - Clic derecho: enviar carta automáticamente a fundación
    - Ctrl+Z: deshacer último movimiento
    - Ctrl+N: nuevo juego
    - ESC: abrir/cerrar menú
"""
import sys
import os

# Asegurar que el directorio del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.game_gui import SolitaireGUI


def main():
    app = SolitaireGUI()
    app.run()


if __name__ == '__main__':
    main()
