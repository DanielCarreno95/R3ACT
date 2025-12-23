"""
Script de exploración de datos de SkillCorner
Analiza la estructura de todos los archivos disponibles para identificar
eventos críticos y métricas disponibles.
"""

import json
import pandas as pd
import requests
from typing import Dict, List, Any
from pathlib import Path
import io


class SkillCornerDataExplorer:
    """Explorador de datos de SkillCorner Open Data"""
    
    BASE_URL = "https://raw.githubusercontent.com/SkillCorner/opendata/master/data"
    
    def __init__(self):
        self.matches_info = None
        self.sample_match_id = None
        
    def load_matches_info(self) -> Dict:
        """Carga información de todos los partidos disponibles"""
        url = f"{self.BASE_URL}/matches.json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.matches_info = response.json()
            print(f"[OK] Cargados {len(self.matches_info)} partidos")
            if self.matches_info:
                self.sample_match_id = self.matches_info[0].get('id')
                print(f"[OK] ID de partido de ejemplo: {self.sample_match_id}")
            return self.matches_info
        except Exception as e:
            print(f"[ERROR] Error cargando matches.json: {e}")
            return None
    
    def explore_match_json(self, match_id: str = None) -> Dict:
        """Explora estructura de match.json"""
        if not match_id:
            match_id = self.sample_match_id
        if not match_id:
            return None
            
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_match.json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            print(f"\n{'='*60}")
            print(f"MATCH.JSON - Partido {match_id}")
            print(f"{'='*60}")
            print(f"Claves principales: {list(data.keys())}")
            
            # Información clave
            if 'home_team' in data:
                print(f"\nEquipo local: {data.get('home_team', {}).get('name', 'N/A')}")
            if 'away_team' in data:
                print(f"Equipo visitante: {data.get('away_team', {}).get('name', 'N/A')}")
            if 'pitch_size' in data:
                print(f"Tamaño del campo: {data.get('pitch_size', {})}")
            if 'lineup' in data:
                print(f"Jugadores en alineación: {len(data.get('lineup', []))}")
            
            return data
        except Exception as e:
            print(f"[ERROR] Error cargando match.json: {e}")
            return None
    
    def explore_dynamic_events(self, match_id: str = None) -> pd.DataFrame:
        """Explora estructura de dynamic_events.csv"""
        if not match_id:
            match_id = self.sample_match_id
        if not match_id:
            return None
            
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_dynamic_events.csv"
        try:
            response = requests.get(url)
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.text))
            
            print(f"\n{'='*60}")
            print(f"DYNAMIC_EVENTS.CSV - Partido {match_id}")
            print(f"{'='*60}")
            print(f"Shape: {df.shape}")
            print(f"\nColumnas disponibles:")
            for col in df.columns:
                print(f"  - {col}")
            
            print(f"\nTipos de datos:")
            print(df.dtypes)
            
            print(f"\nPrimeras 5 filas:")
            print(df.head())
            
            print(f"\nValores únicos en columnas clave:")
            for col in df.columns:
                if df[col].dtype == 'object' or df[col].nunique() < 20:
                    unique_vals = df[col].unique()[:10]
                    print(f"  {col}: {unique_vals}")
                    if df[col].nunique() > 10:
                        print(f"    ... y {df[col].nunique() - 10} más")
            
            # Estadísticas básicas
            print(f"\nEstadísticas descriptivas:")
            print(df.describe())
            
            return df
        except Exception as e:
            print(f"[ERROR] Error cargando dynamic_events.csv: {e}")
            return None
    
    def explore_phases_of_play(self, match_id: str = None) -> pd.DataFrame:
        """Explora estructura de phases_of_play.csv"""
        if not match_id:
            match_id = self.sample_match_id
        if not match_id:
            return None
            
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_phases_of_play.csv"
        try:
            response = requests.get(url)
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.text))
            
            print(f"\n{'='*60}")
            print(f"PHASES_OF_PLAY.CSV - Partido {match_id}")
            print(f"{'='*60}")
            print(f"Shape: {df.shape}")
            print(f"\nColumnas disponibles:")
            for col in df.columns:
                print(f"  - {col}")
            
            print(f"\nPrimeras 5 filas:")
            print(df.head())
            
            print(f"\nValores únicos:")
            for col in df.columns:
                if df[col].dtype == 'object' or df[col].nunique() < 20:
                    unique_vals = df[col].unique()[:10]
                    print(f"  {col}: {unique_vals}")
            
            return df
        except Exception as e:
            print(f"[ERROR] Error cargando phases_of_play.csv: {e}")
            return None
    
    def explore_tracking_sample(self, match_id: str = None, n_lines: int = 5) -> Dict:
        """Explora estructura de tracking_extrapolated.jsonl (muestra)"""
        if not match_id:
            match_id = self.sample_match_id
        if not match_id:
            return None
            
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_tracking_extrapolated.jsonl"
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            print(f"\n{'='*60}")
            print(f"TRACKING_EXTRAPOLATED.JSONL - Partido {match_id}")
            print(f"{'='*60}")
            
            frames = []
            for i, line in enumerate(response.iter_lines()):
                if i >= n_lines:
                    break
                if line:
                    frame_data = json.loads(line)
                    frames.append(frame_data)
            
            if frames:
                print(f"Estructura de un frame (muestra de {len(frames)} frames):")
                print(f"Claves principales: {list(frames[0].keys())}")
                
                # Análisis detallado
                sample_frame = frames[0]
                for key in sample_frame.keys():
                    print(f"\n  {key}:")
                    if isinstance(sample_frame[key], dict):
                        print(f"    Claves: {list(sample_frame[key].keys())}")
                        if 'player_data' in key or 'ball_data' in key:
                            print(f"    Tipo: {type(sample_frame[key])}")
                    elif isinstance(sample_frame[key], list):
                        print(f"    Longitud: {len(sample_frame[key])}")
                        if sample_frame[key] and isinstance(sample_frame[key][0], dict):
                            print(f"    Claves del primer elemento: {list(sample_frame[key][0].keys())}")
                    else:
                        print(f"    Valor ejemplo: {sample_frame[key]}")
                
                # Información de player_data
                if 'player_data' in sample_frame:
                    print(f"\n  player_data - Estructura:")
                    if sample_frame['player_data']:
                        player_sample = sample_frame['player_data'][0]
                        print(f"    Claves: {list(player_sample.keys())}")
                        print(f"    Ejemplo: {player_sample}")
                
                # Información de ball_data
                if 'ball_data' in sample_frame:
                    print(f"\n  ball_data - Estructura:")
                    print(f"    Claves: {list(sample_frame['ball_data'].keys())}")
                    print(f"    Ejemplo: {sample_frame['ball_data']}")
                
                # Información de possession
                if 'possession' in sample_frame:
                    print(f"\n  possession - Estructura:")
                    print(f"    Ejemplo: {sample_frame['possession']}")
            
            return frames
        except Exception as e:
            print(f"[ERROR] Error cargando tracking_extrapolated.jsonl: {e}")
            return None
    
    def identify_critical_events(self, df_events: pd.DataFrame) -> Dict[str, Any]:
        """Identifica posibles eventos críticos en dynamic_events"""
        if df_events is None or df_events.empty:
            return {}
        
        print(f"\n{'='*60}")
        print("ANÁLISIS DE EVENTOS CRÍTICOS")
        print(f"{'='*60}")
        
        critical_events = {}
        
        # Buscar columnas que puedan indicar eventos críticos
        print(f"\nBuscando eventos críticos potenciales...")
        
        # Análisis por columnas
        for col in df_events.columns:
            if 'type' in col.lower() or 'event' in col.lower():
                print(f"\nColumna '{col}':")
                unique_vals = df_events[col].unique()
                print(f"  Valores únicos ({len(unique_vals)}): {unique_vals[:20]}")
                
                # Contar frecuencias
                value_counts = df_events[col].value_counts()
                print(f"  Top 10 valores más frecuentes:")
                print(value_counts.head(10))
        
        # Buscar columnas de resultado/outcome
        outcome_cols = [col for col in df_events.columns if 'outcome' in col.lower() or 'result' in col.lower() or 'success' in col.lower()]
        if outcome_cols:
            print(f"\nColumnas de resultado encontradas: {outcome_cols}")
            for col in outcome_cols:
                print(f"  {col}: {df_events[col].unique()}")
        
        # Buscar columnas de equipo
        team_cols = [col for col in df_events.columns if 'team' in col.lower() or 'side' in col.lower()]
        if team_cols:
            print(f"\nColumnas de equipo encontradas: {team_cols}")
            for col in team_cols:
                print(f"  {col}: {df_events[col].unique()}")
        
        return critical_events
    
    def full_exploration(self):
        """Ejecuta exploración completa de todos los datos"""
        print("="*60)
        print("EXPLORACIÓN COMPLETA DE DATOS SKILLCORNER")
        print("="*60)
        
        # 1. Cargar información de partidos
        self.load_matches_info()
        
        if not self.sample_match_id:
            print("[ERROR] No se pudo obtener ID de partido de ejemplo")
            return
        
        # 2. Explorar match.json
        match_data = self.explore_match_json()
        
        # 3. Explorar dynamic_events.csv
        df_events = self.explore_dynamic_events()
        
        # 4. Explorar phases_of_play.csv
        df_phases = self.explore_phases_of_play()
        
        # 5. Explorar tracking (muestra)
        tracking_sample = self.explore_tracking_sample()
        
        # 6. Identificar eventos críticos
        if df_events is not None:
            self.identify_critical_events(df_events)
        
        print(f"\n{'='*60}")
        print("EXPLORACIÓN COMPLETA")
        print(f"{'='*60}")
        
        return {
            'matches_info': self.matches_info,
            'match_data': match_data,
            'dynamic_events': df_events,
            'phases_of_play': df_phases,
            'tracking_sample': tracking_sample
        }


if __name__ == "__main__":
    explorer = SkillCornerDataExplorer()
    results = explorer.full_exploration()

