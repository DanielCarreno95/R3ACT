"""
Event Detector for Critical Events
Detecta eventos críticos desde dynamic_events.csv de forma parametrizable
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import timedelta
import numpy as np


class CriticalEventDetector:
    """Detector de eventos críticos parametrizable"""
    
    def __init__(self, event_weights: Optional[Dict[str, float]] = None):
        """
        Inicializa el detector con pesos de eventos
        
        Args:
            event_weights: Diccionario con pesos para cada tipo de evento
        """
        # Pesos por defecto (se normalizan automáticamente)
        self.default_weights = {
            "possession_loss_defensive_third": 1.0,
            "possession_loss_middle_third": 0.7,
            "possession_loss_attacking_third": 0.5,
            "possession_loss_penalty_area": 1.5,
            "failed_pass_dangerous": 1.2,
            "failed_pass_lead_to_shot": 1.5,
            "failed_pass_offside": 0.8,
            "goal_conceded": 2.0,
            "goal_scored": 2.0,  # Para GIRI
            "defensive_error_lead_to_shot": 1.3,
            "interception_conceded_dangerous": 0.8,
            "interception_conceded_defensive_third": 1.0,
        }
        
        self.event_weights = event_weights if event_weights else self.default_weights
        self._normalize_weights()
    
    def _normalize_weights(self):
        """Normaliza los pesos para que sumen 1.0"""
        total = sum(self.event_weights.values())
        if total > 0:
            self.event_weights = {k: v/total for k, v in self.event_weights.items()}
    
    def detect_critical_events(self, events_df: pd.DataFrame, match_id: str, 
                               match_json: Dict) -> pd.DataFrame:
        """
        Detecta todos los eventos críticos en un partido
        
        Args:
            events_df: DataFrame con dynamic_events
            match_id: ID del partido
            match_json: Información del partido
            
        Returns:
            DataFrame con eventos críticos detectados
        """
        critical_events = []
        
        # Obtener IDs de equipos
        home_team_id = match_json.get('home_team', {}).get('id')
        away_team_id = match_json.get('away_team', {}).get('id')
        
        # 1. Pérdidas de posesión
        possession_losses = self._detect_possession_losses(
            events_df, home_team_id, away_team_id
        )
        critical_events.extend(possession_losses)
        
        # 2. Pases fallidos
        failed_passes = self._detect_failed_passes(
            events_df, home_team_id, away_team_id
        )
        critical_events.extend(failed_passes)
        
        # 3. Goles
        goals = self._detect_goals(
            events_df, home_team_id, away_team_id
        )
        critical_events.extend(goals)
        
        # 4. Errores defensivos
        defensive_errors = self._detect_defensive_errors(
            events_df, home_team_id, away_team_id
        )
        critical_events.extend(defensive_errors)
        
        # 5. Intercepciones concedidas
        interceptions = self._detect_interceptions_conceded(
            events_df, home_team_id, away_team_id
        )
        critical_events.extend(interceptions)
        
        if not critical_events:
            return pd.DataFrame()
        
        # Convertir a DataFrame
        df_critical = pd.DataFrame(critical_events)
        
        # Agregar peso según tipo de evento
        df_critical['event_weight'] = df_critical['event_type'].map(
            self.event_weights
        ).fillna(0.5)  # Peso por defecto si no está en la configuración
        
        # Ordenar por timestamp
        df_critical = df_critical.sort_values('timestamp').reset_index(drop=True)
        
        return df_critical
    
    def _detect_possession_losses(self, events_df: pd.DataFrame, 
                                  home_team_id: int, away_team_id: int) -> List[Dict]:
        """Detecta pérdidas de posesión"""
        critical_events = []
        
        # Filtrar eventos de pérdida de posesión
        losses = events_df[
            (events_df['end_type'] == 'possession_loss') |
            (events_df['associated_player_possession_end_type'] == 'possession_loss')
        ].copy()
        
        for _, row in losses.iterrows():
            # Determinar equipo que perdió
            team_id = row.get('team_id')
            is_home = team_id == home_team_id
            
            # Determinar zona del campo
            third = row.get('third_start', 'unknown')
            penalty_area = row.get('penalty_area_start', False)
            
            # Clasificar tipo de pérdida
            if penalty_area:
                event_type = "possession_loss_penalty_area"
            elif third == 'defensive_third':
                event_type = "possession_loss_defensive_third"
            elif third == 'middle_third':
                event_type = "possession_loss_middle_third"
            else:
                event_type = "possession_loss_attacking_third"
            
            critical_events.append({
                'match_id': row.get('match_id'),
                'event_id': row.get('event_id'),
                'timestamp': self._parse_time(row.get('time_start', '00:00.0')),
                'frame': row.get('frame_start'),
                'period': row.get('period'),
                'player_id': row.get('player_id'),
                'player_name': row.get('player_name'),
                'team_id': team_id,
                'is_home': is_home,
                'event_type': event_type,
                'x': row.get('x_start'),
                'y': row.get('y_start'),
                'third': third,
                'penalty_area': penalty_area,
            })
        
        return critical_events
    
    def _detect_failed_passes(self, events_df: pd.DataFrame,
                             home_team_id: int, away_team_id: int) -> List[Dict]:
        """Detecta pases fallidos"""
        critical_events = []
        
        # Filtrar pases fallidos
        failed = events_df[
            (events_df['pass_outcome'] == 'unsuccessful') |
            (events_df['pass_outcome'] == 'offside')
        ].copy()
        
        for _, row in failed.iterrows():
            team_id = row.get('team_id')
            is_home = team_id == home_team_id
            
            # Clasificar tipo de pase fallido
            if row.get('pass_outcome') == 'offside':
                event_type = "failed_pass_offside"
            elif row.get('dangerous', False):
                event_type = "failed_pass_dangerous"
            elif row.get('lead_to_shot', False):
                event_type = "failed_pass_lead_to_shot"
            else:
                event_type = "failed_pass"
            
            critical_events.append({
                'match_id': row.get('match_id'),
                'event_id': row.get('event_id'),
                'timestamp': self._parse_time(row.get('time_start', '00:00.0')),
                'frame': row.get('frame_start'),
                'period': row.get('period'),
                'player_id': row.get('player_id'),
                'player_name': row.get('player_name'),
                'team_id': team_id,
                'is_home': is_home,
                'event_type': event_type,
                'x': row.get('x_start'),
                'y': row.get('y_start'),
                'third': row.get('third_start'),
            })
        
        return critical_events
    
    def _detect_goals(self, events_df: pd.DataFrame,
                      home_team_id: int, away_team_id: int) -> List[Dict]:
        """Detecta goles (para GIRI)"""
        critical_events = []
        
        # Buscar goles en game_interruption_after
        goals_after = events_df[
            (events_df['game_interruption_after'] == 'goal_for') |
            (events_df['game_interruption_after'] == 'goal_against')
        ].copy()
        
        # También buscar en lead_to_goal
        goals_lead = events_df[events_df['lead_to_goal'] == True].copy()
        
        # Combinar y eliminar duplicados
        all_goals = pd.concat([goals_after, goals_lead]).drop_duplicates(
            subset=['event_id']
        )
        
        for _, row in all_goals.iterrows():
            team_id = row.get('team_id')
            is_home = team_id == home_team_id
            
            # Determinar si es gol a favor o en contra
            if row.get('game_interruption_after') == 'goal_for':
                event_type = "goal_scored"
            elif row.get('game_interruption_after') == 'goal_against':
                event_type = "goal_conceded"
            elif row.get('lead_to_goal'):
                # Si lead_to_goal es True, es gol a favor del equipo que hizo la acción
                event_type = "goal_scored"
            else:
                continue
            
            critical_events.append({
                'match_id': row.get('match_id'),
                'event_id': row.get('event_id'),
                'timestamp': self._parse_time(row.get('time_start', '00:00.0')),
                'frame': row.get('frame_start'),
                'period': row.get('period'),
                'player_id': row.get('player_id'),
                'player_name': row.get('player_name'),
                'team_id': team_id,
                'is_home': is_home,
                'event_type': event_type,
                'x': row.get('x_start'),
                'y': row.get('y_start'),
            })
        
        return critical_events
    
    def _detect_defensive_errors(self, events_df: pd.DataFrame,
                                home_team_id: int, away_team_id: int) -> List[Dict]:
        """Detecta errores defensivos (clearance seguido de pérdida o tiro)"""
        critical_events = []
        
        # Buscar clearances
        clearances = events_df[events_df['end_type'] == 'clearance'].copy()
        
        for _, row in clearances.iterrows():
            team_id = row.get('team_id')
            is_home = team_id == home_team_id
            
            # Verificar si el clearance llevó a tiro o pérdida peligrosa
            if row.get('lead_to_shot', False):
                event_type = "defensive_error_lead_to_shot"
            else:
                continue  # Solo considerar clearances que llevan a tiro
            
            critical_events.append({
                'match_id': row.get('match_id'),
                'event_id': row.get('event_id'),
                'timestamp': self._parse_time(row.get('time_start', '00:00.0')),
                'frame': row.get('frame_start'),
                'period': row.get('period'),
                'player_id': row.get('player_id'),
                'player_name': row.get('player_name'),
                'team_id': team_id,
                'is_home': is_home,
                'event_type': event_type,
                'x': row.get('x_start'),
                'y': row.get('y_start'),
            })
        
        return critical_events
    
    def _detect_interceptions_conceded(self, events_df: pd.DataFrame,
                                      home_team_id: int, away_team_id: int) -> List[Dict]:
        """Detecta intercepciones concedidas"""
        critical_events = []
        
        # Buscar intercepciones (cuando el oponente intercepta)
        interceptions = events_df[
            events_df['start_type'] == 'pass_interception'
        ].copy()
        
        for _, row in interceptions.iterrows():
            team_id = row.get('team_id')
            is_home = team_id == home_team_id
            
            # Clasificar por zona
            third = row.get('third_start', 'unknown')
            dangerous = row.get('dangerous', False)
            
            if dangerous:
                event_type = "interception_conceded_dangerous"
            elif third == 'defensive_third':
                event_type = "interception_conceded_defensive_third"
            else:
                event_type = "interception_conceded"
            
            critical_events.append({
                'match_id': row.get('match_id'),
                'event_id': row.get('event_id'),
                'timestamp': self._parse_time(row.get('time_start', '00:00.0')),
                'frame': row.get('frame_start'),
                'period': row.get('period'),
                'player_id': row.get('player_id'),
                'player_name': row.get('player_name'),
                'team_id': team_id,
                'is_home': is_home,
                'event_type': event_type,
                'x': row.get('x_start'),
                'y': row.get('y_start'),
                'third': third,
            })
        
        return critical_events
    
    def _parse_time(self, time_str: str) -> float:
        """
        Convierte string de tiempo (MM:SS.s) a segundos totales
        
        Args:
            time_str: String en formato "MM:SS.s" o "MM:SS"
            
        Returns:
            Segundos totales como float
        """
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except:
            return 0.0

