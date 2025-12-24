# Cómo Generar Datos Pre-procesados para R3ACT

## Problema

Los archivos de tracking están en Git LFS (89MB+ cada uno) y no se pueden descargar desde Streamlit Cloud. Para visualizar las métricas en el dashboard, necesitas generar los datos pre-procesados localmente.

## Solución

### Paso 1: Instalar Git LFS

```bash
# Windows (con Chocolatey)
choco install git-lfs

# macOS
brew install git-lfs

# Linux
sudo apt-get install git-lfs  # Ubuntu/Debian
# o
sudo yum install git-lfs       # CentOS/RHEL

# Configurar Git LFS
git lfs install
```

### Paso 2: Clonar el Repositorio SkillCorner con LFS

```bash
# Clonar el repositorio (esto descargará los archivos LFS)
git clone https://github.com/SkillCorner/opendata.git
cd opendata
git lfs pull
```

### Paso 3: Ejecutar el Script de Cálculo

```bash
# Desde el directorio de tu proyecto R3ACT
python calculate_metrics_locally.py
```

**Tiempo estimado:** 30-60 minutos (depende de tu conexión y CPU)

### Paso 4: Subir el CSV al Repositorio

```bash
# El script genera: r3act_metrics_preprocessed.csv
# Súbelo a tu repositorio GitHub

git add r3act_metrics_preprocessed.csv
git commit -m "Add pre-processed R3ACT metrics"
git push origin main
```

### Paso 5: Verificar en Streamlit

El dashboard Streamlit cargará automáticamente el CSV desde GitHub y mostrará las métricas calculadas.

## Verificación

Después de subir el CSV, el dashboard debería mostrar:
- ✅ Métricas CRT, TSI, GIRI calculadas
- ✅ Gráficos funcionando
- ✅ Filtros funcionando correctamente

## Notas

- El CSV contiene todos los eventos críticos con sus métricas calculadas
- Los filtros (jugador, equipo, partido) funcionan con los datos pre-procesados
- El cálculo es REAL y aplicable según los filtros seleccionados
- El CSV se actualiza automáticamente cuando cambias los filtros en Streamlit

