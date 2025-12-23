"""
Script de diagnóstico para identificar problemas con la carga de tracking data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from src.data_loader import SkillCornerDataLoader

print("="*70)
print("DIAGNÓSTICO DE CARGA DE TRACKING DATA")
print("="*70)

loader = SkillCornerDataLoader()

# 1. Verificar que podemos cargar matches.json
print("\n[1/5] Verificando carga de matches.json...")
try:
    matches = loader.load_matches_info()
    print(f"  ✓ Cargados {len(matches)} partidos")
    if len(matches) > 0:
        test_match_id = str(matches[0].get('id'))
        print(f"  ✓ ID del primer partido: {test_match_id}")
    else:
        print("  ✗ No hay partidos disponibles")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. Verificar URL del tracking data
print(f"\n[2/5] Verificando URL del tracking data para partido {test_match_id}...")
url = f"{loader.BASE_URL}/matches/{test_match_id}/{test_match_id}_tracking_extrapolated.jsonl"
print(f"  URL: {url}")

try:
    response = requests.get(url, stream=True, timeout=30)
    print(f"  Status Code: {response.status_code}")
    
    if response.status_code == 404:
        print(f"  ✗ ERROR: Archivo no encontrado (404)")
        print(f"  Verificando si existe el directorio del partido...")
        
        # Intentar cargar match.json para verificar que el partido existe
        match_json_url = f"{loader.BASE_URL}/matches/{test_match_id}/{test_match_id}_match.json"
        match_response = requests.get(match_json_url, timeout=30)
        if match_response.status_code == 200:
            print(f"  ✓ match.json existe, pero tracking_extrapolated.jsonl no")
            print(f"  Posible problema: El archivo tiene otro nombre o no existe")
        else:
            print(f"  ✗ match.json tampoco existe (status: {match_response.status_code})")
    elif response.status_code == 200:
        print(f"  ✓ Archivo encontrado (200)")
        
        # 3. Intentar leer el archivo
        print(f"\n[3/5] Intentando leer el archivo...")
        frames = []
        line_count = 0
        error_count = 0
        
        for i, line in enumerate(response.iter_lines(decode_unicode=True)):
            line_count += 1
            if line:
                try:
                    if isinstance(line, bytes):
                        line = line.decode('utf-8')
                    frame_data = json.loads(line)
                    frames.append(frame_data)
                    
                    if len(frames) == 1:
                        print(f"  ✓ Primer frame cargado correctamente")
                        print(f"     Keys del frame: {list(frame_data.keys())[:10]}")
                    
                    if len(frames) >= 10:
                        print(f"  ✓ Cargados {len(frames)} frames (mostrando primeros 10)")
                        break
                except json.JSONDecodeError as e:
                    error_count += 1
                    if error_count <= 3:
                        print(f"  ✗ Error en línea {i}: {e}")
                        print(f"     Primeros 100 caracteres: {line[:100]}")
        
        print(f"\n  Resumen:")
        print(f"    - Líneas leídas: {line_count}")
        print(f"    - Frames válidos: {len(frames)}")
        print(f"    - Errores de JSON: {error_count}")
        
        if len(frames) == 0:
            print(f"\n  ✗ PROBLEMA: Se leyeron {line_count} líneas pero 0 frames válidos")
            print(f"  Posibles causas:")
            print(f"    1. El formato del archivo no es JSONL válido")
            print(f"    2. Problema de codificación")
            print(f"    3. El archivo está vacío o corrupto")
        else:
            print(f"\n  ✓ ÉXITO: Se pueden cargar frames correctamente")
            
            # Verificar estructura del frame
            if len(frames) > 0:
                frame = frames[0]
                print(f"\n[4/5] Verificando estructura del frame...")
                required_keys = ['frame', 'timestamp', 'period', 'player_data', 'possession']
                for key in required_keys:
                    if key in frame:
                        print(f"  ✓ '{key}' presente")
                    else:
                        print(f"  ✗ '{key}' AUSENTE")
                
                if 'player_data' in frame:
                    player_data = frame['player_data']
                    if isinstance(player_data, list) and len(player_data) > 0:
                        print(f"  ✓ player_data tiene {len(player_data)} jugadores")
                        first_player = player_data[0]
                        print(f"     Keys del jugador: {list(first_player.keys())[:5]}")
                    else:
                        print(f"  ✗ player_data está vacío o no es una lista")
    
    else:
        print(f"  ✗ Status code inesperado: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        
except requests.exceptions.RequestException as e:
    print(f"  ✗ Error de conexión: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"  ✗ Error inesperado: {e}")
    import traceback
    traceback.print_exc()

# 5. Probar método load_tracking_data
print(f"\n[5/5] Probando método load_tracking_data()...")
try:
    tracking_frames = loader.load_tracking_data(test_match_id)
    print(f"  Frames retornados: {len(tracking_frames)}")
    if len(tracking_frames) > 0:
        print(f"  ✓ ÉXITO: El método funciona correctamente")
    else:
        print(f"  ✗ PROBLEMA: El método retorna 0 frames")
except Exception as e:
    print(f"  ✗ ERROR en load_tracking_data(): {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("FIN DEL DIAGNÓSTICO")
print("="*70)

