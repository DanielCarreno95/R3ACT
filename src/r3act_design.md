# R3ACT System Design - Basado en Exploración de Datos

## Eventos Críticos Identificados en dynamic_events.csv

### 1. Pérdidas de Posesión
- **Campo**: `end_type == 'possession_loss'`
- **Contexto adicional**: 
  - `third_start` / `third_end`: Zona del campo (defensive_third, middle_third, attacking_third)
  - `penalty_area_start`: Si está en área de penalti
  - `team_possession_loss_in_phase`: Pérdida en fase de posesión
- **Ponderación sugerida**: Alta si es en defensive_third o penalty_area

### 2. Pases Fallidos
- **Campo**: `pass_outcome == 'unsuccessful'` o `pass_outcome == 'offside'`
- **Contexto adicional**:
  - `third_start`: Zona del campo
  - `dangerous`: Si el pase era peligroso
  - `lead_to_shot` / `lead_to_goal`: Si el pase fallido llevó a tiro/gol
- **Ponderación sugerida**: Alta si es dangerous o lead_to_shot

### 3. Goles Recibidos
- **Campo**: `game_interruption_after == 'goal_against'` o `lead_to_goal == True` (para el oponente)
- **También en phases_of_play**: `team_possession_lead_to_goal == True` (para el oponente)
- **Ponderación sugerida**: Máxima (2.0)

### 4. Goles Marcados
- **Campo**: `game_interruption_after == 'goal_for'` o `lead_to_goal == True` (para el equipo)
- **Para GIRI**: Activa análisis de respuesta del equipo que marcó

### 5. Errores Defensivos
- **Campo**: `end_type == 'clearance'` seguido de `possession_loss` o `lead_to_shot`
- **Contexto**: `inside_defensive_shape_start/end`: Si estaba dentro de la forma defensiva
- **Ponderación sugerida**: Media-Alta

### 6. Intercepciones Concedidas
- **Campo**: `start_type == 'pass_interception'` (cuando el oponente intercepta)
- **Contexto**: `third_start`: Zona del campo
- **Ponderación sugerida**: Media

## Métricas Físicas para CRT (Estado Base)

### Métricas Individuales (por jugador):
1. **Velocidad promedio** (m/s) - calculada desde tracking
2. **Aceleración promedio** (m/s²) - derivada de velocidad
3. **Distancia recorrida por minuto** (m/min)
4. **Posición promedio X** (metros desde centro)
5. **Posición promedio Y** (metros desde centro)
6. **Distancia al centro del campo** (m)
7. **Frecuencia de cambios de dirección** (cambios/min)

### Métricas Colectivas (por equipo):
1. **Compactness** (área del convex hull en m²)
2. **Velocidad promedio del bloque** (m/s)
3. **Distancia promedio entre jugadores** (m)
4. **Ancho del bloque** (m) - desde phases_of_play: `team_in_possession_width`
5. **Largo del bloque** (m) - desde phases_of_play: `team_in_possession_length`

## Cálculo de TSI (Team Support Index)

### Componente 1: Proximidad Física
- **Métrica**: Distancia promedio del equipo (compañeros + oponentes) al jugador que erró
- **Cálculo**: 
  - Pre-error: promedio de distancias en ventana pre
  - Post-error: promedio de distancias en ventana post
  - TSI_proximity = (pre - post) / pre  (positivo = más cerca = más apoyo)

### Componente 2: Frecuencia de Posesión
- **Métrica**: % de posesión del equipo post-error vs pre-error
- **Cálculo desde tracking**: 
  - Contar frames donde `possession['group'] == 'home'` o `'away'`
  - TSI_possession = (post_% - pre_%) / pre_%

### Componente 3: Estructura Defensiva (solo cuando defiende)
- **Métricas desde phases_of_play**:
  - `team_in_possession_width`: Ancho del bloque
  - `team_in_possession_length`: Largo del bloque
  - Compactness = width * length (menor = más compacto)
- **Cálculo**:
  - Pre-error: compactness promedio en ventana pre
  - Post-error: compactness promedio en ventana post
  - TSI_structure = (pre - post) / pre  (positivo = más compacto = mejor respuesta)

### TSI Final:
- TSI = (TSI_proximity * w1 + TSI_possession * w2 + TSI_structure * w3) / (w1 + w2 + w3)
- Pesos por defecto: w1=0.4, w2=0.3, w3=0.3

## Cálculo de GIRI (Goal Impact Response Index)

### Métricas Tácticas Post-Gol:
1. **Altura del bloque** (posición Y promedio del equipo)
2. **Velocidad media del equipo** (m/s)
3. **Número de pases por secuencia** (desde dynamic_events: contar `player_possession` consecutivos)
4. **Intensidad de pressing** (número de `on_ball_engagement` por minuto)
5. **Compactness** (desde phases_of_play)

### Cálculo:
- Pre-gol: promedio de métricas en ventana pre
- Post-gol: promedio de métricas en ventana post
- GIRI = cambio normalizado en cada métrica
- GIRI final = promedio de cambios (o promedio ponderado)

## Ventanas Temporales

### Predefinidas:
- **Short**: 2 minutos (120 segundos)
- **Medium**: 5 minutos (300 segundos)
- **Long**: 10 minutos (600 segundos)

### Implementación:
- Usuario selecciona ventana
- Pre y post son simétricas
- Resultados mostrados por ventana seleccionada

## Sistema de Ponderación

### Por Tipo de Evento Crítico:
```python
EVENT_WEIGHTS = {
    "possession_loss_defensive_third": 1.0,
    "possession_loss_penalty_area": 1.5,
    "failed_pass_dangerous": 1.2,
    "failed_pass_lead_to_shot": 1.5,
    "goal_conceded": 2.0,
    "defensive_error_lead_to_shot": 1.3,
    "interception_conceded_dangerous": 0.8,
    # ... más eventos
}
```

### Normalización:
- Todos los pesos se normalizan para que sumen 1.0
- Permite comparación justa entre diferentes configuraciones

## Estado Base (Baseline)

### Cálculo:
- **Individual**: Promedio de métricas del jugador sobre TODOS los partidos (10 partidos)
- **Colectivo**: Promedio de métricas del equipo sobre TODOS los partidos
- **NO por partido**: El estado base es global, no específico de partido

### Almacenamiento:
- Se calcula una vez al inicio
- Se guarda en estructura: `{player_id: {metric: value}}` y `{team_id: {metric: value}}`

## Flujo de Procesamiento

1. **Cargar todos los partidos** (10 partidos)
2. **Calcular estado base** (promedios globales)
3. **Para cada partido**:
   - Detectar eventos críticos
   - Para cada evento crítico:
     - Extraer ventana temporal (pre y post)
     - Calcular métricas pre-error
     - Calcular métricas post-error
     - Calcular CRT, TSI, GIRI (si aplica)
4. **Agregar resultados** con ponderación
5. **Generar dataset final** con métricas calculadas

