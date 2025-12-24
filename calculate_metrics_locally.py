"""
Script para calcular métricas R3ACT localmente y guardar en CSV
EJECUTAR LOCALMENTE con Git LFS instalado para descargar tracking data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from src.r3act_system import R3ACTSystem
import json

print("="*70)
print("R3ACT - CALCULADOR DE MÉTRICAS LOCAL")
print("="*70)
print("\nEste script calcula las métricas R3ACT localmente con tracking data")
print("Requisitos: Git LFS instalado y configurado")
print("="*70)

# Inicializar sistema
print("\n[1/4] Inicializando sistema R3ACT...")
r3act = R3ACTSystem(time_window='medium')

# Procesar todos los partidos CON tracking
print("\n[2/4] Procesando partidos (esto puede tardar 30-60 minutos)...")
print("NOTA: Se descargarán archivos de tracking desde Git LFS")
print("Asegúrate de tener Git LFS instalado: git lfs install")
print("\nIniciando procesamiento...\n")

try:
    results_df = r3act.process_all_matches(load_tracking=True)
    
    if results_df.empty:
        print("\n❌ ERROR: No se generaron resultados")
        sys.exit(1)
    
    print(f"\n[3/4] Resultados generados: {len(results_df)} eventos")
    
    # Verificar métricas calculadas
    crt_count = results_df['CRT'].notna().sum() if 'CRT' in results_df.columns else 0
    tsi_count = results_df['TSI'].notna().sum() if 'TSI' in results_df.columns else 0
    giri_count = results_df['GIRI'].notna().sum() if 'GIRI' in results_df.columns else 0
    
    print(f"\nMétricas calculadas:")
    print(f"  - CRT: {crt_count}/{len(results_df)} ({100*crt_count/len(results_df):.1f}%)")
    print(f"  - TSI: {tsi_count}/{len(results_df)} ({100*tsi_count/len(results_df):.1f}%)")
    print(f"  - GIRI: {giri_count}/{len(results_df)} ({100*giri_count/len(results_df):.1f}%)")
    
    if crt_count == 0:
        print("\n⚠️ ADVERTENCIA: No se calcularon métricas CRT/TSI")
        print("Verifica que Git LFS esté instalado y que los archivos se descargaron correctamente")
        response = input("\n¿Deseas continuar y guardar los resultados de todas formas? (s/n): ")
        if response.lower() != 's':
            print("Cancelado")
            sys.exit(1)
    
    # Guardar en CSV
    output_file = "r3act_metrics_preprocessed.csv"
    print(f"\n[4/4] Guardando resultados en {output_file}...")
    
    results_df.to_csv(output_file, index=False)
    
    print(f"\n✅ ÉXITO: Resultados guardados en {output_file}")
    print(f"   - Total eventos: {len(results_df)}")
    print(f"   - Columnas: {list(results_df.columns)}")
    print(f"\n📊 Estadísticas:")
    print(f"   - Eventos con CRT: {crt_count}")
    print(f"   - Eventos con TSI: {tsi_count}")
    print(f"   - Eventos con GIRI: {giri_count}")
    
    # Guardar también un resumen en JSON
    summary = {
        'total_events': len(results_df),
        'crt_calculated': int(crt_count),
        'tsi_calculated': int(tsi_count),
        'giri_calculated': int(giri_count),
        'crt_percentage': float(100*crt_count/len(results_df)) if len(results_df) > 0 else 0,
        'tsi_percentage': float(100*tsi_count/len(results_df)) if len(results_df) > 0 else 0,
        'giri_percentage': float(100*giri_count/len(results_df)) if len(results_df) > 0 else 0,
        'columns': list(results_df.columns),
        'match_ids': results_df['match_id'].unique().tolist() if 'match_id' in results_df.columns else [],
    }
    
    summary_file = "r3act_metrics_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Resumen guardado en {summary_file}")
    print("\n" + "="*70)
    print("PRÓXIMOS PASOS:")
    print("="*70)
    print(f"1. Sube {output_file} a tu repositorio GitHub")
    print(f"2. El Streamlit app cargará automáticamente estos datos")
    print(f"3. Los filtros funcionarán con los datos pre-procesados")
    print("="*70)
    
except KeyboardInterrupt:
    print("\n\n⚠️ Proceso cancelado por el usuario")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

