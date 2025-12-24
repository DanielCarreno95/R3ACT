"""
Script para calcular métricas REALES usando archivos locales descargados con Git LFS
EJECUTAR DESPUÉS de clonar el repositorio SkillCorner con Git LFS
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from src.r3act_system import R3ACTSystem
from src.data_loader_local import SkillCornerDataLoaderLocal

print("="*70)
print("R3ACT - CALCULO CON DATOS LOCALES (GIT LFS)")
print("="*70)

# Verificar que existe el directorio de datos
local_path = "../opendata/data"
if not os.path.exists(local_path):
    print(f"\n[ERROR]: No se encuentra el directorio {local_path}")
    print("\nINSTRUCCIONES:")
    print("1. Clona el repositorio SkillCorner:")
    print("   git clone https://github.com/SkillCorner/opendata.git")
    print("2. Entra al directorio:")
    print("   cd opendata")
    print("3. Descarga los archivos LFS:")
    print("   git lfs pull")
    print("4. Vuelve al directorio del proyecto y ejecuta este script")
    sys.exit(1)

print(f"\n[1/4] Usando datos locales desde: {local_path}")

# Crear loader local
loader = SkillCornerDataLoaderLocal(local_path)

# Crear sistema R3ACT con loader personalizado
print("\n[2/4] Inicializando sistema R3ACT...")
r3act = R3ACTSystem(time_window='medium')

# Reemplazar el data_loader con el local
r3act.data_loader = loader

print("\n[3/4] Procesando partidos con tracking data local...")
print("NOTA: Esto puede tardar 30-60 minutos\n")

try:
    # Cargar datos usando el loader local
    all_matches_data = loader.load_all_matches_data()
    match_ids = list(all_matches_data.keys())
    print(f"Cargados {len(match_ids)} partidos")
    
    # Cargar tracking data local
    print("\nCargando tracking data desde archivos locales...")
    tracking_data_dict = {}
    for match_id in match_ids:
        tracking_frames = loader.load_tracking_data(match_id)
        tracking_data_dict[match_id] = tracking_frames
        print(f"  Partido {match_id}: {len(tracking_frames)} frames")
    
    # Calcular baselines
    print("\nCalculando estado base...")
    r3act.baseline_calculator.calculate_baselines(all_matches_data, tracking_data_dict)
    r3act.baseline_calculator.calculate_velocity_baselines(all_matches_data, tracking_data_dict)
    
    # Inicializar calculador de métricas
    from src.metrics_calculator import MetricsCalculator
    r3act.metrics_calculator = MetricsCalculator(r3act.baseline_calculator)
    
    # Procesar partidos
    print("\nProcesando partidos y calculando métricas...")
    all_results = []
    for match_id in match_ids:
        print(f"\nProcesando partido {match_id}...")
        try:
            match_results = r3act._process_match(
                match_id,
                all_matches_data[match_id],
                tracking_data_dict.get(match_id, [])
            )
            all_results.extend(match_results)
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    # Crear DataFrame
    print("\n[4/4] Generando dataset final...")
    if all_results:
        # Asegurar columnas
        for result in all_results:
            if 'CRT' not in result:
                result['CRT'] = None
            if 'TSI' not in result:
                result['TSI'] = None
            if 'GIRI' not in result:
                result['GIRI'] = None
        
        results_df = pd.DataFrame(all_results)
        
        # Enriquecer con nombres
        results_df = r3act._enrich_with_names(results_df, all_matches_data)
        
        # Estadísticas
        crt_count = results_df['CRT'].notna().sum()
        tsi_count = results_df['TSI'].notna().sum()
        giri_count = results_df['GIRI'].notna().sum()
        
        print(f"\nMetricas calculadas:")
        print(f"  - CRT: {crt_count}/{len(results_df)} ({100*crt_count/len(results_df):.1f}%)")
        print(f"  - TSI: {tsi_count}/{len(results_df)} ({100*tsi_count/len(results_df):.1f}%)")
        print(f"  - GIRI: {giri_count}/{len(results_df)} ({100*giri_count/len(results_df):.1f}%)")
        
        # Guardar
        output_file = "r3act_metrics_preprocessed.csv"
        results_df.to_csv(output_file, index=False)
        
        print(f"\n[OK] EXITO: Resultados guardados en {output_file}")
        print(f"   - Total eventos: {len(results_df)}")
        print(f"   - Metricas REALES calculadas")
        print(f"\nSiguiente paso: Sube este archivo a GitHub")
        print(f"   git add {output_file}")
        print(f"   git commit -m 'Add real R3ACT metrics'")
        print(f"   git push origin main")
    else:
        print("\n[ERROR]: No se generaron resultados")
        
except Exception as e:
    print(f"\n[ERROR]: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

