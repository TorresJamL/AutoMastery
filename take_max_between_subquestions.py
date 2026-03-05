import pandas as pd
import numpy as np
from pathlib import Path
import os
from typing import List
import re

def is_question_col(col):
    return "pts)" in col and "ptional" not in col

def extract_question_key(col):
    """
    Extract keys like '4.3:cii.' from:
    '4.3: cii. defining recursive function (4.0 pts)'
    """
    og_pattern = r"\s*(\d+(?:\.\d+)?)\s*:\s*([a-zA-Z]?)\.",
    m = re.match(
        r"\s*(\d+(?:\.\d+)?)\s*:\s*([a-zA-Z]+)?\.?",
        col
    )
    if not m:
        return None
    num, letters = m.groups()
    return f"{num}:{letters.lower()}"

def extract_points(col):
    m = re.search(r"\((\d+(?:\.\d+)?)\s*pts\)", col)
    if not m:
        return None
    return float(m.group(1))


def build_question_key_map(df):
    """
    Maps question_key -> column_name for a particular df into a dictionary of
    question_keys (ex. 3.4:,
    """
    key_map = {}
    for col in df.columns:
        if "implementation" in col:
            print("here")
        if is_question_col(col):
            key = extract_question_key(col)
            if key is not None:
                key_map[key] = col
    return key_map


def create_bestof_df(dfs: List[pd.DataFrame]):
    """

    Args:
        dfs: A list of Pandas dataframes representing student scores

        a single df containing the union of all students across exams *AND* their maximum
        score on each subquestion

        on the final rubric, we use the question keys from the first listed df
        There must be an equivalent number in each CSV
    """
    ref_df = dfs[0]
    bestof_df = ref_df.copy(deep=True).set_index("SID")
    # Iterate over question keys
    ref_question_key_map = build_question_key_map(ref_df)
    print(ref_question_key_map)

    cols_to_transfer = ["Email", "Max Points", "First Name", "Last Name"]


    for alt_df in dfs[1:]:
        alt_df = alt_df.set_index("SID")
        alt_question_key_map = build_question_key_map(alt_df)

        for qkey, best_col in ref_question_key_map.items():
            if qkey not in alt_question_key_map:
                raise ValueError(f"Missing matching question key: {qkey}")

            alt_col = alt_question_key_map[qkey]
            best_vals = pd.to_numeric(bestof_df[best_col], errors="coerce").fillna(0)
            alt_vals = pd.to_numeric(alt_df[alt_col], errors="coerce").fillna(0)

            bestvals = best_vals.combine(alt_vals, max)
            bestof_df[best_col] = bestvals

        for col in cols_to_transfer:
            bestof_df[col] = bestof_df[col].combine_first(alt_df[col])

    assert (bestof_df[list(ref_question_key_map.values())].isna().sum().sum() == 0)

    qcols = list(ref_question_key_map.values())
    bestof_df["Total Score"] = bestof_df[qcols].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
    bestof_df = bestof_df.reset_index()
    bestof_df = bestof_df.dropna(subset=["SID"])
    bestof_df["SID"] = bestof_df["SID"].astype(int)
    return bestof_df


def verify_bounds(original_path, bestof_path):
    orig_df = pd.read_csv(original_path)
    best_df = pd.read_csv(bestof_path)

    # index by SID for alignment
    orig_df = orig_df.set_index("SID")
    best_df = best_df.set_index("SID")

    orig_qmap = build_question_key_map(orig_df)
    best_qmap = build_question_key_map(best_df)

    errors = 0
    diffs = 0

    for qkey, orig_col in orig_qmap.items():
        if qkey not in best_qmap:
            print(f"[ERROR] Missing question in bestof CSV: {qkey}")
            errors += 1
            continue

        best_col = best_qmap[qkey]

        orig_vals = (
            pd.to_numeric(orig_df[orig_col], errors="coerce")
            .fillna(0)
        )
        best_vals = (
            pd.to_numeric(best_df[best_col], errors="coerce")
            .fillna(0)
        )

        for sid in orig_vals.index.union(best_vals.index):
            if pd.isna(sid):
                continue
            o = orig_vals.get(sid, 0)
            b = best_vals.get(sid, 0)

            if b < o:
                print(
                    f"[VIOLATION] SID {sid} | {qkey} | "
                    f"original={o} bestof={b}"
                )
                errors += 1
            elif b > o:
                if sid not in orig_df.index:
                    print("Could not find a student")
                    continue
                first_name = orig_df.loc[sid, "First Name"]
                last_name = orig_df.loc[sid, "Last Name"]
                if pd.isna(first_name):
                    print("[ERROR] First Name missing")
                print(
                    f"[IMPROVED] {first_name} {last_name}  SID {sid} | {qkey} | "
                    f"original={o} bestof={b}"
                )
                diffs += 1

    print("\nSummary")
    print("-------")
    print(f"Improvements found : {diffs}")
    print(f"Violations found   : {errors}")

def get_matching_dfs(exam_num, root_dir = "data/"):
    """
    Args:
        exam_num:  number of the test
        root_dir: All exams
        MUST FOLLOW THIS FORMAT: examNall.csv
    Returns:

    """
    if not os.path.exists(root_dir):
        raise NotADirectoryError(f"{root_dir} does not exist")

    dfs = []
    file_matches = [f"exam{exam_num}all", f"Test_{exam_num}_retake", f"Exam_{exam_num}_retake"] #others would need to be combined
    fns = []
    for f in os.listdir(root_dir):
        for file_match in file_matches:
            if file_match in f:
                df = pd.read_csv(os.path.join(root_dir, f))
                dfs.append(df)
                fns.append(f)
                print(f)
    if "retake" in fns[0]:
        dfs.reverse()
    if not len(dfs):
        raise FileNotFoundError(f"Could not find a file of the format: data/exam{exam_num}all*.csv")
    return dfs

def merge_indices_of_dfs(dfs):
    dfs = [df.set_index("SID") for df in dfs]
    all_sids = dfs[0].index
    for df in dfs[1:]:
        all_sids = all_sids.union(df.index)
    assert len(all_sids) >= max(len(df) for df in dfs)
    dfs = [df.reindex(all_sids) for df in dfs]
    dfs = [df.reset_index() for df in dfs]

    return dfs

if __name__ == "__main__":
    #for exam_num in range(2):
    for exam_num in [1,2,3]:
        matching_dfs = get_matching_dfs(exam_num=exam_num)
        merged_dfs = merge_indices_of_dfs(matching_dfs)
        bestof_df = create_bestof_df(merged_dfs)
        bestof_df.to_csv(os.path.join("data", f"exam{exam_num}bestof.csv"))
        verify_bounds(f"data/exam{exam_num}all.csv", os.path.join("data", f"exam{exam_num}bestof.csv"))
