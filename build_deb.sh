#!/bin/bash
set -e

PKG=solitario-klondike_1.0_amd64

echo "==> Instalando PyInstaller..."
venv/bin/pip install pyinstaller -q

echo "==> Compilando con PyInstaller..."
venv/bin/pyinstaller \
  --onedir \
  --name solitario-klondike \
  --add-data "assets:assets" \
  --add-data "themes:themes" \
  --add-data "saves:saves" \
  --add-data "src:src" \
  -y \
  main.py

echo "==> Creando estructura del paquete..."
mkdir -p $PKG/DEBIAN
mkdir -p $PKG/usr/lib/solitario-klondike
mkdir -p $PKG/usr/bin
mkdir -p $PKG/usr/share/applications

cp -r dist/solitario-klondike/* $PKG/usr/lib/solitario-klondike/

cat > $PKG/DEBIAN/control << 'EOF'
Package: solitario-klondike
Version: 1.0
Section: games
Priority: optional
Architecture: amd64
Maintainer: Derian
Description: Solitario Klondike
 Juego de cartas solitario Klondike.
EOF

cat > $PKG/usr/bin/solitario-klondike << 'EOF'
#!/bin/bash
exec /usr/lib/solitario-klondike/solitario-klondike "$@"
EOF
chmod 755 $PKG/usr/bin/solitario-klondike

cat > $PKG/usr/share/applications/solitario-klondike.desktop << 'EOF'
[Desktop Entry]
Name=Solitario Klondike
Exec=solitario-klondike
Icon=solitario-klondike
Type=Application
Categories=Game;CardGame;
Terminal=false
EOF

echo "==> Construyendo .deb..."
dpkg-deb --build $PKG

echo ""
echo "Listo: ${PKG}.deb"
echo "Para instalar: sudo dpkg -i ${PKG}.deb"
