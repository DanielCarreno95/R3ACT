# INSTRUCCIONES PARA CALCULAR MÉTRICAS REALES

## Situación Actual

El CSV `r3act_metrics_preprocessed.csv` tiene la estructura correcta pero **métricas = None** porque los archivos de tracking están en Git LFS (89MB+ cada uno) y no se pueden descargar desde Streamlit Cloud o sin Git LFS instalado.

## Solución: Ejecutar Localmente

### Paso 1: Instalar Git LFS

**Windows:**
```powershell
# Opción 1: Con Chocolatey
choco install git-lfs

# Opción 2: Descargar desde
# https://git-lfs.github.com/
# Ejecutar el instalador y luego:
git lfs install
```

**Verificar instalación:**
```bash
git lfs version
```

### Paso 2: Clonar Repositorio SkillCorner con LFS

```bash
# Clonar el repositorio (esto descargará los archivos LFS automáticamente)
git clone https://github.com/SkillCorner/opendata.git
cd opendata
git lfs pull
```

**NOTA:** Esto descargará ~890MB de datos (10 partidos × 89MB cada uno)

### Paso 3: Configurar el Script para Usar Archivos Locales

Modifica `src/data_loader.py` temporalmente para usar archivos locales en lugar de descargar desde GitHub.

### Paso 4: Ejecutar Cálculo

```bash
python calculate_metrics_locally.py
```

**Tiempo estimado:** 30-60 minutos

### Paso 5: Subir CSV con Métricas Reales

```bash
git add r3act_metrics_preprocessed.csv
git commit -m "Add pre-processed R3ACT metrics with real calculations"
git push origin main
```

## Alternativa: Usar Datos de Muestra

Si no puedes ejecutar con Git LFS, el dashboard funcionará con el CSV actual (métricas = None) pero mostrará N/A en los KPIs.

## Verificación

Después de subir el CSV con métricas reales, el dashboard debería mostrar:
- ✅ Métricas CRT, TSI, GIRI con valores numéricos
- ✅ Gráficos funcionando
- ✅ Filtros aplicando correctamente

