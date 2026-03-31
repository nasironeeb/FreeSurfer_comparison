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
    """
    Extracts the volumes from an aseg.stats file for a list of structures.

    Parameters
    ----------
    file_path : str
        Path to the .stats file
    structures : list or None
        List of structures to extract (None = all)

    Returns
    -------
    dict
        {structure: valeur}
    """
    data = {}
    if not os.path.isfile(file_path):
        return data
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.split()
                if len(parts) > 4 and parts[4] in structures:
                    data[parts[4]] = float(parts[3])
                # Comprehensive measures (TotalGrayVol, etc.)
                for s in structures:
                    if f"# Measure {s}" in line:
                        data[s] = float(line.split(',')[3])
    except Exception as e:
        print(f"Erreur lors de la lecture de {file_path} : {e}")
    return data

def parse_aparc_stats(file_path, structures=None, metric="ThickAvg"):
    """
    Extracts a specific metric (e.g., thickness) from an aparc.stats file for a list of structures.
    
    Parameters
    ----------
    file_path : str
        Path to the .stats file
    structures : list or None
        List of structures to extract (None = all)
    metric : str
        Metric to extract (e.g., "ThickAvg", "GrayVol", "SurfArea"). Default is "ThickAvg".
    
    Returns
    -------
    dict
        {structure: valeur}
    """
    # Column mapping (based on the standard aparc.stats format)
    # 0: StructName, 1: NumVert, 2: SurfArea, 3: GrayVol, 4: ThickAvg, etc.
    # Note: In FreeSurfer, the actual index often starts after the structure name.
    metric_map = {
        "NumVert": 1,
        "SurfArea": 2,
        "GrayVol": 3,
        "ThickAvg": 4,
        "ThickStd": 5,
        "MeanCurv": 6,
        "GausCurv": 7,
        "FoldInd": 8,
        "CurvInd": 9
    }
    if not os.path.exists(file_path):
        return {}
    if metric not in metric_map:
        raise ValueError(f"Métrique '{metric}' invalide. Options: {list(metric_map.keys())}")
    data = {}
    target_idx = metric_map[metric]
    # Conversion to a set for O(1) search
    search_set = set(structures) if structures else None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.split()
                if len(parts) < 10: # Safety checks on the line format
                    continue
                struct_name = parts[0]
                # If `structures` is `None`, everything is accepted. Otherwise, we check for its presence.
                if search_set is None or struct_name in search_set:
                    try:
                        data[struct_name] = float(parts[target_idx])
                    except (ValueError, IndexError):
                        continue
    except IOError as e:
        print(f"Erreur de lecture : {e}")
        return {}
    return data

def collect_fs_data(
    regex_path_v7,
    regex_path_v8,
    structures,
    file_name="aseg.stats"):
    """
    Parses FreeSurfer directories, extracts volumes/thicknesses for given structures, 
    and calculates the relative difference between version 7 and version 8.

    The function matches subjects and sessions present in both versions, 
    searches for the specified statistics file, and compiles the results into a DataFrame.

    Parameters
    ----------
    regex_path_v7 : list of str
        List of paths (or glob outputs) pointing to FS v7 folders or files.
    regex_path_v8 : list of str
        List of paths (or glob outputs) pointing to FS v8 folders or files.
    structures : list of str
        List of anatomical structure names to extract (e.g., ['Left-Hippocampus', 'Brain-Stem']).
    file_name : str, optional
        Name of the stats file to parse. Supports "aseg.stats" or atlas files 
        such as "aparc.stats". Default is "aseg.stats".

    Returns
    -------
    pandas.DataFrame
        A table containing the following columns:
        - 'Subject': Subject ID extracted from the path.
        - 'Session': Session ID extracted from the path.
        - 'Structure': Name of the anatomical structure.
        - 'v7': Numerical value from FreeSurfer v7.
        - 'v8': Numerical value from FreeSurfer v8.
        - 'Diff_Perc': Percentage difference [(v8 - v7) / v7 * 100].

    Notes
    -----
    - The function assumes that paths contain 'sub-<id>' and 'ses-<id>' patterns.
    - If a path is a directory, it automatically looks into the 'stats/' sub-folder.
    - (Subject, Session) pairs not present in both versions are ignored.
    """
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
                # if multiple files are founded, we keep the first one
                if key not in m:
                    m[key] = p
            except Exception:
                continue
        return m

    map_v7 = build_map(regex_path_v7)
    map_v8 = build_map(regex_path_v8)
    # Intersect subject/session pairs present in both versions
    common_keys = set(map_v7.keys()) & set(map_v8.keys())
    results = []
    for key in sorted(common_keys):
        sub_id, ses_id = key
        f7 = map_v7[key]
        f8 = map_v8[key]
        # If the provided paths do not point directly to the file, try to construct the path
        if os.path.isdir(f7):
            f7 = os.path.join(f7, "stats", file_name)
        if os.path.isdir(f8):
            f8 = os.path.join(f8, "stats", file_name)
        if not os.path.exists(f7) or not os.path.exists(f8):
            # ignore if one of the files is missing
            continue
        try:
            if file_name == "aseg.stats":
                data7 = parse_aseg(f7, structures)
                data8 = parse_aseg(f8, structures)
            if file_name.endswith("a2009s.stats") or file_name.endswith("DKTatlas.stats"):
                data7 = parse_aparc_stats(f7, structures)
                data8 = parse_aparc_stats(f8, structures)

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
