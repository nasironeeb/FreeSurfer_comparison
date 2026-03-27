"""
    function that are use to compare Freesurfer v7.1 and Freesurfer v8.1
"""

import os
import glob
import re
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from scipy import stats

def parse_aseg(file_path, structures):
    """Extrait les volumes d'un fichier aseg.stats pour une liste de structures."""
    data = {}
    if not os.path.isfile(file_path):
        return data

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.split()
                # Structures segmentées (colonnes 3 et 4)
                if len(parts) > 4 and parts[4] in structures:
                    data[parts[4]] = float(parts[3])
                # Mesures globales (TotalGrayVol, etc.)
                for s in structures:
                    if f"# Measure {s}" in line:
                        data[s] = float(line.split(',')[3])
    except Exception as e:
        print(f"Erreur lors de la lecture de {file_path} : {e}")

    return data

def collect_fs_data(
    regex_path_v7,
    regex_path_v8,
    structures,
    file_name="aseg.stats"):
    """
    Parcourt les dossiers et compare les deux versions de FreeSurfer.

    Returns
    -------
        dataframe
    """
    # Construire des maps (sub_id, ses_id) -> chemin
    def build_map(paths):
        m = {}
        for p in paths:
            try:
                sub_match = re.search(r'sub-([A-Za-z0-9]+)', p)
                ses_match = re.search(r'ses-([A-Za-z0-9]+)', p)
                if not sub_match or not ses_match:
                    continue
                sub_id = sub_match.group(1)
                ses_id = ses_match.group(1)
                key = (sub_id, ses_id)
                # si plusieurs fichiers pour la même paire, on garde le premier trouvé
                if key not in m:
                    m[key] = p
            except Exception:
                continue
        return m

    map_v7 = build_map(regex_path_v7)
    map_v8 = build_map(regex_path_v8)
    # Intersection des sujets/sessions présents dans les deux versions
    common_keys = set(map_v7.keys()) & set(map_v8.keys())

    results = []
    for key in sorted(common_keys):
        sub_id, ses_id = key
        f7 = map_v7[key]
        f8 = map_v8[key]

        # Si les chemins fournis ne pointent pas directement sur le fichier, tenter de construire le chemin
        if os.path.isdir(f7):
            f7 = os.path.join(f7, "stats", file_name)
        if os.path.isdir(f8):
            f8 = os.path.join(f8, "stats", file_name)

        if not os.path.exists(f7) or not os.path.exists(f8):
            # ignorer si l'un des fichiers manque
            continue

        try:
            if file_name == "aseg.stats":
                data7 = parse_aseg(f7, structures)
                data8 = parse_aseg(f8, structures)

                for struct in structures:
                    if struct in data7 and struct in data8 and data7[struct] != 0:
                        diff_perc = (data8[struct] - data7[struct]) / data7[struct] * 100
                        results.append({
                            "Subject": sub_id,
                            "Session": ses_id,
                            "Structure": struct,
                            "v7": data7[struct],
                            "v8": data8[struct],
                            "Diff_Perc": diff_perc
                        })
        except Exception as e:
            print(f"Erreur sur la paire {sub_id}_{ses_id} : {e}")

    return pd.DataFrame(results)

