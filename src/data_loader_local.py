"""
Data Loader para uso LOCAL con archivos descargados via Git LFS
Usa este archivo cuando tengas los archivos de tracking descargados localmente
"""

import json
import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path
import os

class SkillCornerDataLoaderLocal:
    """Cargador de datos desde archivos locales (después de clonar con Git LFS)"""
    
    def __init__(self, local_data_path: str = "../opendata/data"):
        """
        Args:
            local_data_path: Ruta al directorio data/ del repositorio opendata clonado
        """
        self.local_data_path = Path(local_data_path)
        self.cache = {}
    
    def load_matches_info(self) -> List[Dict]:
        """Carga información de todos los partidos"""
        matches_file = self.local_data_path / "matches.json"
        with open(matches_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_match_json(self, match_id: str) -> Dict:
        """Carga información detallada de un partido"""
        match_file = self.local_data_path / "matches" / match_id / f"{match_id}_match.json"
        with open(match_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_dynamic_events(self, match_id: str) -> pd.DataFrame:
        """Carga eventos dinámicos"""
        events_file = self.local_data_path / "matches" / match_id / f"{match_id}_dynamic_events.csv"
        return pd.read_csv(events_file)
    
    def load_phases_of_play(self, match_id: str) -> pd.DataFrame:
        """Carga fases de juego"""
        phases_file = self.local_data_path / "matches" / match_id / f"{match_id}_phases_of_play.csv"
        return pd.read_csv(phases_file)
    
    def load_tracking_data(self, match_id: str, max_frames: Optional[int] = None) -> List[Dict]:
        """Carga datos de tracking desde archivo local"""
        tracking_file = self.local_data_path / "matches" / match_id / f"{match_id}_tracking_extrapolated.jsonl"
        
        if not tracking_file.exists():
            print(f"      Archivo no encontrado: {tracking_file}")
            return []
        
        frames = []
        with open(tracking_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if line.strip():
                    try:
                        frame_data = json.loads(line)
                        frames.append(frame_data)
                        if max_frames and len(frames) >= max_frames:
                            break
                    except json.JSONDecodeError:
                        continue
        
        print(f"      Cargados {len(frames)} frames desde archivo local")
        return frames
    
    def get_match_ids(self) -> List[str]:
        """Obtiene lista de IDs de partidos"""
        matches = self.load_matches_info()
        return [str(match.get('id')) for match in matches if 'id' in match]
    
    def load_all_matches_data(self) -> Dict[str, Dict]:
        """Carga todos los datos de todos los partidos"""
        match_ids = self.get_match_ids()
        all_data = {}
        
        for match_id in match_ids:
            try:
                all_data[match_id] = {
                    'match_json': self.load_match_json(match_id),
                    'events': self.load_dynamic_events(match_id),
                    'phases': self.load_phases_of_play(match_id),
                    'match_id': match_id
                }
            except Exception as e:
                print(f"Error cargando partido {match_id}: {e}")
                continue
        
        return all_data

