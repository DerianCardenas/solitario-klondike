# GitHub Actions Workflows

Este proyecto incluye dos workflows de GitHub Actions para compilar automáticamente el paquete `.deb`:

## 1. `build-deb.yml` - Build continuo

**Se ejecuta en:**
- Push a `main` o `master`
- Pull requests
- Tags que empiecen con `v*` (ej: `v1.0.0`)
- Releases

**Resultado:**
- Sube el `.deb` como artefacto (disponible 30 días)
- Si es un tag, también lo adjunta al release automáticamente

## 2. `release.yml` - Build solo en releases

**Se ejecuta en:**
- Cuando publicas un release en GitHub

**Resultado:**
- Compila el `.deb` y lo adjunta al release
- Agrega instrucciones de instalación automáticamente

---

## Cómo usar

### Opción 1: Crear un release desde GitHub

1. Ve a tu repositorio en GitHub
2. Click en "Releases" → "Create a new release"
3. Elige un tag (ej: `v1.0.0`)
4. Escribe título y descripción
5. Click "Publish release"
6. GitHub Actions compilará automáticamente el `.deb` y lo adjuntará al release

### Opción 2: Crear un release desde la terminal

```bash
# Crear y push del tag
git tag v1.0.0
git push origin v1.0.0

# Luego ve a GitHub y crea el release desde el tag
```

### Opción 3: Usar GitHub CLI

```bash
# Instalar gh si no lo tienes
# sudo apt install gh

# Crear release
gh release create v1.0.0 \
  --title "Solitario Klondike v1.0.0" \
  --notes "Primera versión estable"

# GitHub Actions compilará y subirá el .deb automáticamente
```

---

## Ver el progreso

1. Ve a la pestaña "Actions" en tu repositorio
2. Verás los workflows ejecutándose
3. Click en uno para ver los logs en tiempo real
4. Cuando termine, el `.deb` estará disponible en:
   - **Artifacts** (si es push normal)
   - **Release assets** (si es un release o tag)

---

## Descargar artefactos manualmente

Si quieres descargar el `.deb` de un build sin crear un release:

1. Ve a "Actions" → Click en el workflow completado
2. Scroll hasta "Artifacts"
3. Click en "solitario-klondike-deb" para descargar

---

## Notas

- El build tarda aproximadamente 3-5 minutos
- Requiere que el repositorio sea público o tengas GitHub Actions habilitado
- Los artefactos se guardan por 30 días
- Los releases son permanentes
