"""
Metrics Calculator
Calcula las 3 métricas R3ACT: CRT, TSI, GIRI
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy.spatial.distance import mahalanobis
from scipy.spatial import ConvexHull
from collections import defaultdict


class MetricsCalculator:
    """Calcula métricas R3ACT: CRT, TSI, GIRI"""
    
    def __init__(self, baseline_calculator):
        """
        Args:
            baseline_calculator: Instancia de BaselineCalculator
        """
        self.baseline = baseline_calculator
    
    def calculate_crt(self, player_id: int, error_timestamp: float, 
                     error_frame: int, tracking_frames: List[Dict],
                     window_seconds: float = 120) -> Optional[float]:
        """
        Calcula Cognitive Reset Time (CRT)
        
        Args:
            player_id: ID del jugador que cometió el error
            error_timestamp: Timestamp del error (segundos)
            error_frame: Frame del error
            tracking_frames: Lista de frames de tracking
            window_seconds: Ventana temporal en segundos (default 120 = 2 min)
            
        Returns:
            CRT en segundos, o None si no se puede calcular
        """
        # Encontrar frame del error en tracking_frames
        error_frame_data = None
        error_frame_idx = None
        for idx, frame in enumerate(tracking_frames):
            if (frame.get('frame') == error_frame or 
                abs(frame.get('timestamp', 0) - error_timestamp) < 0.5):
                error_frame_data = frame
                error_frame_idx = idx
                break
        
        if error_frame_data is None:
            return None
        
        error_period = error_frame_data.get('period', 1)
        
        # Filtrar frames en la ventana post-error
        post_error_frames = []
        for idx, frame in enumerate(tracking_frames):
            frame_period = frame.get('period', 1)
            frame_timestamp = frame.get('timestamp', 0)
            
            # Solo frames del mismo periodo y después del error
            if (frame_period == error_period and
                frame_timestamp >= error_timestamp and
                frame_timestamp <= error_timestamp + window_seconds):
                post_error_frames.append((idx, frame))
        
        if len(post_error_frames) < 10:  # Mínimo de frames para calcular
            return None
        
        # Obtener baseline del jugador
        baseline = self.baseline.get_player_baseline(player_id)
        if not baseline:
            return None
        
        # Calcular métricas del jugador en cada frame post-error
        player_metrics = []
        for frame_idx, frame in post_error_frames:
            player_data_list = frame.get('player_data', [])
            player = next((p for p in player_data_list if p.get('player_id') == player_id), None)
            if not player:
                continue
            
            x = player.get('x', 0)
            y = player.get('y', 0)
            dist_to_center = np.sqrt(x**2 + y**2)
            
            # Calcular velocidad (necesitamos frame anterior)
            velocity = 0
            if len(player_metrics) > 0:
                prev_metrics = player_metrics[-1]
                dt = frame.get('timestamp', 0) - prev_metrics['timestamp']
                if dt > 0:
                    dx = x - prev_metrics['x']
                    dy = y - prev_metrics['y']
                    velocity = np.sqrt(dx**2 + dy**2) / dt
            elif frame_idx > 0 and frame_idx < len(tracking_frames):
                # Buscar frame anterior en tracking_frames completo
                prev_frame = tracking_frames[frame_idx - 1]
                prev_player = next((p for p in prev_frame.get('player_data', []) 
                                  if p.get('player_id') == player_id), None)
                if prev_player:
                    dt = frame.get('timestamp', 0) - prev_frame.get('timestamp', 0)
                    if dt > 0:
                        dx = x - prev_player.get('x', 0)
                        dy = y - prev_player.get('y', 0)
                        velocity = np.sqrt(dx**2 + dy**2) / dt
            
            player_metrics.append({
                'timestamp': frame.get('timestamp', 0),
                'x': x,
                'y': y,
                'dist_to_center': dist_to_center,
                'velocity': velocity
            })
        
        if len(player_metrics) < 5:
            return None
        
        # Calcular distancia de Mahalanobis para cada frame
        # Usar métricas: x, y, dist_to_center, velocity
        baseline_vector = np.array([
            baseline.get('x_mean', 0),
            baseline.get('y_mean', 0),
            baseline.get('dist_to_center_mean', 0),
            baseline.get('velocity_mean', 0)
        ])
        
        # Calcular matriz de covarianza de los datos post-error
        metrics_array = np.array([
            [m['x'], m['y'], m['dist_to_center'], m['velocity']]
            for m in player_metrics
        ])
        
        if metrics_array.shape[0] < 2:
            return None
        
        cov_matrix = np.cov(metrics_array.T)
        # Añadir pequeña constante para evitar singularidad
        cov_matrix += np.eye(cov_matrix.shape[0]) * 0.01
        
        try:
            inv_cov = np.linalg.inv(cov_matrix)
        except:
            return None
        
        # Calcular distancias de Mahalanobis
        mahalanobis_distances = []
        for metrics in player_metrics:
            current_vector = np.array([
                metrics['x'],
                metrics['y'],
                metrics['dist_to_center'],
                metrics['velocity']
            ])
            
            try:
                dist = mahalanobis(current_vector, baseline_vector, inv_cov)
                mahalanobis_distances.append(dist)
            except:
                continue
        
        if len(mahalanobis_distances) < 5:
            return None
        
        # Aplicar EWMA (Exponentially Weighted Moving Average)
        alpha = 0.3  # Factor de suavizado
        ewma_values = [mahalanobis_distances[0]]
        for dist in mahalanobis_distances[1:]:
            ewma_values.append(alpha * dist + (1 - alpha) * ewma_values[-1])
        
        # Encontrar momento de recuperación (distancia < umbral)
        threshold = 1.0  # Umbral de Mahalanobis para considerar "recuperado"
        recovery_time = None
        
        for i, ewma in enumerate(ewma_values):
            if ewma < threshold:
                recovery_time = player_metrics[i]['timestamp'] - error_timestamp
                break
        
        # Si no se recupera en la ventana, retornar tiempo máximo
        if recovery_time is None:
            recovery_time = window_seconds
        
        return recovery_time
    
    def calculate_tsi(self, player_id: int, team_id: int, error_timestamp: float,
                     error_frame: int, tracking_frames: List[Dict],
                     phases_df: pd.DataFrame, window_seconds: float = 120) -> Optional[float]:
        """
        Calcula Team Support Index (TSI)
        
        Args:
            player_id: ID del jugador que cometió el error
            team_id: ID del equipo del jugador
            error_timestamp: Timestamp del error
            error_frame: Frame del error
            tracking_frames: Lista de frames de tracking
            phases_df: DataFrame con phases_of_play
            window_seconds: Ventana temporal en segundos
            
        Returns:
            TSI (valor entre -1 y 1, positivo = más apoyo)
        """
        # Componente 1: Proximidad física
        proximity_score = self._calculate_proximity_component(
            player_id, team_id, error_timestamp, error_frame,
            tracking_frames, window_seconds
        )
        
        # Componente 2: Frecuencia de posesión
        possession_score = self._calculate_possession_component(
            team_id, error_timestamp, error_frame,
            tracking_frames, window_seconds
        )
        
        # Componente 3: Estructura defensiva
        structure_score = self._calculate_structure_component(
            team_id, error_timestamp, phases_df, window_seconds
        )
        
        # Combinar componentes con pesos
        weights = {'proximity': 0.4, 'possession': 0.3, 'structure': 0.3}
        tsi = (proximity_score * weights['proximity'] +
               possession_score * weights['possession'] +
               structure_score * weights['structure'])
        
        return tsi
    
    def _calculate_proximity_component(self, player_id: int, team_id: int,
                                      error_timestamp: float, error_frame: int,
                                      tracking_frames: List[Dict],
                                      window_seconds: float) -> float:
        """Calcula componente de proximidad física"""
        # Extraer ventanas pre y post
        pre_frames = []
        post_frames = []
        
        error_period = tracking_frames[error_frame].get('period', 1)
        
        for frame in tracking_frames:
            frame_period = frame.get('period', 1)
            frame_timestamp = frame.get('timestamp', 0)
            
            if frame_period != error_period:
                continue
            
            if error_timestamp - window_seconds <= frame_timestamp < error_timestamp:
                pre_frames.append(frame)
            elif error_timestamp <= frame_timestamp <= error_timestamp + window_seconds:
                post_frames.append(frame)
        
        if len(pre_frames) < 5 or len(post_frames) < 5:
            return 0.0
        
        # Calcular distancia promedio del equipo al jugador
        def avg_team_distance(frames, is_pre=True):
            distances = []
            for frame in frames:
                player_data_list = frame.get('player_data', [])
                error_player = next((p for p in player_data_list 
                                   if p.get('player_id') == player_id), None)
                if not error_player:
                    continue
                
                error_x = error_player.get('x', 0)
                error_y = error_player.get('y', 0)
                
                # Calcular distancia a todos los demás jugadores (compañeros y oponentes)
                for player in player_data_list:
                    if player.get('player_id') == player_id:
                        continue
                    
                    px = player.get('x', 0)
                    py = player.get('y', 0)
                    dist = np.sqrt((px - error_x)**2 + (py - error_y)**2)
                    distances.append(dist)
            
            return np.mean(distances) if distances else 100.0  # Default grande
        
        pre_avg_dist = avg_team_distance(pre_frames, is_pre=True)
        post_avg_dist = avg_team_distance(post_frames, is_pre=False)
        
        # TSI_proximity = (pre - post) / pre (positivo = más cerca = más apoyo)
        if pre_avg_dist > 0:
            proximity_score = (pre_avg_dist - post_avg_dist) / pre_avg_dist
        else:
            proximity_score = 0.0
        
        return proximity_score
    
    def _calculate_possession_component(self, team_id: int,
                                       error_timestamp: float, error_frame: int,
                                       tracking_frames: List[Dict],
                                       window_seconds: float) -> float:
        """Calcula componente de frecuencia de posesión"""
        # Determinar si el equipo es home o away
        error_frame_data = tracking_frames[error_frame]
        possession = error_frame_data.get('possession', {})
        group = possession.get('group', '')
        is_home = (group == 'home')
        
        # Extraer ventanas
        pre_frames = []
        post_frames = []
        error_period = error_frame_data.get('period', 1)
        
        for frame in tracking_frames:
            frame_period = frame.get('period', 1)
            frame_timestamp = frame.get('timestamp', 0)
            
            if frame_period != error_period:
                continue
            
            if error_timestamp - window_seconds <= frame_timestamp < error_timestamp:
                pre_frames.append(frame)
            elif error_timestamp <= frame_timestamp <= error_timestamp + window_seconds:
                post_frames.append(frame)
        
        if len(pre_frames) < 5 or len(post_frames) < 5:
            return 0.0
        
        # Calcular % de posesión
        def possession_rate(frames, is_home_team):
            possession_count = 0
            for frame in frames:
                pos = frame.get('possession', {})
                if pos.get('group') == ('home' if is_home_team else 'away'):
                    possession_count += 1
            return possession_count / len(frames) if frames else 0.0
        
        pre_possession = possession_rate(pre_frames, is_home)
        post_possession = possession_rate(post_frames, is_home)
        
        # TSI_possession = (post - pre) / pre (positivo = más posesión = mejor)
        if pre_possession > 0:
            possession_score = (post_possession - pre_possession) / pre_possession
        else:
            possession_score = 0.0
        
        return possession_score
    
    def _calculate_structure_component(self, team_id: int,
                                      error_timestamp: float,
                                      phases_df: pd.DataFrame,
                                      window_seconds: float) -> float:
        """Calcula componente de estructura defensiva (solo cuando defiende)"""
        # Convertir timestamp a formato de phases
        error_minutes = int(error_timestamp // 60)
        error_seconds = error_timestamp % 60
        
        # Filtrar fases en ventana pre y post
        pre_phases = []
        post_phases = []
        
        for _, phase in phases_df.iterrows():
            phase_team_id = phase.get('team_in_possession_id')
            if phase_team_id != team_id:  # Solo cuando el equipo NO tiene posesión (defiende)
                continue
            
            phase_start = self._parse_phase_time(phase.get('time_start', '00:00.0'))
            phase_end = self._parse_phase_time(phase.get('time_end', '00:00.0'))
            
            # Verificar si la fase está en ventana pre o post
            if error_timestamp - window_seconds <= phase_start < error_timestamp:
                pre_phases.append(phase)
            elif error_timestamp <= phase_start <= error_timestamp + window_seconds:
                post_phases.append(phase)
        
        if len(pre_phases) < 1 or len(post_phases) < 1:
            return 0.0
        
        # Calcular compactness (width * length, menor = más compacto)
        def avg_compactness(phases):
            compactness_values = []
            for phase in phases:
                width = phase.get('team_out_of_possession_width_start', 0)
                length = phase.get('team_out_of_possession_length_start', 0)
                if width > 0 and length > 0:
                    compactness_values.append(width * length)
            return np.mean(compactness_values) if compactness_values else 1000.0
        
        pre_compactness = avg_compactness(pre_phases)
        post_compactness = avg_compactness(post_phases)
        
        # TSI_structure = (pre - post) / pre (positivo = más compacto = mejor)
        if pre_compactness > 0:
            structure_score = (pre_compactness - post_compactness) / pre_compactness
        else:
            structure_score = 0.0
        
        return structure_score
    
    def calculate_giri(self, team_id: int, goal_timestamp: float,
                      tracking_frames: List[Dict], phases_df: pd.DataFrame,
                      window_seconds: float = 300) -> Optional[float]:
        """
        Calcula Goal Impact Response Index (GIRI)
        
        Args:
            team_id: ID del equipo
            goal_timestamp: Timestamp del gol
            tracking_frames: Lista de frames de tracking
            phases_df: DataFrame con phases_of_play
            window_seconds: Ventana temporal (default 300 = 5 min)
            
        Returns:
            GIRI (valor normalizado)
        """
        # Extraer ventanas pre y post gol
        pre_frames = []
        post_frames = []
        
        for frame in tracking_frames:
            frame_timestamp = frame.get('timestamp', 0)
            frame_period = frame.get('period', 1)
            
            if goal_timestamp - window_seconds <= frame_timestamp < goal_timestamp:
                pre_frames.append(frame)
            elif goal_timestamp <= frame_timestamp <= goal_timestamp + window_seconds:
                post_frames.append(frame)
        
        if len(pre_frames) < 10 or len(post_frames) < 10:
            return None
        
        # Métricas tácticas a calcular:
        # 1. Altura del bloque (posición Y promedio)
        # 2. Velocidad media del equipo
        # 3. Compactness
        
        pre_metrics = self._calculate_tactical_metrics(pre_frames, team_id, phases_df, goal_timestamp - window_seconds)
        post_metrics = self._calculate_tactical_metrics(post_frames, team_id, phases_df, goal_timestamp)
        
        if not pre_metrics or not post_metrics:
            return None
        
        # Calcular cambios normalizados
        changes = {}
        for metric in ['block_height', 'avg_velocity', 'compactness']:
            pre_val = pre_metrics.get(metric, 0)
            post_val = post_metrics.get(metric, 0)
            if pre_val != 0:
                changes[metric] = (post_val - pre_val) / abs(pre_val)
            else:
                changes[metric] = 0.0
        
        # GIRI = promedio de cambios (positivo = respuesta proactiva)
        giri = np.mean(list(changes.values()))
        
        return giri
    
    def _calculate_tactical_metrics(self, frames: List[Dict], team_id: int,
                                   phases_df: pd.DataFrame, start_timestamp: float) -> Dict:
        """Calcula métricas tácticas para un conjunto de frames"""
        if not frames:
            return None
        
        # Determinar si es home o away
        first_frame = frames[0]
        possession = first_frame.get('possession', {})
        group = possession.get('group', '')
        is_home = (group == 'home')
        
        # 1. Altura del bloque (posición Y promedio del equipo)
        y_positions = []
        velocities = []
        
        for frame in frames:
            player_data_list = frame.get('player_data', [])
            frame_possession = frame.get('possession', {})
            
            # Solo jugadores del equipo
            if frame_possession.get('group') == ('home' if is_home else 'away'):
                for player in player_data_list:
                    y = player.get('y', 0)
                    y_positions.append(y)
                    
                    # Calcular velocidad (simplificado)
                    # En implementación completa, calcularíamos velocidad real
        
        block_height = np.mean(y_positions) if y_positions else 0
        
        # 2. Compactness desde phases_of_play
        compactness_values = []
        for _, phase in phases_df.iterrows():
            phase_team_id = phase.get('team_in_possession_id')
            if phase_team_id == team_id:
                phase_start = self._parse_phase_time(phase.get('time_start', '00:00.0'))
                if abs(phase_start - start_timestamp) < 60:  # Dentro de 1 minuto
                    width = phase.get('team_in_possession_width_start', 0)
                    length = phase.get('team_in_possession_length_start', 0)
                    if width > 0 and length > 0:
                        compactness_values.append(width * length)
        
        compactness = np.mean(compactness_values) if compactness_values else 1000.0
        
        return {
            'block_height': block_height,
            'avg_velocity': 0,  # Placeholder - calcular en implementación completa
            'compactness': compactness
        }
    
    def _parse_phase_time(self, time_str: str) -> float:
        """Convierte tiempo de phase a segundos"""
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            return float(time_str)
        except:
            return 0.0

