"""
test case of a dataset (all subject)
if you have the freesurfer v7.1 & freesurfer v8.1 output  
"""
import os
import glob
import re
from pathlib import Path

from functions import (
    parse_aseg,
    parse_aparc_stats,
    collect_fs_data
) 

# --- CONFIGURATION ---
REGEX_PATH_V7 = glob.glob("~/derivatives/freesurfer-reconall-v7.1.1/sub-*/ses-*/")
REGEX_PATH_V8 = glob.glob("~/derivatives/freesurfer-reconall-v8.1.0/sub-*/ses-*/")

# List of values(regions) that we want to compare
MY_STRUCTURES = [
    "Left-Hippocampus", 
    "Right-Hippocampus", 
    "Left-Amygdala", 
    "Right-Amygdala",
    "Left-Caudate",
    "Right-Caudate",
    "Left-Putamen",
    "Right-Putamen",
    "TotalGray",
    "EstimatedTotalIntraCranialVol"
]
MY_STRUCTURES_a2009s = [
    "G_front_sup",
    "G_front_middle",
    "G_parietal_sup",
    "S_front_middle"
]
MY_STRUCTURES_DKTatlas = [
    "superiorfrontal",
    "postcentral",
    "lateraloccipital",
    "caudalmiddlefrontal"
]

if __name__ == "__main__":
    
    df = collect_fs_data(
             file_name = "aseg.stats",
             regex_path_v7 = REGEX_PATH_V7,
             regex_path_v8 = REGEX_PATH_V8,
             structures = MY_STRUCTURES
             )

    df_a2009s = collect_fs_data(
             file_name = "lh.aparc.a2009s.stats",
             regex_path_v7 = REGEX_PATH_V7,
             regex_path_v8 = REGEX_PATH_V8,
             structures = MY_STRUCTURES_a2009s
             )

    df_DKTatlas = collect_fs_data(
             file_name = "lh.aparc.DKTatlas.stats",
             regex_path_v7 = REGEX_PATH_V7,
             regex_path_v8 = REGEX_PATH_V8,
             structures = MY_STRUCTURES_DKTatlas
             )

