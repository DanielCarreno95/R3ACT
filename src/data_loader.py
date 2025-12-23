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
            return self.cache[cache_key].copy()
        
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_dynamic_events.csv"
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            # Usar low_memory=False para evitar warnings de tipos mixtos
            df = pd.read_csv(io.StringIO(response.text), low_memory=False)
            self.cache[cache_key] = df
            return df.copy()
        except Exception as e:
            raise Exception(f"Error cargando dynamic_events.csv para {match_id}: {e}")
    
    def load_phases_of_play(self, match_id: str) -> pd.DataFrame:
        """Carga fases de juego de un partido"""
        cache_key = f"phases_{match_id}"
        if cache_key in self.cache:
            return self.cache[cache_key].copy()
        
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_phases_of_play.csv"
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.text))
            self.cache[cache_key] = df
            return df.copy()
        except Exception as e:
            raise Exception(f"Error cargando phases_of_play.csv para {match_id}: {e}")
    
    def load_tracking_data(self, match_id: str, max_frames: Optional[int] = None) -> List[Dict]:
        """
        Carga datos de tracking de un partido
        Por defecto carga todos los frames, pero puede limitarse con max_frames
        """
        cache_key = f"tracking_{match_id}"
        if cache_key in self.cache and max_frames is None:
            return self.cache[cache_key]
        
        url = f"{self.BASE_URL}/matches/{match_id}/{match_id}_tracking_extrapolated.jsonl"
        try:
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            frames = []
            line_count = 0
            for i, line in enumerate(response.iter_lines(decode_unicode=True)):
                line_count += 1
                if line:
                    try:
                        # Decodificar si es bytes
                        if isinstance(line, bytes):
                            line = line.decode('utf-8')
                        frame_data = json.loads(line)
                        frames.append(frame_data)
                        if max_frames and len(frames) >= max_frames:
                            break
                    except json.JSONDecodeError as e:
                        if i < 10:  # Solo mostrar primeros errores
                            print(f"      Línea {i} inválida: {e}")
                        continue  # Saltar líneas inválidas
            
            if max_frames is None:
                self.cache[cache_key] = frames
            
            if len(frames) == 0 and line_count > 0:
                print(f"      ADVERTENCIA: Se leyeron {line_count} líneas pero 0 frames válidos")
            
            return frames
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"      ADVERTENCIA: Archivo no encontrado en {url}")
                return []
            else:
                raise Exception(f"Error HTTP cargando tracking data para {match_id}: {e}")
        except Exception as e:
            print(f"      ERROR cargando tracking: {e}")
            import traceback
            traceback.print_exc()
            return []  # Retornar lista vacía en lugar de lanzar excepción
    
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

