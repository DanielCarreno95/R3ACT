"""
Validación específica de cálculos numéricos
Verifica que los valores calculados tienen sentido
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.r3act_system import R3ACTSystem


def validate_numerical_results():
    """Valida que los resultados numéricos tienen sentido"""
    print("="*60)
    print("VALIDACIÓN DE CÁLCULOS NUMÉRICOS")
    print("="*60)
    
    # Procesar con sistema completo (sin tracking para rapidez)
    r3act = R3ACTSystem(time_window='medium')
    results_df = r3act.process_all_matches(load_tracking=False)
    
    if results_df.empty:
        print("[ERROR] No se generaron resultados")
        return False
    
    print(f"\n[OK] Total de eventos procesados: {len(results_df)}")
    
    # Validación 1: Verificar que los timestamps son consistentes
    print("\n[VALIDACIÓN 1] Timestamps")
    timestamps = results_df['timestamp'].values
    assert all(timestamps >= 0), "Timestamps negativos encontrados"
    assert all(timestamps <= 7200), "Timestamps mayores a 2 horas (7200s)"
    print(f"  - Rango: {timestamps.min():.1f}s - {timestamps.max():.1f}s")
    print(f"  - Media: {timestamps.mean():.1f}s")
    print(f"  [OK] Timestamps válidos")
    
    # Validación 2: Verificar distribución de eventos
    print("\n[VALIDACIÓN 2] Distribución de Eventos")
    event_counts = results_df['event_type'].value_counts()
    total_events = len(results_df)
    
    for event_type, count in event_counts.items():
        percentage = (count / total_events) * 100
        print(f"  - {event_type}: {count} ({percentage:.1f}%)")
        
        # Verificar que ningún tipo de evento domina completamente (>90%)
        assert percentage < 90, f"Tipo de evento {event_type} domina demasiado ({percentage:.1f}%)"
    
    print(f"  [OK] Distribución balanceada")
    
    # Validación 3: Verificar pesos de eventos
    print("\n[VALIDACIÓN 3] Pesos de Eventos")
    weights = results_df['event_weight'].values
    
    # Los pesos deben estar en rango razonable (0-2 típicamente)
    assert all(weights >= 0), "Pesos negativos encontrados"
    assert all(weights <= 3), "Pesos excesivamente altos (>3)"
    
    print(f"  - Rango: {weights.min():.3f} - {weights.max():.3f}")
    print(f"  - Media: {weights.mean():.3f}")
    print(f"  [OK] Pesos válidos")
    
    # Validación 4: Verificar que los eventos críticos tienen sentido
    print("\n[VALIDACIÓN 4] Coherencia de Eventos")
    
    # Verificar que los goles son eventos raros pero presentes
    goals = results_df[results_df['event_type'].isin(['goal_scored', 'goal_conceded'])]
    goal_percentage = (len(goals) / total_events) * 100
    print(f"  - Goles: {len(goals)} ({goal_percentage:.2f}%)")
    assert 0.1 <= goal_percentage <= 20, f"Porcentaje de goles fuera de rango esperado ({goal_percentage:.2f}%)"
    
    # Verificar que las pérdidas de posesión son comunes
    possession_losses = results_df[results_df['event_type'].str.contains('possession_loss', na=False)]
    loss_percentage = (len(possession_losses) / total_events) * 100
    print(f"  - Pérdidas de posesión: {len(possession_losses)} ({loss_percentage:.2f}%)")
    assert loss_percentage >= 10, f"Muy pocas pérdidas de posesión ({loss_percentage:.2f}%)"
    
    print(f"  [OK] Coherencia de eventos válida")
    
    # Validación 5: Verificar estructura de datos
    print("\n[VALIDACIÓN 5] Estructura de Datos")
    required_cols = ['match_id', 'event_id', 'event_type', 'timestamp', 'player_id', 'team_id']
    for col in required_cols:
        assert col in results_df.columns, f"Falta columna requerida: {col}"
        null_percentage = (results_df[col].isna().sum() / len(results_df)) * 100
        print(f"  - {col}: {null_percentage:.1f}% valores nulos")
    
    print(f"  [OK] Estructura correcta")
    
    # Validación 6: Verificar que los partidos están distribuidos
    print("\n[VALIDACIÓN 6] Distribución por Partido")
    matches = results_df['match_id'].value_counts()
    print(f"  - Partidos únicos: {len(matches)}")
    print(f"  - Eventos por partido: min={matches.min()}, max={matches.max()}, media={matches.mean():.1f}")
    
    # Verificar que todos los partidos tienen eventos
    assert len(matches) == 10, f"Debe haber eventos de 10 partidos, encontré {len(matches)}"
    assert matches.min() > 0, "Algún partido no tiene eventos"
    
    print(f"  [OK] Distribución por partido válida")
    
    print("\n" + "="*60)
    print("[OK] TODAS LAS VALIDACIONES NUMÉRICAS PASARON")
    print("="*60)
    
    return True


if __name__ == "__main__":
    validate_numerical_results()

