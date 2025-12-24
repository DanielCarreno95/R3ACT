"""
Script mejorado para descargar tracking data y calcular métricas
Intenta múltiples métodos para acceder a los archivos LFS
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import subprocess
import pandas as pd
from src.r3act_system import R3ACTSystem

print("="*70)
print("R3ACT - DESCARGAR Y CALCULAR MÉTRICAS")
print("="*70)

def try_download_with_git_lfs(match_id):
    """Intenta descargar usando git lfs directamente"""
    try:
        # Verificar si git lfs está instalado
        result = subprocess.run(['git', 'lfs', 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  Git LFS detectado: {result.stdout.strip()}")
            return True
    except:
        pass
    return False

def try_download_from_github_api(match_id):
    """Intenta descargar usando GitHub API"""
    url = f"https://api.github.com/repos/SkillCorner/opendata/contents/data/matches/{match_id}/{match_id}_tracking_extrapolated.jsonl"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'download_url' in data:
                # Intentar descargar el archivo
                download_url = data['download_url']
                file_response = requests.get(download_url, stream=True, timeout=120)
                if file_response.status_code == 200:
                    # Verificar si es LFS pointer
                    first_line = next(file_response.iter_lines(decode_unicode=True), None)
                    if first_line and 'git-lfs' in first_line:
                        print(f"  ⚠️ Archivo en Git LFS, necesitamos descargar el contenido real")
                        # Intentar obtener el SHA y descargar desde LFS
                        sha = data.get('sha')
                        if sha:
                            # GitHub LFS endpoint
                            lfs_url = f"https://github.com/SkillCorner/opendata.git/info/lfs/objects/batch"
                            lfs_payload = {
                                "operation": "download",
                                "objects": [{"oid": sha, "size": data.get('size', 0)}]
                            }
                            # Esto requiere autenticación, no funcionará sin token
                            return False
                    else:
                        return True  # No es LFS, podemos descargarlo
    except Exception as e:
        print(f"  Error con GitHub API: {e}")
    return False

def download_tracking_alternative(match_id):
    """Método alternativo: intentar desde diferentes URLs"""
    urls_to_try = [
        f"https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{match_id}/{match_id}_tracking_extrapolated.jsonl",
        f"https://github.com/SkillCorner/opendata/raw/master/data/matches/{match_id}/{match_id}_tracking_extrapolated.jsonl",
    ]
    
    for url in urls_to_try:
        try:
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                # Leer primeras líneas
                first_lines = []
                for i, line in enumerate(response.iter_lines(decode_unicode=True)):
                    if i < 3:
                        first_lines.append(line)
                    else:
                        break
                
                # Si no es LFS pointer, retornar True
                if first_lines and 'git-lfs' not in first_lines[0]:
                    return True, url
        except:
            continue
    
    return False, None

# Verificar métodos disponibles
print("\n[1/4] Verificando métodos de descarga...")
has_git_lfs = try_download_with_git_lfs("test")

if not has_git_lfs:
    print("  ⚠️ Git LFS no está instalado")
    print("  Intentando métodos alternativos...")
    
    # Probar con un match_id de ejemplo
    test_match = "2017461"
    success, url = download_tracking_alternative(test_match)
    
    if not success:
        print("\n[PROBLEMA]: No se puede acceder a los archivos de tracking")
        print("Los archivos están en Git LFS y requieren:")
        print("  1. Git LFS instalado localmente")
        print("  2. Clonar el repositorio con: git clone https://github.com/SkillCorner/opendata.git")
        print("  3. Ejecutar: git lfs pull")
        print("\nAlternativa: Usar datos de muestra o calcular métricas simplificadas")
        
        # Preguntar si quiere continuar con datos de muestra
        print("\n¿Deseas generar un CSV de ejemplo con estructura correcta?")
        print("(Las métricas serán None, pero el dashboard funcionará)")
        
        # Generar CSV de ejemplo
        print("\n[2/4] Generando CSV de ejemplo con estructura correcta...")
        from src.data_loader import SkillCornerDataLoader
        from src.event_detector import CriticalEventDetector
        
        loader = SkillCornerDataLoader()
        detector = CriticalEventDetector()
        
        # Cargar eventos sin tracking
        all_matches_data = loader.load_all_matches_data()
        all_results = []
        
        for match_id, match_data in all_matches_data.items():
            events_df = match_data['events']
            match_json = match_data['match_json']
            
            critical_events = detector.detect_critical_events(events_df, match_id, match_json)
            
            for _, event in critical_events.iterrows():
                result = {
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
                    'CRT': None,  # No se puede calcular sin tracking
                    'TSI': None,  # No se puede calcular sin tracking
                    'GIRI': None,  # No se puede calcular sin tracking
                }
                all_results.append(result)
        
        results_df = pd.DataFrame(all_results)
        
        # Enriquecer con nombres
        r3act = R3ACTSystem(time_window='medium')
        results_df = r3act._enrich_with_names(results_df, all_matches_data)
        
        output_file = "r3act_metrics_preprocessed.csv"
        results_df.to_csv(output_file, index=False)
        
        print(f"\n[OK] CSV de ejemplo generado: {output_file}")
        print(f"   - Total eventos: {len(results_df)}")
        print(f"   - Métricas: None (requieren tracking data)")
        print(f"\n⚠️ NOTA: Este CSV tiene la estructura correcta pero métricas = None")
        print("   Para métricas reales, necesitas ejecutar con Git LFS localmente")
        
        sys.exit(0)

# Si llegamos aquí, tenemos Git LFS o acceso directo
print("\n[2/4] Inicializando sistema R3ACT...")
r3act = R3ACTSystem(time_window='medium')

print("\n[3/4] Procesando partidos con tracking data...")
print("NOTA: Esto puede tardar 30-60 minutos dependiendo de la conexión\n")

try:
    results_df = r3act.process_all_matches(load_tracking=True)
    
    if results_df.empty:
        print("\n❌ ERROR: No se generaron resultados")
        sys.exit(1)
    
    print(f"\n[4/4] Guardando resultados...")
    
    # Verificar métricas
    crt_count = results_df['CRT'].notna().sum() if 'CRT' in results_df.columns else 0
    tsi_count = results_df['TSI'].notna().sum() if 'TSI' in results_df.columns else 0
    giri_count = results_df['GIRI'].notna().sum() if 'GIRI' in results_df.columns else 0
    
    print(f"\nMétricas calculadas:")
    print(f"  - CRT: {crt_count}/{len(results_df)} ({100*crt_count/len(results_df):.1f}%)")
    print(f"  - TSI: {tsi_count}/{len(results_df)} ({100*tsi_count/len(results_df):.1f}%)")
    print(f"  - GIRI: {giri_count}/{len(results_df)} ({100*giri_count/len(results_df):.1f}%)")
    
    # Guardar CSV
    output_file = "r3act_metrics_preprocessed.csv"
    results_df.to_csv(output_file, index=False)
    
        print(f"\n[OK] EXITO: Resultados guardados en {output_file}")
        print(f"   - Total eventos: {len(results_df)}")
        print(f"   - Metricas reales calculadas")
    
except Exception as e:
        print(f"\n[ERROR]: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

