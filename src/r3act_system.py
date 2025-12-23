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
                    if len(tracking_frames) == 0:
                        print(f"  ADVERTENCIA: Partido {match_id}: 0 frames cargados - verificar URL o formato")
                    else:
                        print(f"  Partido {match_id}: {len(tracking_frames)} frames")
                except Exception as e:
                    print(f"  ERROR: Error cargando tracking para {match_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    tracking_data_dict[match_id] = []
        else:
            print("\n[2/5] Omitiendo carga de tracking (load_tracking=False)")
        
        # 3. Calcular estado base sobre todos los partidos
        print("\n[3/5] Calculando estado base...")
        if load_tracking and tracking_data_dict:
            baselines = self.baseline_calculator.calculate_baselines(
                all_matches_data, tracking_data_dict
            )
            
            # Calcular baselines de velocidad
            self.baseline_calculator.calculate_velocity_baselines(
                all_matches_data, tracking_data_dict
            )
            
            print(f"Baselines calculados: {len(self.baseline_calculator.player_baselines)} jugadores, {len(self.baseline_calculator.team_baselines)} equipos")
        else:
            print("Advertencia: No hay tracking data para calcular baselines")
        
        # 4. Inicializar calculador de métricas
        self.metrics_calculator = MetricsCalculator(self.baseline_calculator)
        print("MetricsCalculator inicializado")
        
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
        
        # 6. Crear DataFrame final y enriquecer con nombres
        print("\n[5/5] Generando dataset final...")
        if all_results:
            # Asegurar que TODOS los resultados tengan las columnas de métricas
            for result in all_results:
                if 'CRT' not in result:
                    result['CRT'] = None
                if 'TSI' not in result:
                    result['TSI'] = None
                if 'GIRI' not in result:
                    result['GIRI'] = None
            
            results_df = pd.DataFrame(all_results)
            
            # Verificar que las columnas existen después de crear el DataFrame
            if 'CRT' not in results_df.columns:
                results_df['CRT'] = None
            if 'TSI' not in results_df.columns:
                results_df['TSI'] = None
            if 'GIRI' not in results_df.columns:
                results_df['GIRI'] = None
            
            # Estadísticas de métricas calculadas
            crt_count = results_df['CRT'].notna().sum() if 'CRT' in results_df.columns else 0
            tsi_count = results_df['TSI'].notna().sum() if 'TSI' in results_df.columns else 0
            giri_count = results_df['GIRI'].notna().sum() if 'GIRI' in results_df.columns else 0
            
            print(f"  Métricas calculadas: CRT={crt_count}/{len(results_df)}, TSI={tsi_count}/{len(results_df)}, GIRI={giri_count}/{len(results_df)}")
            
            # Enriquecer con nombres de partidos, equipos y jugadores
            print("Enriqueciendo datos con nombres...")
            results_df = self._enrich_with_names(results_df, all_matches_data)
            
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
            
            # Inicializar métricas como None por defecto (SIEMPRE)
            event_result['CRT'] = None
            event_result['TSI'] = None
            event_result['GIRI'] = None
            
            # Calcular CRT (si hay tracking y player_id)
            if tracking_frames and len(tracking_frames) > 0 and event.get('player_id') and self.metrics_calculator:
                try:
                    crt = self.metrics_calculator.calculate_crt(
                        int(event.get('player_id')),
                        float(event.get('timestamp')),
                        int(event.get('frame', 0)),
                        tracking_frames,
                        self.time_window_seconds
                    )
                    event_result['CRT'] = crt
                    if crt is None:
                        print(f"    CRT no calculado para evento {event.get('event_id')} - player {event.get('player_id')}")
                except Exception as e:
                    print(f"    Error calculando CRT para evento {event.get('event_id')}: {e}")
                    event_result['CRT'] = None
            else:
                if not tracking_frames:
                    print(f"    Sin tracking para evento {event.get('event_id')}")
                elif not event.get('player_id'):
                    print(f"    Sin player_id para evento {event.get('event_id')}")
                elif not self.metrics_calculator:
                    print(f"    MetricsCalculator no inicializado")
            
            # Calcular TSI (si hay tracking y phases)
            if tracking_frames and len(tracking_frames) > 0 and not phases_df.empty and self.metrics_calculator:
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
                    if tsi is None:
                        print(f"    TSI no calculado para evento {event.get('event_id')}")
                except Exception as e:
                    print(f"    Error calculando TSI para evento {event.get('event_id')}: {e}")
                    event_result['TSI'] = None
            
            # Calcular GIRI (solo para goles)
            if event.get('event_type') in ['goal_scored', 'goal_conceded']:
                if tracking_frames and len(tracking_frames) > 0 and not phases_df.empty and self.metrics_calculator:
                    try:
                        giri = self.metrics_calculator.calculate_giri(
                            int(event.get('team_id', 0)),
                            float(event.get('timestamp')),
                            tracking_frames,
                            phases_df,
                            self.time_window_seconds
                        )
                        event_result['GIRI'] = giri
                        if giri is None:
                            print(f"    GIRI no calculado para evento {event.get('event_id')}")
                    except Exception as e:
                        print(f"    Error calculando GIRI para evento {event.get('event_id')}: {e}")
                        event_result['GIRI'] = None
            
            results.append(event_result)
        
        return results
    
    def _enrich_with_names(self, results_df: pd.DataFrame, all_matches_data: Dict) -> pd.DataFrame:
        """Enriquece el DataFrame con nombres de partidos, equipos y jugadores"""
        if results_df.empty:
            return results_df
        
        # Crear diccionarios de mapeo
        match_names = {}
        team_names = {}
        player_names = {}
        
        # Procesar cada partido para extraer nombres
        for match_id, match_data in all_matches_data.items():
            match_json = match_data.get('match_json', {})
            
            # Nombre del partido
            home_team = match_json.get('home_team', {})
            away_team = match_json.get('away_team', {})
            home_name = home_team.get('name', f"Team {home_team.get('id', 'Unknown')}")
            away_name = away_team.get('name', f"Team {away_team.get('id', 'Unknown')}")
            match_names[str(match_id)] = f"{home_name} vs {away_name}"
            
            # Nombres de equipos
            home_team_id = home_team.get('id')
            away_team_id = away_team.get('id')
            if home_team_id:
                team_names[home_team_id] = home_name
            if away_team_id:
                team_names[away_team_id] = away_name
            
            # Nombres de jugadores (desde lineups)
            lineups = match_json.get('lineups', [])
            for lineup in lineups:
                players = lineup.get('players', [])
                for player in players:
                    player_id = player.get('player_id')
                    player_name = player.get('player_name', f"Player {player_id}")
                    if player_id:
                        player_names[player_id] = player_name
        
        # Agregar columnas de nombres
        results_df['match_name'] = results_df['match_id'].astype(str).map(match_names).fillna(results_df['match_id'])
        results_df['team_name'] = results_df['team_id'].map(team_names).fillna(results_df['team_id'].astype(str))
        
        # Si player_name ya existe, usarlo; si no, mapear desde player_id
        if 'player_name' not in results_df.columns:
            results_df['player_name'] = None
        results_df['player_name'] = results_df['player_name'].fillna(
            results_df['player_id'].map(player_names).fillna(results_df['player_id'].astype(str))
        )
        
        return results_df
    
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

