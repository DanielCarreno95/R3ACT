"""
R3ACT System - Sistema principal que orquesta todo el análisis
Resilience, Reaction and Recovery Analysis of Critical Transitions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from src.data_loader import SkillCornerDataLoader
from src.event_detector import CriticalEventDetector
from src.baseline_calculator import BaselineCalculator
from src.metrics_calculator import MetricsCalculator


class R3ACTSystem:
    """Sistema principal R3ACT"""
    
    # Ventanas temporales predefinidas (en segundos)
    TIME_WINDOWS = {
        'short': 120,   # 2 minutos
        'medium': 300,  # 5 minutos
        'long': 600     # 10 minutos
    }
    
    def __init__(self, event_weights: Optional[Dict] = None, 
                 time_window: str = 'medium'):
        """
        Inicializa el sistema R3ACT
        
        Args:
            event_weights: Pesos personalizados para eventos críticos
            time_window: Ventana temporal ('short', 'medium', 'long')
        """
        self.data_loader = SkillCornerDataLoader()
        self.event_detector = CriticalEventDetector(event_weights)
        self.baseline_calculator = BaselineCalculator()
        self.metrics_calculator = None  # Se inicializa después de calcular baselines
        
        self.time_window_seconds = self.TIME_WINDOWS.get(time_window, 300)
        self.selected_window = time_window
        
        self.results = []
    
    def process_all_matches(self, load_tracking: bool = True) -> pd.DataFrame:
        """
        Procesa todos los partidos y calcula métricas R3ACT
        
        Args:
            load_tracking: Si True, carga datos de tracking (más lento pero completo)
            
        Returns:
            DataFrame con resultados de todas las métricas
        """
        print("="*60)
        print("SISTEMA R3ACT - Procesando todos los partidos")
        print("="*60)
        
        # 1. Cargar datos de todos los partidos
        print("\n[1/5] Cargando datos de partidos...")
        all_matches_data = self.data_loader.load_all_matches_data()
        match_ids = list(all_matches_data.keys())
        print(f"Cargados {len(match_ids)} partidos")
        
        # 2. Cargar tracking data (opcional, puede ser lento)
        tracking_data_dict = {}
        if load_tracking:
            print("\n[2/5] Cargando datos de tracking (esto puede tardar)...")
            for match_id in match_ids:
                try:
                    tracking_frames = self.data_loader.load_tracking_data(match_id)
                    tracking_data_dict[match_id] = tracking_frames
                    print(f"  Partido {match_id}: {len(tracking_frames)} frames")
                except Exception as e:
                    print(f"  Advertencia: Error cargando tracking para {match_id}: {e}")
                    tracking_data_dict[match_id] = []
        else:
            print("\n[2/5] Omitiendo carga de tracking (load_tracking=False)")
        
        # 3. Calcular estado base sobre todos los partidos
        print("\n[3/5] Calculando estado base...")
        baselines = self.baseline_calculator.calculate_baselines(
            all_matches_data, tracking_data_dict
        )
        
        # Calcular baselines de velocidad
        if load_tracking:
            self.baseline_calculator.calculate_velocity_baselines(
                all_matches_data, tracking_data_dict
            )
        
        # 4. Inicializar calculador de métricas
        self.metrics_calculator = MetricsCalculator(self.baseline_calculator)
        
        # 5. Procesar cada partido
        print(f"\n[4/5] Procesando partidos (ventana: {self.selected_window}, {self.time_window_seconds}s)...")
        all_results = []
        
        for match_id in match_ids:
            print(f"\nProcesando partido {match_id}...")
            try:
                match_results = self._process_match(
                    match_id,
                    all_matches_data[match_id],
                    tracking_data_dict.get(match_id, [])
                )
                all_results.extend(match_results)
            except Exception as e:
                print(f"  Error procesando partido {match_id}: {e}")
                continue
        
        # 6. Crear DataFrame final
        print("\n[5/5] Generando dataset final...")
        if all_results:
            results_df = pd.DataFrame(all_results)
            self.results = results_df
            print(f"Dataset generado: {len(results_df)} eventos críticos analizados")
            return results_df
        else:
            print("No se generaron resultados")
            return pd.DataFrame()
    
    def _process_match(self, match_id: str, match_data: Dict,
                      tracking_frames: List[Dict]) -> List[Dict]:
        """Procesa un partido individual"""
        results = []
        
        # Detectar eventos críticos
        events_df = match_data['events']
        phases_df = match_data['phases']
        match_json = match_data['match_json']
        
        critical_events = self.event_detector.detect_critical_events(
            events_df, match_id, match_json
        )
        
        if critical_events.empty:
            return results
        
        print(f"  Detectados {len(critical_events)} eventos críticos")
        
        # Procesar cada evento crítico
        for _, event in critical_events.iterrows():
            event_result = {
                'match_id': match_id,
                'event_id': event.get('event_id'),
                'event_type': event.get('event_type'),
                'event_weight': event.get('event_weight'),
                'timestamp': event.get('timestamp'),
                'frame': event.get('frame'),
                'period': event.get('period'),
                'player_id': event.get('player_id'),
                'player_name': event.get('player_name'),
                'team_id': event.get('team_id'),
                'is_home': event.get('is_home'),
                'time_window': self.selected_window,
            }
            
            # Calcular CRT (si hay tracking y player_id)
            if tracking_frames and event.get('player_id'):
                try:
                    crt = self.metrics_calculator.calculate_crt(
                        int(event.get('player_id')),
                        float(event.get('timestamp')),
                        int(event.get('frame', 0)),
                        tracking_frames,
                        self.time_window_seconds
                    )
                    event_result['CRT'] = crt
                except Exception as e:
                    event_result['CRT'] = None
            
            # Calcular TSI (si hay tracking y phases)
            if tracking_frames and not phases_df.empty:
                try:
                    tsi = self.metrics_calculator.calculate_tsi(
                        int(event.get('player_id', 0)),
                        int(event.get('team_id', 0)),
                        float(event.get('timestamp')),
                        int(event.get('frame', 0)),
                        tracking_frames,
                        phases_df,
                        self.time_window_seconds
                    )
                    event_result['TSI'] = tsi
                except Exception as e:
                    event_result['TSI'] = None
            
            # Calcular GIRI (solo para goles)
            if event.get('event_type') in ['goal_scored', 'goal_conceded']:
                if tracking_frames and not phases_df.empty:
                    try:
                        giri = self.metrics_calculator.calculate_giri(
                            int(event.get('team_id', 0)),
                            float(event.get('timestamp')),
                            tracking_frames,
                            phases_df,
                            self.time_window_seconds
                        )
                        event_result['GIRI'] = giri
                    except Exception as e:
                        event_result['GIRI'] = None
            else:
                event_result['GIRI'] = None
            
            results.append(event_result)
        
        return results
    
    def get_results_summary(self) -> Dict:
        """Obtiene resumen estadístico de los resultados"""
        if self.results.empty:
            return {}
        
        summary = {
            'total_events': len(self.results),
            'events_by_type': self.results['event_type'].value_counts().to_dict(),
            'crt_stats': {
                'mean': self.results['CRT'].mean(),
                'median': self.results['CRT'].median(),
                'std': self.results['CRT'].std(),
                'min': self.results['CRT'].min(),
                'max': self.results['CRT'].max(),
            } if 'CRT' in self.results.columns else None,
            'tsi_stats': {
                'mean': self.results['TSI'].mean(),
                'median': self.results['TSI'].median(),
                'std': self.results['TSI'].std(),
            } if 'TSI' in self.results.columns else None,
            'giri_stats': {
                'mean': self.results['GIRI'].mean(),
                'median': self.results['GIRI'].median(),
                'std': self.results['GIRI'].std(),
            } if 'GIRI' in self.results.columns else None,
        }
        
        return summary
    
    def save_results(self, filepath: str):
        """Guarda resultados en CSV"""
        if not self.results.empty:
            self.results.to_csv(filepath, index=False)
            print(f"Resultados guardados en {filepath}")
        else:
            print("No hay resultados para guardar")

