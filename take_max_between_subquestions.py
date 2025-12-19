import pandas as pd
from pathlib import Path
import os
from typing import List
import re

def is_question_col(col):
    return "pts)" in col

def extract_question_key(col):
    """
    Extract keys like '4.3:cii.' from:
    '4.3: cii. defining recursive function (4.0 pts)'
    """
    m = re.match(
        r"\s*(\d+(?:\.\d+)?)\s*:\s*([a-zA-Z]+)\.",
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
    for alt_df in dfs[1:]:
        alt_df = alt_df.set_index("SID")
        alt_question_key_map = build_question_key_map(alt_df)

        for qkey, best_col in ref_question_key_map.items():
            if qkey not in alt_question_key_map:
                raise ValueError(f"Missing matching question key: {qkey}")

            alt_col = alt_question_key_map[qkey]
            best_vals = pd.to_numeric(bestof_df[best_col], errors="coerce").fillna(0)
            alt_vals = pd.to_numeric(alt_df[alt_col], errors="coerce").fillna(0)

            bestof_df[best_col] = best_vals.combine(alt_vals, max)

    assert (bestof_df[list(ref_question_key_map.values())].isna().sum().sum() == 0)
    return bestof_df


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
    for f in os.listdir(root_dir):
        for file_match in file_matches:
            if file_match in f:
                dfs.append(pd.read_csv(os.path.join(root_dir, f)))

    if not len(dfs):
        raise FileNotFoundError(f"Could not find a file of the format: data/exam{exam_num}all*.csv")
    return dfs


if __name__ == "__main__":
    #for exam_num in range(2):
    exam_num = 1
    matching_dfs = get_matching_dfs(exam_num=1)
    bestof_df = create_bestof_df(matching_dfs)
    bestof_df.to_csv(os.path.join("data", f"exam{exam_num}bestof.csv"))
