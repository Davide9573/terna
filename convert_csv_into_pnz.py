"""
Read .csv files and construct a dictionary indexed by source (Thermal, Wind, Geothermal, Photovoltaic, Self-consumption,
Hydro), each containing a NumPy array of 35040 values ordered chronologically (one value every 15 minutes, year 2025).
Save the dictionary in 'generation.npz' and provide a function for reloading it.

Usage
--------
    python convert_csv_into_npz.py
"""

from parameters import SOURCES
from utility import load_consumption_data_from_csv, load_generation_data_from_csv, load_import_export_data_from_csv, save_power_data_to_npz, load_power_data_from_npz
from pathlib import Path
import numpy as np

import utility

GEN_PATH = Path(__file__).parent / "power_generation_2025.csv"
IMP_PATH = Path(__file__).parent / "power_imp_exp_2025.csv"
CONS_PATH = Path(__file__).parent / "power_consumption_2025.csv"
NPZ_PATH = Path(__file__).parent / "power_2025.npz"

if __name__ == "__main__":
    print(f"Reading {GEN_PATH} ...")
    gen_data = load_generation_data_from_csv(GEN_PATH)
    print("\nDictionary built:")
    for src, vec in gen_data.power_item.items():
        n_valid = int(np.sum(~np.isnan(vec)))
        print(f"  {src:<18}  {len(vec):>6} elements  ({n_valid} valid)")
    print(f"Start date: {gen_data.start}")
    print(f"End date: {gen_data.end}")

    print(f"Reading {IMP_PATH} ...")
    imp_data = load_import_export_data_from_csv(IMP_PATH)
    print("\nDictionary built:")
    for src, vec in imp_data.power_item.items():
        n_valid = int(np.sum(~np.isnan(vec)))
        print(f"  {src:<18}  {len(vec):>6} elements  ({n_valid} valid)")
    print(f"Start date: {imp_data.start}")
    print(f"End date: {imp_data.end}")

    print(f"Reading {CONS_PATH} ...")
    cons_data = load_consumption_data_from_csv(CONS_PATH)
    print("\nDictionary built:")
    for src, vec in cons_data.power_item.items():
        n_valid = int(np.sum(~np.isnan(vec)))
        print(f"  {src:<18}  {len(vec):>6} elements  ({n_valid} valid)")
    print(f"Start date: {cons_data.start}")
    print(f"End date: {cons_data.end}")

    print(f"Merge of the three dictionaries ...")
    data = utility.merge_power_data(gen_data, imp_data, cons_data)
    print("\nDictionary built:")
    for src, vec in data.power_item.items():
        n_valid = int(np.sum(~np.isnan(vec)))
        print(f"  {src:<18}  {len(vec):>6} elements  ({n_valid} valid)")
    print(f"Start date: {data.start}")
    print(f"End date: {data.end}")

    save_power_data_to_npz(data, NPZ_PATH)
    size_kb = NPZ_PATH.stat().st_size / 1024
    print(f"\nFile saved: {NPZ_PATH}  ({size_kb:.1f} KB)")

    # Round-trip check: load the .npz file and compare with the original data
    reloaded = load_power_data_from_npz(NPZ_PATH)
    for src in data.power_item.keys():
        assert np.array_equal(data.power_item[src], reloaded.power_item[src], equal_nan=True), \
            f"Round-trip ERROR: {src} not equal"
    print("Round-trip check: OK")
