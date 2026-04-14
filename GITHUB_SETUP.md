# Guía para subir el proyecto a GitHub

## Paso 1: Crear el repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre del repositorio: `solitario-klondike` (o el que prefieras)
3. Descripción: "Juego de solitario Klondike en Python con Pygame"
4. Público o Privado (tu elección)
5. **NO** marques "Add a README file" (ya tienes uno)
6. Click "Create repository"

## Paso 2: Inicializar Git localmente

Desde la carpeta `solitario_game/`:

```bash
# Inicializar repositorio
git init

# Agregar todos los archivos
git add .

# Primer commit
git commit -m "Initial commit: Solitario Klondike v1.0"

# Renombrar rama a main (si es necesario)
git branch -M main

# Conectar con GitHub (reemplaza TU_USUARIO y TU_REPO)
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git

# Subir código
git push -u origin main
```

## Paso 3: Verificar que GitHub Actions funciona

1. Ve a tu repositorio en GitHub
2. Click en la pestaña "Actions"
3. Deberías ver el workflow "Build DEB Package" ejecutándose
4. Espera 3-5 minutos a que termine
5. Si todo está verde ✅, el build fue exitoso

## Paso 4: Crear tu primer release

### Opción A: Desde la web de GitHub

1. Ve a tu repositorio
2. Click en "Releases" (lado derecho)
3. Click "Create a new release"
4. En "Choose a tag", escribe `v1.0.0` y click "Create new tag"
5. Título: `Solitario Klondike v1.0.0`
6. Descripción:
   ```markdown
   ## Características
   
   - Juego completo de Solitario Klondike
   - 5 niveles de dificultad
   - 3 temas visuales
   - Reverso de carta personalizable
   - Auto-resolver
   - Doble clic para mover cartas
   
   ## Instalación
   
   ```bash
   sudo dpkg -i solitario-klondike_1.0_amd64.deb
   ```
   
   ## Requisitos
   
   - Debian 11+ / Ubuntu 20.04+
   - Sistema de 64 bits
   ```
7. Click "Publish release"
8. GitHub Actions compilará el `.deb` automáticamente y lo adjuntará al release

### Opción B: Desde la terminal

```bash
# Crear y subir el tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Luego ve a GitHub y crea el release desde ese tag
```

## Paso 5: Descargar el .deb compilado

Una vez que el workflow termine:

1. Ve a tu release en GitHub
2. Scroll hasta "Assets"
3. Verás `solitario-klondike_1.0_amd64.deb`
4. Click para descargar

## Comandos útiles

### Ver el estado de Git
```bash
git status
```

### Hacer cambios y subirlos
```bash
git add .
git commit -m "Descripción de los cambios"
git push
```

### Crear un nuevo release
```bash
# Incrementar versión
git tag v1.1.0
git push origin v1.1.0

# Luego crear el release en GitHub
```

### Ver tags existentes
```bash
git tag
```

### Eliminar un tag (si te equivocaste)
```bash
# Local
git tag -d v1.0.0

# Remoto
git push origin --delete v1.0.0
```

## Solución de problemas

### El workflow falla

1. Ve a "Actions" → Click en el workflow fallido
2. Lee los logs para ver qué falló
3. Problemas comunes:
   - Falta alguna dependencia en `requirements.txt`
   - Error en `build_deb.sh`
   - Permisos incorrectos

### No aparece el .deb en el release

- Asegúrate de que el tag empiece con `v` (ej: `v1.0.0`)
- Verifica que el workflow "Release Build" se haya ejecutado
- Revisa los logs en "Actions"

### El repositorio es privado y no funciona Actions

- GitHub Actions es gratis para repositorios públicos
- Para privados, tienes minutos limitados (2000/mes en plan gratuito)
- Considera hacer el repo público o comprar más minutos

## Badges para el README

Agrega estos badges al inicio de tu `README.md`:

```markdown
![Build Status](https://github.com/TU_USUARIO/TU_REPO/workflows/Build%20DEB%20Package/badge.svg)
![Release](https://img.shields.io/github/v/release/TU_USUARIO/TU_REPO)
![Downloads](https://img.shields.io/github/downloads/TU_USUARIO/TU_REPO/total)
```

Reemplaza `TU_USUARIO` y `TU_REPO` con tus datos.
