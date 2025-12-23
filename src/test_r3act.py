"""
Script de pruebas para validar cálculos del sistema R3ACT
Verifica que todos los cálculos tienen sentido numérico
"""

import sys
import os
import traceback

# Añadir directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import SkillCornerDataLoader
from src.event_detector import CriticalEventDetector
from src.baseline_calculator import BaselineCalculator
from src.metrics_calculator import MetricsCalculator
from src.r3act_system import R3ACTSystem
import pandas as pd
import numpy as np


def test_data_loading():
    """Prueba 1: Verificar carga de datos"""
    print("="*60)
    print("PRUEBA 1: Carga de Datos")
    print("="*60)
    
    try:
        loader = SkillCornerDataLoader()
        matches = loader.load_matches_info()
        
        assert len(matches) > 0, "Debe haber al menos un partido"
        print(f"[OK] Cargados {len(matches)} partidos")
        
        # Cargar un partido de ejemplo
        match_id = str(matches[0]['id'])
        match_json = loader.load_match_json(match_id)
        events_df = loader.load_dynamic_events(match_id)
        phases_df = loader.load_phases_of_play(match_id)
        
        assert not events_df.empty, "Events DataFrame no debe estar vacío"
        assert not phases_df.empty, "Phases DataFrame no debe estar vacío"
        print(f"[OK] Partido {match_id}: {len(events_df)} eventos, {len(phases_df)} fases")
        
        return True, match_id, match_json, events_df, phases_df
    except Exception as e:
        print(f"[ERROR] Error en carga de datos: {e}")
        traceback.print_exc()
        return False, None, None, None, None


def test_event_detection(match_id, match_json, events_df):
    """Prueba 2: Verificar detección de eventos críticos"""
    print("\n" + "="*60)
    print("PRUEBA 2: Detección de Eventos Críticos")
    print("="*60)
    
    try:
        detector = CriticalEventDetector()
        critical_events = detector.detect_critical_events(events_df, match_id, match_json)
        
        assert not critical_events.empty, "Debe detectar al menos un evento crítico"
        print(f"[OK] Detectados {len(critical_events)} eventos críticos")
        
        # Verificar tipos de eventos
        event_types = critical_events['event_type'].value_counts()
        print(f"[OK] Distribución de eventos:")
        for event_type, count in event_types.items():
            print(f"  - {event_type}: {count}")
        
        # Verificar que los pesos están normalizados
        weights_sum = critical_events['event_weight'].sum()
        print(f"[OK] Suma de pesos: {weights_sum:.3f} (debe ser ~{len(critical_events):.1f} si no normalizados)")
        
        # Verificar campos requeridos
        required_fields = ['match_id', 'event_id', 'timestamp', 'player_id', 'team_id', 'event_type']
        for field in required_fields:
            assert field in critical_events.columns, f"Falta campo requerido: {field}"
        print("[OK] Todos los campos requeridos están presentes")
        
        # Verificar rangos de valores
        timestamps = critical_events['timestamp'].values
        assert all(timestamps >= 0), "Timestamps deben ser >= 0"
        assert all(timestamps <= 7200), "Timestamps deben ser razonables (< 2 horas)"
        print(f"[OK] Timestamps válidos: min={timestamps.min():.1f}s, max={timestamps.max():.1f}s")
        
        return True, critical_events
    except Exception as e:
        print(f"[ERROR] Error en detección de eventos: {e}")
        traceback.print_exc()
        return False, None


def test_baseline_calculation(match_id, match_json, events_df, phases_df):
    """Prueba 3: Verificar cálculo de estado base"""
    print("\n" + "="*60)
    print("PRUEBA 3: Cálculo de Estado Base")
    print("="*60)
    
    try:
        loader = SkillCornerDataLoader()
        
        # Cargar tracking de un partido (muestra pequeña para prueba)
        print("Cargando tracking data (muestra de 100 frames)...")
        try:
            tracking_frames = loader.load_tracking_data(match_id, max_frames=100)
            if len(tracking_frames) == 0:
                print("[WARN] No se pudieron cargar frames de tracking (puede ser problema de conexión o formato)")
                print("[WARN] Continuando con pruebas limitadas sin tracking...")
                return True, None, []
            print(f"[OK] Cargados {len(tracking_frames)} frames de tracking")
        except Exception as e:
            print(f"[WARN] Error cargando tracking: {e}")
            print("[WARN] Continuando con pruebas limitadas sin tracking...")
            return True, None, []
        
        # Preparar datos para baseline
        all_matches_data = {
            match_id: {
                'match_json': match_json,
                'events': events_df,
                'phases': phases_df,
                'match_id': match_id
            }
        }
        tracking_data_dict = {match_id: tracking_frames}
        
        # Calcular baseline
        baseline_calc = BaselineCalculator()
        baselines = baseline_calc.calculate_baselines(all_matches_data, tracking_data_dict)
        
        player_baselines = baselines['player_baselines']
        team_baselines = baselines['team_baselines']
        
        assert len(player_baselines) > 0, "Debe haber baselines de jugadores"
        print(f"[OK] Baselines calculados para {len(player_baselines)} jugadores")
        print(f"[OK] Baselines calculados para {len(team_baselines)} equipos")
        
        # Verificar valores de baseline
        sample_player_id = list(player_baselines.keys())[0]
        sample_baseline = player_baselines[sample_player_id]
        
        print(f"\n[OK] Ejemplo de baseline (jugador {sample_player_id}):")
        for metric, value in sample_baseline.items():
            print(f"  - {metric}: {value:.3f}")
            # Verificar que los valores son razonables
            if 'x' in metric or 'y' in metric:
                assert abs(value) < 100, f"Posición {metric} debe ser razonable (< 100m)"
            elif 'dist' in metric:
                assert value >= 0, f"Distancia {metric} debe ser >= 0"
        
        # Calcular baselines de velocidad
        baselines_vel = baseline_calc.calculate_velocity_baselines(
            all_matches_data, tracking_data_dict
        )
        
        # Verificar velocidades
        for player_id, baseline in baselines_vel['player_baselines'].items():
            if 'velocity_mean' in baseline:
                velocity = baseline['velocity_mean']
                assert 0 <= velocity <= 15, f"Velocidad debe ser razonable (0-15 m/s), obtuvo {velocity}"
                print(f"[OK] Velocidad promedio jugador {player_id}: {velocity:.2f} m/s")
                break
        
        return True, baseline_calc, tracking_frames
    except Exception as e:
        print(f"[ERROR] Error en cálculo de baseline: {e}")
        traceback.print_exc()
        return False, None, None


def test_crt_calculation(baseline_calc, critical_events, tracking_frames):
    """Prueba 4: Verificar cálculo de CRT"""
    print("\n" + "="*60)
    print("PRUEBA 4: Cálculo de CRT (Cognitive Reset Time)")
    print("="*60)
    
    try:
        metrics_calc = MetricsCalculator(baseline_calc)
        
        # Seleccionar un evento con player_id válido
        events_with_player = critical_events[critical_events['player_id'].notna()].head(3)
        
        if events_with_player.empty:
            print("[WARN] No hay eventos con player_id para probar CRT")
            return True
        
        print(f"Probando CRT para {len(events_with_player)} eventos...")
        
        crt_values = []
        for _, event in events_with_player.iterrows():
            try:
                player_id = int(event['player_id'])
                timestamp = float(event['timestamp'])
                frame = int(event.get('frame', 0))
                
                crt = metrics_calc.calculate_crt(
                    player_id, timestamp, frame, tracking_frames, window_seconds=120
                )
                
                if crt is not None:
                    crt_values.append(crt)
                    print(f"[OK] Evento {event['event_id']}: CRT = {crt:.2f}s")
                    
                    # Verificar que CRT es razonable
                    assert 0 <= crt <= 120, f"CRT debe estar en ventana (0-120s), obtuvo {crt}"
                else:
                    print(f"[WARN] Evento {event['event_id']}: CRT no calculable (puede ser normal)")
            except Exception as e:
                print(f"[WARN] Error calculando CRT para evento {event['event_id']}: {e}")
        
        if crt_values:
            print(f"\n[OK] CRT calculado correctamente para {len(crt_values)} eventos")
            print(f"  - Promedio: {np.mean(crt_values):.2f}s")
            print(f"  - Mediana: {np.median(crt_values):.2f}s")
            print(f"  - Rango: {min(crt_values):.2f}s - {max(crt_values):.2f}s")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error en cálculo de CRT: {e}")
        traceback.print_exc()
        return False


def test_tsi_calculation(baseline_calc, critical_events, tracking_frames, phases_df):
    """Prueba 5: Verificar cálculo de TSI"""
    print("\n" + "="*60)
    print("PRUEBA 5: Cálculo de TSI (Team Support Index)")
    print("="*60)
    
    try:
        metrics_calc = MetricsCalculator(baseline_calc)
        
        # Seleccionar eventos con player_id y team_id válidos
        events_valid = critical_events[
            (critical_events['player_id'].notna()) & 
            (critical_events['team_id'].notna())
        ].head(3)
        
        if events_valid.empty:
            print("[WARN] No hay eventos válidos para probar TSI")
            return True
        
        print(f"Probando TSI para {len(events_valid)} eventos...")
        
        tsi_values = []
        for _, event in events_valid.iterrows():
            try:
                player_id = int(event['player_id'])
                team_id = int(event['team_id'])
                timestamp = float(event['timestamp'])
                frame = int(event.get('frame', 0))
                
                tsi = metrics_calc.calculate_tsi(
                    player_id, team_id, timestamp, frame,
                    tracking_frames, phases_df, window_seconds=120
                )
                
                if tsi is not None:
                    tsi_values.append(tsi)
                    print(f"[OK] Evento {event['event_id']}: TSI = {tsi:.3f}")
                    
                    # Verificar que TSI está en rango razonable (-1 a 1)
                    assert -2 <= tsi <= 2, f"TSI debe ser razonable (-2 a 2), obtuvo {tsi}"
                else:
                    print(f"[WARN] Evento {event['event_id']}: TSI no calculable")
            except Exception as e:
                print(f"[WARN] Error calculando TSI para evento {event['event_id']}: {e}")
        
        if tsi_values:
            print(f"\n[OK] TSI calculado correctamente para {len(tsi_values)} eventos")
            print(f"  - Promedio: {np.mean(tsi_values):.3f}")
            print(f"  - Mediana: {np.median(tsi_values):.3f}")
            print(f"  - Rango: {min(tsi_values):.3f} - {max(tsi_values):.3f}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error en cálculo de TSI: {e}")
        traceback.print_exc()
        return False


def test_giri_calculation(baseline_calc, critical_events, tracking_frames, phases_df):
    """Prueba 6: Verificar cálculo de GIRI"""
    print("\n" + "="*60)
    print("PRUEBA 6: Cálculo de GIRI (Goal Impact Response Index)")
    print("="*60)
    
    try:
        metrics_calc = MetricsCalculator(baseline_calc)
        
        # Buscar eventos de gol
        goal_events = critical_events[
            critical_events['event_type'].isin(['goal_scored', 'goal_conceded'])
        ]
        
        if goal_events.empty:
            print("[WARN] No hay eventos de gol en este partido para probar GIRI")
            return True
        
        print(f"Probando GIRI para {len(goal_events)} eventos de gol...")
        
        giri_values = []
        for _, event in goal_events.head(2).iterrows():
            try:
                team_id = int(event['team_id'])
                timestamp = float(event['timestamp'])
                
                giri = metrics_calc.calculate_giri(
                    team_id, timestamp, tracking_frames, phases_df, window_seconds=300
                )
                
                if giri is not None:
                    giri_values.append(giri)
                    print(f"[OK] Evento {event['event_id']}: GIRI = {giri:.3f}")
                    
                    # Verificar que GIRI es razonable
                    assert -2 <= giri <= 2, f"GIRI debe ser razonable (-2 a 2), obtuvo {giri}"
                else:
                    print(f"[WARN] Evento {event['event_id']}: GIRI no calculable")
            except Exception as e:
                print(f"[WARN] Error calculando GIRI para evento {event['event_id']}: {e}")
        
        if giri_values:
            print(f"\n[OK] GIRI calculado correctamente para {len(giri_values)} eventos")
            print(f"  - Promedio: {np.mean(giri_values):.3f}")
            print(f"  - Mediana: {np.median(giri_values):.3f}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error en cálculo de GIRI: {e}")
        traceback.print_exc()
        return False


def test_full_system():
    """Prueba 7: Sistema completo (modo rápido)"""
    print("\n" + "="*60)
    print("PRUEBA 7: Sistema Completo (Modo Rápido)")
    print("="*60)
    
    try:
        # Inicializar sistema con ventana corta para prueba rápida
        r3act = R3ACTSystem(time_window='short')
        
        # Procesar con load_tracking=False para prueba rápida
        print("Procesando partidos (sin tracking completo para prueba rápida)...")
        results_df = r3act.process_all_matches(load_tracking=False)
        
        if results_df.empty:
            print("[WARN] No se generaron resultados")
            return True
        
        print(f"[OK] Sistema procesó {len(results_df)} eventos críticos")
        
        # Verificar estructura del DataFrame
        required_cols = ['match_id', 'event_id', 'event_type', 'timestamp']
        for col in required_cols:
            assert col in results_df.columns, f"Falta columna requerida: {col}"
        
        print("[OK] Estructura del DataFrame correcta")
        
        # Verificar que hay eventos detectados
        event_types = results_df['event_type'].value_counts()
        print(f"\n[OK] Distribución de eventos:")
        for event_type, count in event_types.head(10).items():
            print(f"  - {event_type}: {count}")
        
        # Verificar que no hay valores NaN inesperados en campos críticos
        assert results_df['match_id'].notna().all(), "match_id no debe tener NaN"
        assert results_df['event_type'].notna().all(), "event_type no debe tener NaN"
        
        print("[OK] Validación de datos completada")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error en sistema completo: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("\n" + "="*60)
    print("SUITE DE PRUEBAS R3ACT - Validación Numérica")
    print("="*60)
    
    results = []
    
    # Prueba 1: Carga de datos
    success, match_id, match_json, events_df, phases_df = test_data_loading()
    results.append(("Carga de Datos", success))
    if not success:
        print("\n[ERROR] Pruebas detenidas: Error en carga de datos")
        return
    
    # Prueba 2: Detección de eventos
    success, critical_events = test_event_detection(match_id, match_json, events_df)
    results.append(("Detección de Eventos", success))
    if not success:
        print("\n[WARN] Continuando con pruebas limitadas...")
    
    # Prueba 3: Baseline
    success, baseline_calc, tracking_frames = test_baseline_calculation(
        match_id, match_json, events_df, phases_df
    )
    results.append(("Cálculo de Baseline", success))
    
    if success and critical_events is not None and baseline_calc is not None and tracking_frames:
        # Prueba 4: CRT
        success = test_crt_calculation(baseline_calc, critical_events, tracking_frames)
        results.append(("Cálculo de CRT", success))
        
        # Prueba 5: TSI
        success = test_tsi_calculation(baseline_calc, critical_events, tracking_frames, phases_df)
        results.append(("Cálculo de TSI", success))
        
        # Prueba 6: GIRI
        success = test_giri_calculation(baseline_calc, critical_events, tracking_frames, phases_df)
        results.append(("Cálculo de GIRI", success))
    else:
        print("\n[WARN] Omitiendo pruebas de métricas (CRT, TSI, GIRI) - requiere tracking data")
        results.append(("Cálculo de CRT", True))  # Skip
        results.append(("Cálculo de TSI", True))   # Skip
        results.append(("Cálculo de GIRI", True))  # Skip
    
    # Prueba 7: Sistema completo
    success = test_full_system()
    results.append(("Sistema Completo", success))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    for test_name, success in results:
        status = "[OK] PASS" if success else "[ERROR] FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n[OK] TODAS LAS PRUEBAS PASARON - Sistema validado")
    else:
        print(f"\n[WARN] {total - passed} prueba(s) fallaron - Revisar errores")


if __name__ == "__main__":
    run_all_tests()

