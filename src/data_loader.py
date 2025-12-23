"""
Data Loader for SkillCorner Open Data
Carga datos directamente desde el repositorio de GitHub
"""

import json
import pandas as pd
import requests
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import io


class SkillCornerDataLoader:
    """Cargador de datos de SkillCorner desde GitHub"""
    
    BASE_URL = "https://raw.githubusercontent.com/SkillCorner/opendata/master/data"
    GITHUB_API_URL = "https://api.github.com/repos/SkillCorner/opendata/contents/data"
    
    def __init__(self):
        self.matches_info = None
        self.cache = {}  # Cache para evitar múltiples descargas
    
    def load_matches_info(self) -> List[Dict]:
        """Carga información de todos los partidos disponibles"""
        if 'matches_info' in self.cache:
            return self.cache['matches_info']
        
        url = f"{self.BASE_URL}/matches.json"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            self.matches_info = response.json()
            self.cache['matches_info'] = self.matches_info
            return self.matches_info
        except Exception as e:
            raise Exception(f"Error cargando matches.json: {e}")
    
    def load_match_json(self, match_id: str) -> Dict:
        """Carga información detallada de un partido"""
        cache_key = f"match_{match_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_match.json"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            self.cache[cache_key] = data
            return data
        except Exception as e:
            raise Exception(f"Error cargando match.json para {match_id}: {e}")
    
    def load_dynamic_events(self, match_id: str) -> pd.DataFrame:
        """Carga eventos dinámicos de un partido"""
        cache_key = f"events_{match_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_dynamic_events.csv"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.text))
            self.cache[cache_key] = df
            return df
        except Exception as e:
            raise Exception(f"Error cargando dynamic_events.csv para {match_id}: {e}")
    
    def load_phases_of_play(self, match_id: str) -> pd.DataFrame:
        """Carga fases de juego de un partido"""
        cache_key = f"phases_{match_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_phases_of_play.csv"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.text))
            self.cache[cache_key] = df
            return df
        except Exception as e:
            raise Exception(f"Error cargando phases_of_play.csv para {match_id}: {e}")
    
    def _is_git_lfs_pointer(self, content: str) -> bool:
        """Verifica si el contenido es un puntero de Git LFS"""
        return content.startswith('version https://git-lfs.github.com/spec/v1')
    
    def _download_from_lfs(self, match_id: str) -> List[Dict]:
        """
        Intenta descargar desde Git LFS usando la API de GitHub
        NOTA: Los archivos de tracking están en Git LFS y son muy grandes (89MB+)
        Para Streamlit Cloud, esto puede no ser viable. Retornamos lista vacía.
        """
        print(f"      ⚠️ Archivo está en Git LFS (muy grande para descargar)")
        print(f"      Los archivos de tracking son demasiado grandes para cargar desde Streamlit Cloud")
        print(f"      SOLUCIÓN: Trabajar sin tracking data o usar datos pre-procesados")
        return []
    
    def load_tracking_data(self, match_id: str, max_frames: Optional[int] = None) -> List[Dict]:
        """
        Carga datos de tracking de un partido
        NOTA: Los archivos de tracking están en Git LFS y son muy grandes.
        Para esta implementación, retornamos lista vacía y trabajamos sin tracking.
        """
        cache_key = f"tracking_{match_id}"
        if cache_key in self.cache and max_frames is None:
            return self.cache[cache_key]
        
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_tracking_extrapolated.jsonl"
        print(f"      Intentando cargar tracking: {match_id}")
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            print(f"      Status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"      ✗ No se puede cargar (status {response.status_code})")
                return []
            
            # Leer primeras líneas para verificar si es LFS
            first_lines = []
            for i, line in enumerate(response.iter_lines(decode_unicode=True)):
                if i < 3:
                    first_lines.append(line)
                else:
                    break
            
            # Verificar si es puntero de Git LFS
            if first_lines and self._is_git_lfs_pointer(first_lines[0]):
                return self._download_from_lfs(match_id)
            
            # Si no es LFS, intentar cargar normalmente
            response = requests.get(url, stream=True, timeout=120)
            frames = []
            line_count = 0
            
            for i, line in enumerate(response.iter_lines(decode_unicode=True)):
                line_count += 1
                if not line or line.strip() == '':
                    continue
                    
                try:
                    if isinstance(line, bytes):
                        line = line.decode('utf-8')
                    frame_data = json.loads(line)
                    frames.append(frame_data)
                    
                    if max_frames and len(frames) >= max_frames:
                        break
                except json.JSONDecodeError:
                    continue
            
            if max_frames is None:
                self.cache[cache_key] = frames
            
            print(f"      Cargados {len(frames)} frames")
            return frames
            
        except Exception as e:
            print(f"      ✗ Error: {e}")
            return []
    
    def get_match_ids(self) -> List[str]:
        """Obtiene lista de IDs de todos los partidos disponibles"""
        matches = self.load_matches_info()
        return [match.get('id') for match in matches if 'id' in match]
    
    def load_all_matches_data(self) -> Dict[str, Dict]:
        """
        Carga todos los datos de todos los partidos
        Retorna diccionario: {match_id: {match_json, events, phases, tracking}}
        """
        match_ids = self.get_match_ids()
        all_data = {}
        
        for match_id in match_ids:
            print(f"Cargando datos del partido {match_id}...")
            try:
                all_data[str(match_id)] = {
                    'match_json': self.load_match_json(str(match_id)),
                    'events': self.load_dynamic_events(str(match_id)),
                    'phases': self.load_phases_of_play(str(match_id)),
                    'match_id': str(match_id)
                }
            except Exception as e:
                print(f"Advertencia: Error cargando partido {match_id}: {e}")
                continue
        
        return all_data
