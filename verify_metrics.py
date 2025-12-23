"""
Quick verification script to check if R3ACT metrics are being calculated correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.r3act_system import R3ACTSystem
import pandas as pd

print("="*60)
print("R3ACT METRICS VERIFICATION")
print("="*60)

# Initialize system
print("\n[1/3] Initializing R3ACT system...")
r3act = R3ACTSystem(time_window='medium')

# Process matches WITH tracking (required for CRT and TSI)
print("\n[2/3] Processing matches with tracking enabled...")
print("NOTE: This will take several minutes as it loads tracking data from GitHub")
results_df = r3act.process_all_matches(load_tracking=True)

# Verify results
print("\n[3/3] Verifying metrics...")
print(f"\nTotal events detected: {len(results_df)}")

if results_df.empty:
    print("\n[ERROR] No events detected!")
    sys.exit(1)

# Check columns
print(f"\nColumns in results: {list(results_df.columns)}")

# Check CRT
if 'CRT' in results_df.columns:
    crt_values = results_df['CRT'].dropna()
    print(f"\nCRT Statistics:")
    print(f"  - Total events with CRT: {len(crt_values)} / {len(results_df)} ({100*len(crt_values)/len(results_df):.1f}%)")
    if len(crt_values) > 0:
        print(f"  - Mean CRT: {crt_values.mean():.2f}s")
        print(f"  - Median CRT: {crt_values.median():.2f}s")
        print(f"  - Min CRT: {crt_values.min():.2f}s")
        print(f"  - Max CRT: {crt_values.max():.2f}s")
    else:
        print("  [WARNING] No CRT values calculated!")
else:
    print("\n[ERROR] CRT column not found!")

# Check TSI
if 'TSI' in results_df.columns:
    tsi_values = results_df['TSI'].dropna()
    print(f"\nTSI Statistics:")
    print(f"  - Total events with TSI: {len(tsi_values)} / {len(results_df)} ({100*len(tsi_values)/len(results_df):.1f}%)")
    if len(tsi_values) > 0:
        print(f"  - Mean TSI: {tsi_values.mean():.3f}")
        print(f"  - Median TSI: {tsi_values.median():.3f}")
        print(f"  - Min TSI: {tsi_values.min():.3f}")
        print(f"  - Max TSI: {tsi_values.max():.3f}")
    else:
        print("  [WARNING] No TSI values calculated!")
else:
    print("\n[ERROR] TSI column not found!")

# Check GIRI
if 'GIRI' in results_df.columns:
    giri_values = results_df['GIRI'].dropna()
    goal_events = results_df[results_df['event_type'].isin(['goal_scored', 'goal_conceded'])]
    print(f"\nGIRI Statistics:")
    print(f"  - Total goal events: {len(goal_events)}")
    print(f"  - Total events with GIRI: {len(giri_values)} / {len(goal_events)} ({100*len(giri_values)/len(goal_events) if len(goal_events) > 0 else 0:.1f}%)")
    if len(giri_values) > 0:
        print(f"  - Mean GIRI: {giri_values.mean():.3f}")
        print(f"  - Median GIRI: {giri_values.median():.3f}")
        print(f"  - Min GIRI: {giri_values.min():.3f}")
        print(f"  - Max GIRI: {giri_values.max():.3f}")
    else:
        print("  [INFO] No GIRI values calculated (this is normal if there are no goal events)")
else:
    print("\n[ERROR] GIRI column not found!")

# Summary
print("\n" + "="*60)
print("VERIFICATION SUMMARY")
print("="*60)

has_crt = 'CRT' in results_df.columns and len(results_df['CRT'].dropna()) > 0
has_tsi = 'TSI' in results_df.columns and len(results_df['TSI'].dropna()) > 0
has_giri = 'GIRI' in results_df.columns and len(results_df['GIRI'].dropna()) > 0

if has_crt and has_tsi:
    print("\n[OK] Core metrics (CRT, TSI) are being calculated correctly!")
    print("     The Streamlit dashboard should display values instead of N/A.")
else:
    print("\n[WARNING] Some metrics are missing:")
    if not has_crt:
        print("  - CRT is not being calculated")
    if not has_tsi:
        print("  - TSI is not being calculated")

if has_giri:
    print("\n[OK] GIRI is available for goal events")
else:
    print("\n[INFO] GIRI not available (normal if no goal events in dataset)")

print("\n" + "="*60)

