# GitHub Actions Workflows

Este proyecto usa GitHub Actions para compilar automáticamente el paquete `.deb`.

## Workflow: `build-deb.yml`

**Se ejecuta cuando:**
- Haces push de un tag que empiece con `v*` (ej: `v1.0.0`, `v1.2.3`)

**Resultado:**
- Compila el paquete `.deb`
- Crea o actualiza el release automáticamente
- Adjunta el `.deb` al release
- Agrega descripción con instrucciones de instalación

---

## Cómo crear un release

### Método 1: Desde la terminal (recomendado)

```bash
# 1. Asegúrate de que todos los cambios estén commiteados
git add .
git commit -m "Preparar release v1.0.0"
git push

# 2. Crear y push del tag
git tag v1.0.0
git push origin v1.0.0

# 3. GitHub Actions compilará automáticamente y creará el release
```

### Método 2: Desde GitHub web

1. Ve a tu repositorio en GitHub
2. Click en "Releases" → "Create a new release"
3. Click en "Choose a tag" → Escribe `v1.0.0` → "Create new tag: v1.0.0 on publish"
4. Título: `Solitario Klondike v1.0.0`
5. Click "Publish release"
6. GitHub Actions detectará el tag y compilará el `.deb` automáticamente

### Método 3: Con GitHub CLI

```bash
# Crear tag y release en un solo comando
gh release create v1.0.0 \
  --title "Solitario Klondike v1.0.0" \
  --notes "Primera versión estable" \
  --generate-notes

# GitHub Actions compilará y subirá el .deb automáticamente
```

---

## Ver el progreso

1. Ve a la pestaña "Actions" en tu repositorio
2. Verás el workflow "Build DEB Package" ejecutándose
3. Click en él para ver los logs en tiempo real
4. Cuando termine (3-5 minutos), el `.deb` estará en el release

---

## Actualizar un release existente

Si ya tienes un release y quieres recompilar el `.deb`:

```bash
# Eliminar el tag local y remoto
git tag -d v1.0.0
git push origin --delete v1.0.0

# Crear el tag de nuevo
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions recompilará y actualizará el release
```

---

## Solución de problemas

### El workflow no se ejecuta

- Verifica que el tag empiece con `v` (ej: `v1.0.0`, no `1.0.0`)
- Asegúrate de hacer `git push origin v1.0.0` (no solo `git push`)

### El workflow falla

1. Ve a "Actions" → Click en el workflow fallido
2. Lee los logs para ver qué falló
3. Problemas comunes:
   - Falta alguna dependencia en `requirements.txt`
   - Error en `build_deb.sh`
   - Permisos incorrectos (ya configurados en el workflow)

### El .deb no aparece en el release

- Espera a que el workflow termine (3-5 minutos)
- Verifica que el workflow tenga un ✅ verde en "Actions"
- Si falló, revisa los logs

### Error de permisos

El workflow ya tiene `permissions: contents: write` configurado. Si aún así falla:

1. Ve a Settings → Actions → General
2. En "Workflow permissions", selecciona "Read and write permissions"
3. Guarda y vuelve a ejecutar el workflow

---

## Versionado semántico

Usa [Semantic Versioning](https://semver.org/):

- `v1.0.0` - Primera versión estable
- `v1.0.1` - Parche (bug fixes)
- `v1.1.0` - Minor (nuevas características compatibles)
- `v2.0.0` - Major (cambios incompatibles)

Ejemplos:
```bash
git tag v1.0.1  # Bug fix
git tag v1.1.0  # Nueva característica
git tag v2.0.0  # Cambio mayor
git push origin --tags  # Push todos los tags
```
