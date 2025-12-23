"""
Baseline Calculator
Calcula el estado base (promedio) de jugadores y equipos sobre TODOS los partidos
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from collections import defaultdict


class BaselineCalculator:
    """Calcula estado base individual y colectivo sobre todos los partidos"""
    
    def __init__(self):
        self.player_baselines = {}  # {player_id: {metric: value}}
        self.team_baselines = {}     # {team_id: {metric: value}}
    
    def calculate_baselines(self, all_matches_data: Dict, 
                           tracking_data_dict: Dict[str, List]) -> Dict:
        """
        Calcula estado base sobre todos los partidos
        
        Args:
            all_matches_data: Diccionario con datos de todos los partidos
            tracking_data_dict: {match_id: [frames]} - datos de tracking
            
        Returns:
            Diccionario con baselines calculados
        """
        print("Calculando estado base sobre todos los partidos...")
        
        # Acumuladores para promedios
        player_metrics = defaultdict(lambda: defaultdict(list))
        team_metrics = defaultdict(lambda: defaultdict(list))
        
        # Procesar cada partido
        for match_id, match_data in all_matches_data.items():
            match_json = match_data['match_json']
            tracking_frames = tracking_data_dict.get(match_id, [])
            
            if not tracking_frames:
                continue
            
            # Obtener IDs de equipos
            home_team_id = match_json.get('home_team', {}).get('id')
            away_team_id = match_json.get('away_team', {}).get('id')
            
            # Procesar frames de tracking
            for frame in tracking_frames:
                period = frame.get('period', 1)
                timestamp = frame.get('timestamp', 0)
                
                # Procesar jugadores individuales
                player_data_list = frame.get('player_data', [])
                for player in player_data_list:
                    player_id = player.get('player_id')
                    if not player_id:
                        continue
                    
                    x = player.get('x', 0)
                    y = player.get('y', 0)
                    
                    # Calcular distancia al centro
                    dist_to_center = np.sqrt(x**2 + y**2)
                    
                    # Acumular métricas individuales
                    player_metrics[player_id]['x'].append(x)
                    player_metrics[player_id]['y'].append(y)
                    player_metrics[player_id]['dist_to_center'].append(dist_to_center)
                
                # Procesar equipo (necesitamos calcular velocidad y distancia)
                # Esto se hará en una segunda pasada con cálculo de velocidades
                
                # Acumular posesión por equipo
                possession = frame.get('possession', {})
                group = possession.get('group', '')
                if group == 'home' and home_team_id:
                    team_metrics[home_team_id]['possession_frames'].append(1)
                elif group == 'away' and away_team_id:
                    team_metrics[away_team_id]['possession_frames'].append(1)
        
        # Calcular promedios individuales
        for player_id, metrics in player_metrics.items():
            self.player_baselines[player_id] = {
                'x_mean': np.mean(metrics['x']) if metrics['x'] else 0,
                'y_mean': np.mean(metrics['y']) if metrics['y'] else 0,
                'dist_to_center_mean': np.mean(metrics['dist_to_center']) if metrics['dist_to_center'] else 0,
            }
        
        # Calcular promedios colectivos
        for team_id, metrics in team_metrics.items():
            total_frames = len(metrics.get('possession_frames', []))
            self.team_baselines[team_id] = {
                'possession_rate': total_frames,  # Se normalizará después
            }
        
        print(f"Estado base calculado para {len(self.player_baselines)} jugadores")
        print(f"Estado base calculado para {len(self.team_baselines)} equipos")
        
        return {
            'player_baselines': self.player_baselines,
            'team_baselines': self.team_baselines
        }
    
    def calculate_velocity_baselines(self, all_matches_data: Dict,
                                   tracking_data_dict: Dict[str, List]) -> Dict:
        """
        Calcula baselines de velocidad y aceleración (requiere procesamiento temporal)
        """
        print("Calculando baselines de velocidad y aceleración...")
        
        player_velocities = defaultdict(list)
        player_distances = defaultdict(list)
        
        for match_id, match_data in all_matches_data.items():
            tracking_frames = tracking_data_dict.get(match_id, [])
            if len(tracking_frames) < 2:
                continue
            
            # Ordenar frames por timestamp
            sorted_frames = sorted(tracking_frames, key=lambda f: (
                f.get('period', 1), f.get('timestamp', 0)
            ))
            
            # Calcular velocidades
            for i in range(1, len(sorted_frames)):
                prev_frame = sorted_frames[i-1]
                curr_frame = sorted_frames[i]
                
                # Verificar que sean del mismo periodo
                if prev_frame.get('period') != curr_frame.get('period'):
                    continue
                
                dt = curr_frame.get('timestamp', 0) - prev_frame.get('timestamp', 0)
                if dt <= 0:
                    continue
                
                # Procesar jugadores
                prev_players = {p.get('player_id'): p for p in prev_frame.get('player_data', [])}
                curr_players = {p.get('player_id'): p for p in curr_frame.get('player_data', [])}
                
                for player_id, curr_player in curr_players.items():
                    if player_id not in prev_players:
                        continue
                    
                    prev_player = prev_players[player_id]
                    
                    # Calcular distancia recorrida
                    dx = curr_player.get('x', 0) - prev_player.get('x', 0)
                    dy = curr_player.get('y', 0) - prev_player.get('y', 0)
                    distance = np.sqrt(dx**2 + dy**2)
                    
                    # Calcular velocidad (m/s)
                    velocity = distance / dt if dt > 0 else 0
                    
                    player_velocities[player_id].append(velocity)
                    player_distances[player_id].append(distance)
        
        # Actualizar baselines con velocidades
        for player_id, velocities in player_velocities.items():
            if player_id not in self.player_baselines:
                self.player_baselines[player_id] = {}
            
            self.player_baselines[player_id].update({
                'velocity_mean': np.mean(velocities) if velocities else 0,
                'velocity_std': np.std(velocities) if velocities else 0,
                'distance_per_frame_mean': np.mean(player_distances[player_id]) if player_distances[player_id] else 0,
            })
        
        return {
            'player_baselines': self.player_baselines,
            'team_baselines': self.team_baselines
        }
    
    def get_player_baseline(self, player_id: int) -> Dict:
        """Obtiene baseline de un jugador"""
        return self.player_baselines.get(player_id, {})
    
    def get_team_baseline(self, team_id: int) -> Dict:
        """Obtiene baseline de un equipo"""
        return self.team_baselines.get(team_id, {})

