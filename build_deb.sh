#!/bin/bash
set -e

PKG=solitario-klondike_1.0_amd64

echo "==> Limpiando builds anteriores..."
rm -rf build dist $PKG *.deb

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

# Validar que la compilación fue exitosa
if [ ! -d "dist/solitario-klondike" ]; then
  echo "ERROR: PyInstaller no generó dist/solitario-klondike"
  exit 1
fi

if [ ! -f "dist/solitario-klondike/solitario-klondike" ]; then
  echo "ERROR: El ejecutable no se generó en dist/solitario-klondike/"
  exit 1
fi

echo "==> Creando estructura del paquete..."
mkdir -p $PKG/DEBIAN
mkdir -p $PKG/usr/lib/solitario-klondike
mkdir -p $PKG/usr/bin
mkdir -p $PKG/usr/share/applications

echo "==> Copiando archivos compilados..."
cp -r dist/solitario-klondike/* $PKG/usr/lib/solitario-klondike/

# Validar que los archivos se copiaron
if [ ! -f "$PKG/usr/lib/solitario-klondike/solitario-klondike" ]; then
  echo "ERROR: No se copiaron los archivos correctamente"
  ls -la dist/solitario-klondike/
  exit 1
fi

echo "==> Creando archivo de control..."
cat > $PKG/DEBIAN/control << 'EOF'
Package: solitario-klondike
Version: 1.0
Section: games
Priority: optional
Architecture: amd64
Maintainer: Derian <derian@example.com>
Homepage: https://github.com/tu-usuario/solitario-klondike
Description: Solitario Klondike - Juego de cartas
 Juego de solitario Klondike completo con múltiples temas,
 niveles de dificultad y reverso de carta personalizable.
EOF

# Validar que el archivo de control es válido
if [ ! -f "$PKG/DEBIAN/control" ]; then
  echo "ERROR: No se creó el archivo DEBIAN/control"
  exit 1
fi

echo "==> Creando script wrapper..."
cat > $PKG/usr/bin/solitario-klondike << 'WRAPPER'
#!/bin/bash
exec /usr/lib/solitario-klondike/solitario-klondike "$@"
WRAPPER
chmod 755 $PKG/usr/bin/solitario-klondike

# Validar que el wrapper se creó
if [ ! -x "$PKG/usr/bin/solitario-klondike" ]; then
  echo "ERROR: No se creó el wrapper ejecutable"
  exit 1
fi

echo "==> Creando entrada de escritorio..."
cat > $PKG/usr/share/applications/solitario-klondike.desktop << 'DESKTOP'
[Desktop Entry]
Name=Solitario Klondike
Comment=Juego de solitario Klondike
Exec=solitario-klondike
Icon=solitario-klondike
Type=Application
Categories=Game;CardGame;
Terminal=false
DESKTOP

echo "==> Construyendo paquete .deb..."
dpkg-deb --build $PKG

# Validar que el .deb se creó
if [ ! -f "${PKG}.deb" ]; then
  echo "ERROR: No se generó el archivo .deb"
  exit 1
fi

echo ""
echo "✅ Listo: ${PKG}.deb"
echo "📦 Para instalar: sudo dpkg -i ${PKG}.deb"
echo "🗑️  Para desinstalar: sudo apt remove solitario-klondike"
